from emergent.tools.base import Parameter, Tool, ToolResult


class DoDeepResearchTool(Tool):
    name = "do_deep_research"
    description = "Conduct in-depth research on a given topic at the Public Library"
    location_gate = "Public Library"
    parameters = [
        Parameter(name="topic", type="string", description="The research topic to investigate"),
    ]

    async def execute(self, agent, params, db, llm):
        topic = params.get("topic", "")
        return ToolResult(
            success=True,
            data={"topic": topic, "findings": f"Research on '{topic}' reveals 12 relevant sources. Key insight: the field is evolving rapidly with breakthroughs in decentralized consensus and emergent coordination."},
            observation=f"Research complete on '{topic}'.",
        )


class BrowsePapersTool(Tool):
    name = "browse_papers"
    description = "Browse available research papers in the library archive"
    location_gate = "Public Library"
    parameters = []

    async def execute(self, agent, params, db, llm):
        papers = [
            "On the Origin of Agent Cooperation",
            "Emergent Social Dynamics in Simulated Societies",
            "Computational Models of Trust",
            "The Economics of Virtual Communities",
            "Evolution of Communication Protocols",
        ]
        return ToolResult(
            success=True,
            data={"papers": papers},
            observation="You browse the shelves and find 5 papers.",
        )


class PublishToArchiveTool(Tool):
    name = "publish_to_archive"
    description = "Publish a paper or content to the public archive"
    location_gate = "Public Library"
    parameters = [
        Parameter(name="content", type="string", description="The content to publish"),
        Parameter(name="title", type="string", description="The title of your publication"),
    ]

    async def execute(self, agent, params, db, llm):
        title = params.get("title", "")
        return ToolResult(
            success=True,
            data={"title": title},
            observation=f"Your paper '{title}' has been published to the archive.",
        )


class SearchArchiveTool(Tool):
    name = "search_archive"
    description = "Search the public archive by keyword"
    location_gate = "Public Library"
    parameters = [
        Parameter(name="keyword", type="string", description="Keyword to search for"),
    ]

    async def execute(self, agent, params, db, llm):
        keyword = params.get("keyword", "")
        return ToolResult(
            success=True,
            data={"keyword": keyword, "results": []},
            observation=f"Search for '{keyword}' returned no results. Try a different keyword.",
        )
