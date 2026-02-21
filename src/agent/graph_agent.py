# src/agent/graph_agent.py

from __future__ import annotations

from typing import Any, Dict, List
import logging
import os
import json

from langgraph.graph import StateGraph, END

from src.agent.tools.knowledge_base_tool import KnowledgeBaseTool
from src.agent.tools.local_directory_tool import LocalDirectoryTool
from src.agent.tools.memory_tool import MemoryTool
from src.agent.tools.rbac_tool import RBACFilterTool
from src.retrieval.retriever import Retriever
from src.llm.generator import LLMGenerator

logger = logging.getLogger(__name__)

MAX_PLANNER_STEPS = 8  # or whatever limit you prefer

PLANNER_ACTIONS = ["KB_SEARCH", "LOCAL_SEARCH", "ANSWER"]


def build_basic_hr_agent() -> StateGraph:
    """
    Advanced HR/IT-assets RAG agent with:
      - Conversation + user memory
      - LLM-based planner (KB vs Local vs Answer)
      - RBAC filtering of retrieved docs
    """

    # ---- Core components ---- #

    base_retriever = Retriever()
    generator = LLMGenerator()
    memory_tool = MemoryTool()
    rbac_tool = RBACFilterTool()

    # Wrap Retriever in KnowledgeBaseTool
    def kb_retrieve_fn(query: str, top_k: int = 5):
        docs = base_retriever.retrieve(query)
        if top_k and len(docs) > top_k:
            docs = docs[:top_k]
        return docs

    kb_tool = KnowledgeBaseTool(
        retriever=kb_retrieve_fn,
        top_k=base_retriever.top_k,
    )

    local_tool = LocalDirectoryTool(
        local_dir=os.getenv("HR_LOCAL_DOCS_DIR", "data/hr_local"),
        top_k=5,
    )

    # ---------------------- Nodes ---------------------- #

    def load_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load recent conversation history and user profile into state.
        """
        user_id = state.get("user_id", "anonymous")
        steps = state.get("steps", [])
        steps.append("load_memory")

        mem = memory_tool.load(user_id=user_id, limit=10)
        state["conversation_history"] = mem.get("conversation_history", [])
        state["user_profile"] = mem.get("user_profile", {})
        state["steps"] = steps
        return state

    def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide next action: KB_SEARCH, LOCAL_SEARCH, or ANSWER.
        Includes a max-iteration guard to prevent infinite loops.
        """
        question = state.get("question", "")
        role = state.get("role", "")
        steps = state.get("steps", [])
        context = state.get("context") or []

        # ---- MAX ITERATION GUARD ----
        planner_calls = state.get("planner_calls", 0)
        if planner_calls >= MAX_PLANNER_STEPS:
            # We've already planned too many times; stop looping.
            steps.append(f"max_planner_steps_reached:{planner_calls}")

            # Fallback behavior:
            # - If we have some context, try to answer anyway.
            # - If no context at all, still route to ANSWER (the RAG prompt
            #   will see "No context." and say it doesn't know).
            state["next_action"] = "ANSWER"  # route_from_planner -> generate_answer
            state["steps"] = steps
            state["planner_calls"] = planner_calls
            return state
        # ------------------------------

        system_prompt = (
            "You are an orchestration agent for an IT/HR assistant. "
            "You must choose exactly ONE of: KB_SEARCH, LOCAL_SEARCH, ANSWER.\n\n"
            "Guidelines:\n"
            "- Prefer KB_SEARCH first for most questions.\n"
            "- If KB_SEARCH was tried and context is empty, then use LOCAL_SEARCH.\n"
            "- If there is already enough context and the question looks like a "
            "  follow-up, use ANSWER.\n"
            "Respond with ONLY the action label."
        )

        steps_str = " -> ".join(steps) if steps else "none"
        user_content = (
            f"User role: {role}\n"
            f"Question: {question}\n"
            f"Steps so far: {steps_str}\n"
            f"Has context: {bool(context)}\n\n"
            "Choose: KB_SEARCH, LOCAL_SEARCH, or ANSWER."
        )

        raw = generator.generate_text(
            system_prompt=system_prompt,
            user_content=user_content,
            max_tokens=5,
            temperature=0.0,
        )

        action = (raw or "").strip().upper()
        if action not in PLANNER_ACTIONS:
            action = "KB_SEARCH"

        planner_calls += 1
        state["planner_calls"] = planner_calls

        steps.append(f"plan:{action}")
        state["next_action"] = action
        state["steps"] = steps
        return state

    def route_from_planner(state: Dict[str, Any]) -> str:
        action = (state.get("next_action") or "").strip().upper()
        if action == "KB_SEARCH":
            return "kb_retrieve"
        if action == "LOCAL_SEARCH":
            return "local_retrieve"
        return "generate_answer"  # ANSWER or fallback

    def kb_retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve from knowledge base + apply RBAC.
        """
        question = state.get("question", "")
        user_id = state.get("user_id", "")
        role = state.get("role", "")
        steps: List[str] = state.get("steps", [])
        steps.append("kb_retrieve")

        docs = kb_tool.run(question)
        docs = rbac_tool.filter_docs(docs, user_id=user_id, role=role)

        state["kb_docs"] = docs or []
        # Replace or extend context; here we overwrite KB context
        state["context"] = docs or []
        state["steps"] = steps
        return state

    def local_retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve from local directory + apply RBAC, then merge with context.
        """
        question = state.get("question", "")
        user_id = state.get("user_id", "")
        role = state.get("role", "")
        steps: List[str] = state.get("steps", [])
        steps.append("local_retrieve")

        docs = local_tool.run(question)
        docs = rbac_tool.filter_docs(docs, user_id=user_id, role=role)

        state["local_docs"] = docs or []
        prev_ctx = state.get("context") or []
        state["context"] = prev_ctx + (docs or [])
        state["steps"] = steps
        return state

    def generate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use combined context + memory to generate final answer.
        """
        question = state.get("question", "")
        steps: List[str] = state.get("steps", [])
        steps.append("generate_answer")

        # Base context from retrieval
        context_docs = state.get("context") or []

        # Conversation history as a synthetic context doc
        conv = state.get("conversation_history") or []
        if conv:
            conv_text = "\n\n".join(
                f"Q: {t.get('question','')}\nA: {t.get('answer','')}" for t in conv
            )
            context_docs.append(
                {
                    "text": conv_text,
                    "metadata": {"source": "conversation_memory"},
                }
            )

        # User profile as another synthetic context doc
        profile = state.get("user_profile") or {}
        if profile:
            profile_text = "User profile:\n" + json.dumps(profile, ensure_ascii=False)
            context_docs.append(
                {
                    "text": profile_text,
                    "metadata": {"source": "user_profile"},
                }
            )

        answer = generator.generate_answer(
            question=question,
            context_docs=context_docs,
            hr_domain="it_assets",
        )

        state["answer"] = answer
        state["steps"] = steps
        return state

    def save_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save this turn to conversation memory.
        """
        user_id = state.get("user_id", "anonymous")
        question = state.get("question", "")
        answer = state.get("answer", "")

        steps: List[str] = state.get("steps", [])
        steps.append("save_memory")

        if question and answer:
            memory_tool.save_turn(user_id=user_id, question=question, answer=answer)

        state["steps"] = steps
        return state

    # ------------------- Build graph ------------------- #

    graph = StateGraph(dict)

    graph.add_node("load_memory", load_memory_node)
    graph.add_node("plan", planner_node)
    graph.add_node("kb_retrieve", kb_retrieve_node)
    graph.add_node("local_retrieve", local_retrieve_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("save_memory", save_memory_node)

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "plan")

    graph.add_conditional_edges(
        "plan",
        route_from_planner,
        {
            "kb_retrieve": "kb_retrieve",
            "local_retrieve": "local_retrieve",
            "generate_answer": "generate_answer",
        },
    )

    graph.add_edge("kb_retrieve", "plan")
    graph.add_edge("local_retrieve", "plan")
    graph.add_edge("generate_answer", "save_memory")
    graph.add_edge("save_memory", END)

    return graph