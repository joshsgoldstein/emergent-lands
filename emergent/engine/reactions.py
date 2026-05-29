import logging

logger = logging.getLogger(__name__)

MAX_REACTION_DEPTH = 3
MAX_LISTENERS = 4


def _provider_for_agent(router, model_routing, agent_name, agent_configs=None):
    agent_configs = agent_configs or {}
    cfg = agent_configs.get(agent_name)
    if cfg and cfg.provider:
        return router.get_provider(cfg.provider, model=cfg.model)
    overrides = model_routing.get("overrides", {})
    provider_name = overrides.get(agent_name) or model_routing.get("default", "openai")
    return router.get_provider(provider_name)


async def handle_reactions(speaker, speech, db, registry, state_mgr, memory_mgr, context_builder, router, model_routing, depth=0, agent_configs=None, track_usage=None):
    if depth >= MAX_REACTION_DEPTH:
        return

    from sqlalchemy import select
    from emergent.db.models import Agent

    if speaker.current_location_id is None:
        return

    result = await db.execute(
        select(Agent).where(
            Agent.current_location_id == speaker.current_location_id,
            Agent.id != speaker.id,
            Agent.status == "alive",
        )
    )
    nearby = list(result.scalars().all())[:MAX_LISTENERS]

    for listener in nearby:
        listener_provider = _provider_for_agent(router, model_routing, listener.name, agent_configs)

        logger.info(f"    ↻ {listener.name} overheard {speaker.name}: \"{speech[:120]}\"")

        ctx = await context_builder.assemble(listener)
        system_prompt = (
            f"You overheard {speaker.name} say: '{speech}'\n\n"
            f"You are at the same location. You can react briefly (max 2 tools).\n\n"
            f"{ctx['system_prompt']}"
        )

        response = await listener_provider.generate(
            system_prompt=system_prompt,
            messages=[],
            tools=ctx["tools"],
            agent=listener,
        )
        if track_usage and response.usage:
            track_usage(response.usage.prompt_tokens, response.usage.completion_tokens)

        for tc in response.tool_calls:
            tool = registry.get(tc.name)
            if tool:
                await tool.execute(listener, tc.params, db, listener_provider)
                await memory_mgr.add_memory(
                    listener.id,
                    f"[Reaction] Used {tc.name} in response to {speaker.name}",
                )

            if tc.name == "say_to_agent" or tc.name == "think_aloud":
                from emergent.db.models import Speech
                speech_text = tc.params.get("message") or tc.params.get("thought") or ""
                db.add(Speech(
                    agent_id=listener.id,
                    message=speech_text,
                    channel=tc.name,
                    location_id=listener.current_location_id,
                ))
                await db.flush()
                await memory_mgr.add_memory(
                    listener.id,
                    f"[Reaction] Responded to {speaker.name}: {speech_text[:100]}",
                )
                await handle_reactions(
                    listener, speech_text,
                    db, registry, state_mgr, memory_mgr,
                    context_builder, router, model_routing, depth + 1,
                    agent_configs=agent_configs,
                    track_usage=track_usage,
                )
