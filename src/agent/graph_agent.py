# from typing import Dict, Any
# from langgraph.graph import StateGraph, END

# from src.agent.agent_core import ITRAGAgentCore, AgentState


# def build_it_graph_agent() -> StateGraph:
#     """
#     LangGraph agent that does:
#     -> retrieve -> generate -> END
#     """

#     core = ITRAGAgentCore()

#     def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
#         # state contains 'question'
#         question = state["question"]
#         s = core.run_rag(question)
#         return {
#             "question": s.question,
#             "context": s.context,
#             "answer": s.answer,
#             "steps": s.steps,
#             "error": s.error,
#         }

#     graph = StateGraph(dict)
#     graph.add_node("rag_pipeline", start_node)
#     graph.set_entry_point("rag_pipeline")
#     graph.set_finish_point("rag_pipeline")

#     return graph
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from src.agent.agent_core import ITRAGAgentCore, AgentState


def build_it_graph_agent() -> StateGraph:
    """
    LangGraph agent that does:
    -> (optional rewrite) -> retrieve -> generate -> END
    """

    core = ITRAGAgentCore()

    def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # state contains 'question', optionally 'history'
        question = state["question"]
        history = state.get("history", [])

        s = core.run_rag(question, history=history)

        return {
            "question": s.question,
            "rewritten_question": s.rewritten_question,
            "context": s.context,
            "answer": s.answer,
            "steps": s.steps,
            "error": s.error,
            "history": s.history,
        }

    graph = StateGraph(dict)
    graph.add_node("rag_pipeline", start_node)
    graph.set_entry_point("rag_pipeline")
    graph.set_finish_point("rag_pipeline")

    return graph