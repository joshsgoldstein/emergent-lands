import logging

logger = logging.getLogger(__name__)

MAX_REACTION_EXCHANGES = 30
MAX_LISTENERS = 4


async def handle_reactions(speaker, speech, db, registry, state_mgr, memory_mgr, context_builder, provider, exchange_count=0):
    if exchange_count >= MAX_REACTION_EXCHANGES:
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
        exchange_count += 1
        if exchange_count >= MAX_REACTION_EXCHANGES:
            break

        ctx = await context_builder.assemble(listener)
        system_prompt = (
            f"You overheard {speaker.name} say: '{speech}'\n\n"
            f"You are at the same location. You can react briefly (max 2 tools).\n\n"
            f"{ctx['system_prompt']}"
        )

        response = await provider.generate(
            system_prompt=system_prompt,
            messages=[],
            tools=ctx["tools"],
            agent=listener,
        )

        for tc in response.tool_calls:
            tool = registry.get(tc.name)
            if tool:
                await tool.execute(listener, tc.params, db, provider)
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
                    context_builder, provider, exchange_count,
                )
