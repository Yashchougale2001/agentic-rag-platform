from typing import Dict, Any, List
from dataclasses import dataclass, field

from src.agent.tools.rag_tool import RAGTool
from src.agent.tools.analyze_tool import AnalyzeAssetTool
from src.llm.generator import LLMGenerator


@dataclass
class AgentState:
    question: str
    context: List[Dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    error: str = ""
    steps: List[str] = field(default_factory=list)


class ITRAGAgentCore:
    """
    Core logic for IT RAG agent outside of LangGraph for easier reuse & testing.
    """

    def __init__(self):
        self.rag_tool = RAGTool()
        self.analyze_tool = AnalyzeAssetTool()
        self.generator = LLMGenerator()

    def run_rag(self, question: str) -> AgentState:
        state = AgentState(question=question)
        state.steps.append("retrieve")
        docs = self.rag_tool.run(question)
        state.context = docs

        if not docs:
            state.answer = (
                "I don't have IT assets information that answers this question yet. "
                "Please ingest relevant IT assets documents and try again."
            )
            return state

        state.steps.append("generate_answer")
        answer = self.generator.generate_answer(question=question, context_docs=docs)
        state.answer = answer
        return state