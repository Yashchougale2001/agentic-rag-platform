# from typing import Dict, Any, List
# from dataclasses import dataclass, field

# from src.agent.tools.rag_tool import RAGTool
# from src.agent.tools.analyze_tool import AnalyzeAssetTool
# from src.llm.generator import LLMGenerator


# @dataclass
# class AgentState:
#     question: str
#     context: List[Dict[str, Any]] = field(default_factory=list)
#     answer: str = ""
#     error: str = ""
#     steps: List[str] = field(default_factory=list)


# class ITRAGAgentCore:
#     """
#     Core logic for IT RAG agent outside of LangGraph for easier reuse & testing.
#     """

#     def __init__(self):
#         self.rag_tool = RAGTool()
#         self.analyze_tool = AnalyzeAssetTool()
#         self.generator = LLMGenerator()

#     def run_rag(self, question: str) -> AgentState:
#         state = AgentState(question=question)
#         state.steps.append("retrieve")
#         docs = self.rag_tool.run(question)
#         state.context = docs

#         if not docs:
#             state.answer = (
#                 "I don't have IT assets information that answers this question yet. "
#                 "Please ingest relevant IT assets documents and try again."
#             )
#             return state

#         state.steps.append("generate_answer")
#         answer = self.generator.generate_answer(question=question, context_docs=docs)
#         state.answer = answer
#         return state
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from src.agent.tools.rag_tool import RAGTool
from src.agent.tools.analyze_tool import AnalyzeAssetTool
from src.llm.generator import LLMGenerator
from src.processing.query_rewriter import QueryRewriter
from src.utils.config_loader import load_model_config


@dataclass
class AgentState:
    question: str
    context: List[Dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    error: str = ""
    steps: List[str] = field(default_factory=list)
    # New fields:
    rewritten_question: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)


class ITRAGAgentCore:
    """
    Core logic for IT RAG agent outside of LangGraph for easier reuse & testing.
    """

    def __init__(self):
        self.rag_tool = RAGTool()
        self.analyze_tool = AnalyzeAssetTool()
        self.generator = LLMGenerator()

        # Load query rewriting config from model.yaml
        model_cfg = load_model_config()
        retrieval_cfg = model_cfg.get("retrieval", {})
        qr_cfg = retrieval_cfg.get("query_rewriting", {})

        self.query_rewriting_enabled = qr_cfg.get("enabled", False)
        self.query_rewriting_max_history = qr_cfg.get("max_history_messages", 6)
        self.query_rewriter = QueryRewriter(
            llm=self.generator,
            max_history=self.query_rewriting_max_history,
        )

    def run_rag(
        self,
        question: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentState:
        state = AgentState(question=question)
        state.history = history or []

        query_for_retrieval = question

        # Optional query rewriting step
        if self.query_rewriting_enabled:
            state.steps.append("rewrite_query")
            rewritten = self.query_rewriter.rewrite(
                question=question,
                history=state.history,
            )
            state.rewritten_question = rewritten
            query_for_retrieval = rewritten

        state.steps.append("retrieve")
        docs = self.rag_tool.run(query_for_retrieval)
        state.context = docs

        if not docs:
            state.answer = (
                "I don't have IT assets information that answers this question yet. "
                "Please ingest relevant IT assets documents and try again."
            )
            return state

        state.steps.append("generate_answer")
        answer = self.generator.generate_answer(
            question=question,  # keep original user question for answering
            context_docs=docs,
        )
        state.answer = answer
        return state