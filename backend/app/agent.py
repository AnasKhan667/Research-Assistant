import logging
from typing import Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.config import config
from app.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class ResearchFinding(BaseModel):
    """One piece of search result or one finding from the research process."""

    content: str = Field(description="The content of the research finding")
    source: Optional[str] = Field(
        default=None,
        description="The source of the research finding (e.g., URL, tool used, etc.)",
    )


class AgentState(TypedDict):
    """State of the agent at any point in time."""

    query: str
    plan: Optional[str]
    research_findings: List[ResearchFinding]
    critic_feedback: List[str]
    final_report: Optional[str]
    iteration_count: int
    sources: List[str]


class ResearchOrchestrator:
    """Orchestrates a multi-agent (supervisor -> researcher -> critic -> writer) research workflow."""

    def __init__(self):
        self.llm_manager = LLMManager()
        self.model = self.llm_manager.chat_model
        self.parser = self.llm_manager.parser
        self.tools = self._setup_tools()
        self.max_iterations = config.MAX_ITERATIONS

        self.graph = self._setup_graph()
        self.workflow = self.graph.compile()

    def _setup_tools(self):
        """Set up external tools for the agent to use during research."""
        return [DuckDuckGoSearchRun()]

    def _setup_graph(self) -> StateGraph:
        """Set up the LangGraph state graph for the research workflow."""
        graph = StateGraph(AgentState)

        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("researcher", self._researcher_node)
        graph.add_node("critic", self._critic_node)
        graph.add_node("writer", self._writer_node)

        graph.add_edge(START, "supervisor")
        graph.add_edge("supervisor", "researcher")
        graph.add_edge("researcher", "critic")

        graph.add_conditional_edges(
            "critic",
            self._should_continue,
            {"continue_research": "researcher", "write_report": "writer"},
        )
        graph.add_edge("writer", END)

        return graph

    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue research iterations or move to report writing."""
        if state["iteration_count"] >= self.max_iterations:
            logger.info("Max iterations (%d) reached — moving to writer", self.max_iterations)
            return "write_report"

        last_feedback = state["critic_feedback"][-1] if state["critic_feedback"] else ""
        if "GOOD_ENOUGH" in last_feedback.upper() and len(state["research_findings"]) >= 4:
            logger.info("Critic approved findings — moving to writer")
            return "write_report"
        return "continue_research"

    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Supervisor node: provides high-level guidance for the research process."""
        logger.info("Supervisor: planning research for query=%r", state["query"][:80])

        prompt = PromptTemplate.from_template(
            """You are a research supervisor overseeing a research project.
            Provide 4 bullet-point high-level guidance items for the researcher based on
            the original research query:

            {query}

            Plan:"""
        )
        chain = prompt | self.model | self.parser
        state["plan"] = chain.invoke({"query": state["query"]}).strip()
        return state

    def _build_search_query(self, state: AgentState) -> str:
        """Build a refined search query using the original query and critic feedback.

        On the first iteration the original query is used.  On subsequent
        iterations the critic's latest feedback is folded in so that the
        researcher explores gaps rather than re-fetching the same results.
        """
        base_query = state["query"]

        if state["iteration_count"] == 0 or not state["critic_feedback"]:
            return base_query

        last_feedback = state["critic_feedback"][-1]
        # Ask the LLM to produce a concise refined search query
        refine_prompt = PromptTemplate.from_template(
            """Given the original research question and the critic's feedback,
produce a single concise web-search query (≤15 words) that targets the
gaps the critic identified.  Return ONLY the search query, nothing else.

Original question: {query}
Critic feedback: {feedback}

Refined search query:"""
        )
        chain = refine_prompt | self.model | self.parser
        try:
            refined = chain.invoke({"query": base_query, "feedback": last_feedback[:500]}).strip()
            if refined and len(refined) < 200:
                logger.info("Researcher: refined search query=%r", refined[:80])
                return refined
        except Exception:
            logger.warning("Failed to refine search query — falling back to original")

        return base_query

    def _researcher_node(self, state: AgentState) -> AgentState:
        """Researcher node: conducts research using external tools."""
        logger.info("Researcher: iteration %d", state["iteration_count"])

        search_query = self._build_search_query(state)
        existing_contents = {f.content for f in state["research_findings"]}

        for tool in self.tools[:2]:
            try:
                result = tool.invoke(search_query)
                if result and len(str(result)) > 50:
                    content = str(result)[:800]
                    # Skip near-duplicate findings
                    if content in existing_contents:
                        logger.debug("Researcher: skipping duplicate finding")
                        continue
                    existing_contents.add(content)
                    finding = ResearchFinding(content=content, source="DuckDuckGo Search Result")
                    state["research_findings"].append(finding)
                    state["sources"].append(finding.source)
            except Exception as e:
                logger.warning("Researcher: search tool error — %s", e)

        return state

    def _critic_node(self, state: AgentState) -> AgentState:
        """Critic node: evaluates findings and decides whether more research is needed."""
        logger.info("Critic: reviewing %d findings", len(state["research_findings"]))

        if not state["research_findings"]:
            state["critic_feedback"].append("No research findings were generated.")
            state["iteration_count"] += 1
            return state

        critic_prompt = PromptTemplate.from_template(
            """You are a strict research critic.

            Research Query: {query}
            Current Findings: {findings}

            Evaluate the research findings based on the original query. Consider the
            relevance, depth, and breadth of the findings in relation to the query.

            If research is sufficient -> reply ONLY: GOOD_ENOUGH
            Otherwise -> give specific feedback on what is missing."""
        )
        findings_text = "\n\n".join(f.content for f in state["research_findings"])

        chain = critic_prompt | self.model | self.parser
        feedback = chain.invoke(
            {"query": state["query"], "findings": findings_text[:1500]}
        )
        state["critic_feedback"].append(feedback)
        state["iteration_count"] += 1

        logger.info("Critic: verdict=%s", "GOOD_ENOUGH" if "GOOD_ENOUGH" in feedback.upper() else "needs more research")
        return state

    def _writer_node(self, state: AgentState) -> AgentState:
        """Writer node: generates the final report from research findings."""
        logger.info("Writer: generating final report from %d findings", len(state["research_findings"]))

        if not state["research_findings"]:
            state["final_report"] = "Unable to generate report due to lack of research findings."
            return state

        writer_prompt = PromptTemplate.from_template(
            """You are a research report writer.

            Research Query: {query}
            Research Findings: {findings}

            Write a well-structured research report (400-600 words). Include key points
            and sources where possible based on the findings. The report should be
            comprehensive, coherent, and directly address the research query.

            Final report:"""
        )
        findings_text = "\n\n".join(
            f"Finding {i + 1}: {f.content[:450]}"
            for i, f in enumerate(state["research_findings"])
        )

        chain = writer_prompt | self.model | self.parser
        report = chain.invoke(
            {"query": state["query"], "findings": findings_text[:1500]}
        )
        state["final_report"] = report.strip()
        return state

    def generate_report(self, query: str) -> Dict[str, Any]:
        """Run the full workflow and return the final state."""
        initial_state: AgentState = {
            "query": query,
            "plan": None,
            "research_findings": [],
            "critic_feedback": [],
            "final_report": None,
            "iteration_count": 0,
            "sources": [],
        }

        logger.info("Starting research pipeline for query=%r", query[:80])
        result = self.workflow.invoke(initial_state)

        logger.info(
            "Pipeline complete — iterations=%d, findings=%d, report_len=%d",
            result["iteration_count"],
            len(result["research_findings"]),
            len(result["final_report"] or ""),
        )

        return result


if __name__ == "__main__":
    orchestrator = ResearchOrchestrator()
    test_query = "What is the future of AI research in the next 10 years?"
    final_result = orchestrator.generate_report(test_query)

    print("\n" + "=" * 80)
    print("FINAL REPORT SUMMARY")
    print("=" * 80)
    print((final_result.get("final_report") or "")[:700] + "\n...")
