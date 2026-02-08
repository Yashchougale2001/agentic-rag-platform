# # from typing import Dict, Any, List
# # import os
# # import re
# # import html

# # from langgraph.graph import StateGraph

# # from src.agent.tools.rag_tool import RAGTool
# # from src.agent.tools.local_search_tool import LocalSearchTool
# # from src.agent.tools.email_tool import EmailTool
# # from src.llm.generator import LLMGenerator

# # def build_hr_graph_agent() -> StateGraph:
# #     """
# #     LangGraph agent that does:
# #     1) vector retrieve
# #     2) generate
# #     3) if generator says "I don't know", use local fallback and generate again
# #     4) optionally send an email if the user asks for it
# #     """

# #     rag_tool = RAGTool()
# #     local_search_tool = LocalSearchTool(
# #         local_dir=os.getenv("HR_LOCAL_DOCS_DIR", "data/hr_local")
# #     )

# #     email_tool = EmailTool()
# #     generator = LLMGenerator()

# #     UNKNOWN_ANSWER = "I don't know based on the current knowledge base."

# #     def retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
# #         question = state["question"]
# #         steps: List[str] = state.get("steps", [])
# #         steps.append("vector_retrieve")

# #         # Primary: vector-based retrieval
# #         docs = rag_tool.run(question)

# #         return {
# #             "question": question,
# #             "context": docs,   # may be empty or irrelevant
# #             "answer": "",
# #             "error": "",
# #             "steps": steps,
# #         }

# #     def generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
# #         question = state["question"]
# #         docs = state.get("context", [])
# #         steps: List[str] = state.get("steps", [])

# #         # If we already have an answer (e.g., from some earlier node), skip
# #         if state.get("answer"):
# #             return state

# #         # 1) Generate using vector RAG context (if any)
# #         steps.append("generate_answer_primary")
# #         answer = generator.generate_answer(
# #             question=question,
# #             context_docs=docs,
# #             hr_domain="hr_policies",
# #         )

# #         # 2) If LLM couldn't answer, try local fallback
# #         if UNKNOWN_ANSWER in answer:
# #             steps.append("local_fallback_retrieve")
# #             local_docs = local_search_tool.run(question)

# #             if local_docs:
# #                 # Re-generate using local docs
# #                 steps.append("generate_answer_fallback")
# #                 answer = generator.generate_answer(
# #                     question=question,
# #                     context_docs=local_docs,
# #                     hr_domain="hr_policies",
# #                 )
# #                 docs = local_docs  # update context to reflect actual source

# #         state["answer"] = answer
# #         state["context"] = docs
# #         state["steps"] = steps
# #         return state

# #     def send_email_node(state: Dict[str, Any]) -> Dict[str, Any]:
# #         """
# #         Optionally send the generated answer by email if the user requested it.

# #         Simple heuristic:
# #         - If 'email' (or 'mail') is not in the question, do nothing.
# #         - Try to extract an email address from the question.
# #         - Skip if no recipient or if the answer is the UNKNOWN_ANSWER.
# #         """
# #         question = state.get("question", "")
# #         answer = state.get("answer", "")
# #         steps: List[str] = state.get("steps", [])
# #         steps.append("send_email_check")

# #         q_lower = question.lower()

# #         # Don't try to email if we don't know the answer
# #         if UNKNOWN_ANSWER in answer:
# #             state["steps"] = steps
# #             return state

# #         # Only consider sending if the user mentioned email
# #         if "email" not in q_lower and "mail" not in q_lower:
# #             state["steps"] = steps
# #             return state

# #         # Extract recipient email from the question
# #         match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", question)
# #         recipient_email = match.group(0) if match else None

# #         if not recipient_email:
# #             steps.append("send_email_skipped_no_recipient")
# #             state["steps"] = steps
# #             return state

# #         # Build a simple professional HTML email body using the answer
# #         safe_answer_html = html.escape(answer).replace("\n", "<br>")
# #         body_html = f"""
# #         <html>
# #           <body>
# #             <p>
# #               Dear Colleague,<br><br>
# #               {safe_answer_html}<br><br>
# #               Best regards,<br>
# #               HR Team
# #             </p>
# #           </body>
# #         </html>
# #         """

# #         subject = "HR assistant response"

# #         email_payload = {
# #             "recipient_email": recipient_email,
# #             "subject": subject,
# #             "body": body_html,
# #         }

# #         steps.append("send_email_attempted")
# #         email_result = email_tool.run(email_payload)

# #         state["email_result"] = email_result
# #         state["steps"] = steps
# #         return state

# #     graph = StateGraph(dict)
# #     graph.add_node("retrieve", retrieve_node)
# #     graph.add_node("generate", generate_node)
# #     graph.add_node("send_email", send_email_node)

# #     graph.set_entry_point("retrieve")
# #     graph.add_edge("retrieve", "generate")
# #     graph.add_edge("generate", "send_email")
# #     graph.set_finish_point("send_email")

# #     return graph
# # src/agent/graph_agent.py

# from typing import Dict, Any, List
# import os
# import re
# import html

# from langgraph.graph import StateGraph, END

# from src.agent.tools.rag_tool import RAGTool
# from src.agent.tools.local_search_tool import LocalSearchTool
# from src.agent.tools.email_tool import EmailTool
# from src.llm.generator import LLMGenerator


# def build_hr_graph_agent() -> StateGraph:
#     """
#     LangGraph-based HR agent:

#     Flow:
#       1) retrieve_vector       -> vector-based retrieval
#       2) generate_primary      -> RAG generation from vector docs
#       3) conditional:
#            - if "I don't know"  -> retrieve_local -> generate_local
#            - else if email asked -> send_email
#            - else                -> END
#       4) after generate_local:
#            - if email asked and answer known -> send_email
#            - else                            -> END
#     """

#     rag_tool = RAGTool()
#     local_search_tool = LocalSearchTool(
#         local_dir=os.getenv("HR_LOCAL_DOCS_DIR", "data/hr_local")
#     )
#     email_tool = EmailTool()
#     generator = LLMGenerator()

#     # ------------------------------------------------------------------ #
#     # Helper functions
#     # ------------------------------------------------------------------ #

#     UNKNOWN_MARKER = "i don't know"

#     def is_unknown_answer(answer: str) -> bool:
#         """Detect whether the LLM signaled lack of knowledge."""
#         if not answer:
#             return True
#         return UNKNOWN_MARKER in answer.lower()

#     def user_requested_email(question: str) -> bool:
#         q_lower = (question or "").lower()
#         return "email" in q_lower or "mail" in q_lower

#     # ------------------------------------------------------------------ #
#     # Nodes
#     # ------------------------------------------------------------------ #

#     def retrieve_vector_node(state: Dict[str, Any]) -> Dict[str, Any]:
#         question = state["question"]
#         steps: List[str] = state.get("steps", [])
#         steps.append("vector_retrieve")

#         docs = rag_tool.run(question)

#         state["context"] = docs
#         state["steps"] = steps
#         state.setdefault("error", "")
#         return state

#     def generate_primary_node(state: Dict[str, Any]) -> Dict[str, Any]:
#         question = state["question"]
#         docs = state.get("context", [])
#         steps: List[str] = state.get("steps", [])
#         steps.append("generate_answer_primary")

#         answer = generator.generate_answer(
#             question=question,
#             context_docs=docs,
#             hr_domain="hr_policies",
#         )

#         state["answer"] = answer
#         state["steps"] = steps
#         return state

#     def retrieve_local_node(state: Dict[str, Any]) -> Dict[str, Any]:
#         question = state["question"]
#         steps: List[str] = state.get("steps", [])
#         steps.append("local_fallback_retrieve")

#         local_docs = local_search_tool.run(question)

#         state["context"] = local_docs
#         state["steps"] = steps
#         return state

#     def generate_local_node(state: Dict[str, Any]) -> Dict[str, Any]:
#         question = state["question"]
#         docs = state.get("context", [])
#         steps: List[str] = state.get("steps", [])
#         steps.append("generate_answer_fallback")

#         answer = generator.generate_answer(
#             question=question,
#             context_docs=docs,
#             hr_domain="hr_policies",
#         )

#         state["answer"] = answer
#         state["steps"] = steps
#         return state

#     def send_email_node(state: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Send the generated answer by email if:
#         - user requested email, and
#         - we have a recipient address, and
#         - the answer is not an "I don't know" fallback.
#         """
#         question = state.get("question", "")
#         answer = state.get("answer", "")
#         steps: List[str] = state.get("steps", [])
#         steps.append("send_email_check")

#         if is_unknown_answer(answer):
#             steps.append("send_email_skipped_unknown_answer")
#             state["steps"] = steps
#             return state

#         # Extract recipient email from the question
#         match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", question)
#         recipient_email = match.group(0) if match else None

#         if not recipient_email:
#             steps.append("send_email_skipped_no_recipient")
#             state["steps"] = steps
#             return state

#         safe_answer_html = html.escape(answer).replace("\n", "<br>")
#         body_html = f"""
#         <html>
#           <body>
#             <p>
#               Dear Colleague,<br><br>
#               {safe_answer_html}<br><br>
#               Best regards,<br>
#               HR Team
#             </p>
#           </body>
#         </html>
#         """

#         email_payload = {
#             "recipient_email": recipient_email,
#             "subject": "HR assistant response",
#             "body": body_html,
#         }

#         steps.append("send_email_attempted")
#         email_result = email_tool.run(email_payload)

#         state["email_result"] = email_result
#         state["steps"] = steps
#         return state

#     # ------------------------------------------------------------------ #
#     # Routers (conditional edges)
#     # ------------------------------------------------------------------ #

#     def route_after_primary(state: Dict[str, Any]) -> str:
#         """
#         Decide next step after the first generation:

#         - If answer unknown -> try local fallback retrieval.
#         - Else, if user asked for email -> send_email.
#         - Else -> END.
#         """
#         answer = state.get("answer", "")
#         question = state.get("question", "")

#         if is_unknown_answer(answer):
#             return "local_retrieve"

#         if user_requested_email(question):
#             return "send_email"

#         return "end"

#     def route_after_local(state: Dict[str, Any]) -> str:
#         """
#         Decide next step after fallback generation:

#         - If still unknown -> END.
#         - Else, if user asked for email -> send_email.
#         - Else -> END.
#         """
#         answer = state.get("answer", "")
#         question = state.get("question", "")

#         if is_unknown_answer(answer):
#             return "end"

#         if user_requested_email(question):
#             return "send_email"

#         return "end"

#     # ------------------------------------------------------------------ #
#     # Build graph
#     # ------------------------------------------------------------------ #

#     graph = StateGraph(dict)

#     # Nodes
#     graph.add_node("retrieve_vector", retrieve_vector_node)
#     graph.add_node("generate_primary", generate_primary_node)
#     graph.add_node("retrieve_local", retrieve_local_node)
#     graph.add_node("generate_local", generate_local_node)
#     graph.add_node("send_email", send_email_node)

#     # Edges
#     graph.set_entry_point("retrieve_vector")
#     graph.add_edge("retrieve_vector", "generate_primary")

#     graph.add_conditional_edges(
#         "generate_primary",
#         route_after_primary,
#         {
#             "local_retrieve": "retrieve_local",
#             "send_email": "send_email",
#             "end": END,
#         },
#     )

#     graph.add_edge("retrieve_local", "generate_local")

#     graph.add_conditional_edges(
#         "generate_local",
#         route_after_local,
#         {
#             "send_email": "send_email",
#             "end": END,
#         },
#     )

#     graph.add_edge("send_email", END)

#     return graph
# src/agent/graph_agent.py

from typing import Dict, Any, List
import os
import re
import html

from langgraph.graph import StateGraph, END

from src.agent.tools.rag_tool import BasicRetrievalTool
from src.agent.tools.local_search_tool import LocalSearchTool
from src.agent.tools.email_tool import EmailTool
from src.llm.generator import LLMGenerator


ACTIONS = [
    "BASIC_RETRIEVE",      # use vector RAG retrieval
    "LOCAL_RETRIEVE",      # use local file search
    "ANSWER_FROM_CONTEXT", # use current context to generate final answer
    "SEND_EMAIL",          # email the current answer to the user
    "FINISH",              # stop, return current state
]


def build_basic_hr_agent() -> StateGraph:
    """
    Agentic HR assistant graph (LangGraph):

    State keys:
      - question: str
      - context: List[dict] (current docs used for generation)
      - answer: str
      - steps: List[str]
      - next_action: str (planner decision)
      - email_result: Any (optional)

    Workflow (high level):
      1) PLAN               -> LLM planner chooses next action from ACTIONS.
      2) BASIC_RETRIEVE     -> vector-based RAG; then PLAN again.
      3) LOCAL_RETRIEVE     -> local file search; then PLAN again.
      4) ANSWER_FROM_CONTEXT-> generate answer using current context; then PLAN again.
      5) SEND_EMAIL         -> send answer by email; then END.
      6) FINISH             -> END.
    """

    basic_retrieval_tool = BasicRetrievalTool()
    local_search_tool = LocalSearchTool(
        local_dir=os.getenv("HR_LOCAL_DOCS_DIR", "data/hr_local")
    )
    email_tool = EmailTool()
    generator = LLMGenerator()

    # ------------------------------------------------------------------ #
    # Helper: LLM-based planner
    # ------------------------------------------------------------------ #

    def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to decide the next action for the agent.

        LLM must output exactly one of:
        BASIC_RETRIEVE, LOCAL_RETRIEVE, ANSWER_FROM_CONTEXT, SEND_EMAIL, FINISH
        """
        question = state.get("question", "")
        steps: List[str] = state.get("steps", [])
        answer = state.get("answer", "")
        email_result = state.get("email_result", None)
        context = state.get("context", [])

        has_context = bool(context)
        has_answer = bool(answer)
        email_already_sent = email_result is not None

        # System prompt constrains the LLM to select a single action label only
        system_prompt = (
            "You are an HR assistant orchestrator. "
            "You must decide what the agent should do next by choosing exactly "
            "ONE action from this list and returning ONLY the action label:\n"
            "BASIC_RETRIEVE, LOCAL_RETRIEVE, ANSWER_FROM_CONTEXT, SEND_EMAIL, FINISH.\n\n"
            "Guidelines:\n"
            "- Start with BASIC_RETRIEVE for most HR questions when no context is available.\n"
            "- Use LOCAL_RETRIEVE if BASIC_RETRIEVE was tried and the answer is still unknown, "
            "  or if the question suggests data might exist only in local/shared drives.\n"
            "- Use ANSWER_FROM_CONTEXT when you already have relevant context documents and "
            "  you haven't produced a confident answer yet.\n"
            "- Use SEND_EMAIL only if there is a clear answer already AND the user asked to "
            "  email the response. Do not use SEND_EMAIL if there is no valid answer.\n"
            "- Use FINISH when you have already produced the best possible answer and any "
            "  requested email has been handled, or clearly cannot be handled.\n\n"
            "Output strictly one of these tokens with no explanation:\n"
            "BASIC_RETRIEVE, LOCAL_RETRIEVE, ANSWER_FROM_CONTEXT, SEND_EMAIL, FINISH."
        )

        # Summarize current state for the planner
        steps_str = " -> ".join(steps) if steps else "none"

        user_content = (
    f"User question:\n{question}\n\n"
    f"Steps taken so far: {steps_str}\n"
    f"Current answer (may be empty):\n{answer or '<no answer yet>'}\n\n"
    f"Has context docs: {has_context}\n"
    f"Has answer: {has_answer}\n"
    f"Email already sent: {email_already_sent}\n\n"
    "If the current answer looks like 'I don't know', 'cannot answer from the context', "
    "or is clearly missing information, treat that as UNKNOWN and prefer to use "
    "BASIC_RETRIEVE or LOCAL_RETRIEVE again instead of FINISH.\n\n"
    "Now choose exactly one ACTION: BASIC_RETRIEVE, LOCAL_RETRIEVE, ANSWER_FROM_CONTEXT, SEND_EMAIL, FINISH."
)

        raw_action = generator.generate_text(
            system_prompt=system_prompt,
            user_content=user_content,
            max_tokens=8,
            temperature=0.0,
        )

        action = (raw_action or "").strip().upper()

        # Basic safety: if LLM outputs something unexpected, default to FINISH
        if action not in ACTIONS:
            action = "FINISH"

        steps.append(f"plan:{action}")
        state["next_action"] = action
        state["steps"] = steps
        return state

    # ------------------------------------------------------------------ #
    # Tools as nodes
    # ------------------------------------------------------------------ #

    def basic_retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic retrieval using vector-based RAG (Chroma/embeddings).
        """
        question = state.get("question", "")
        steps: List[str] = state.get("steps", [])
        steps.append("basic_retrieve")

        docs = basic_retrieval_tool.run(question)
        state["context"] = docs
        state["steps"] = steps
        return state

    def local_retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Local retrieval from filesystem (HR_LOCAL_DOCS_DIR or data/hr_local).
        """
        question = state.get("question", "")
        steps: List[str] = state.get("steps", [])
        steps.append("local_retrieve")

        docs = local_search_tool.run(question)
        state["context"] = docs
        state["steps"] = steps
        return state

    def generate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an answer using the current context docs via RAG-style prompt.
        """
        question = state.get("question", "")
        context_docs = state.get("context", [])
        steps: List[str] = state.get("steps", [])
        steps.append("generate_answer")

        answer = generator.generate_answer(
            question=question,
            context_docs=context_docs,
            hr_domain="hr_policies",
        )

        state["answer"] = answer
        state["steps"] = steps
        return state

    def send_email_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send the current answer by email, if a recipient can be extracted.
        """
        question = state.get("question", "")
        answer = state.get("answer", "")
        steps: List[str] = state.get("steps", [])
        steps.append("send_email_check")

        # If there's no answer, do nothing
        if not answer:
            steps.append("send_email_skipped_no_answer")
            state["steps"] = steps
            return state

        # Quick heuristic: only try if 'email' or 'mail' is in the question
        q_lower = question.lower()
        if "email" not in q_lower and "mail" not in q_lower:
            steps.append("send_email_skipped_not_requested")
            state["steps"] = steps
            return state

        # Extract recipient email from the question
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", question)
        recipient_email = match.group(0) if match else None
        if not recipient_email:
            steps.append("send_email_skipped_no_recipient")
            state["steps"] = steps
            return state

        # Build email body
        safe_answer_html = html.escape(answer).replace("\n", "<br>")
        body_html = f"""
        <html>
          <body>
            <p>
              Dear Colleague,<br><br>
              {safe_answer_html}<br><br>
              Best regards,<br>
              HR Team
            </p>
          </body>
        </html>
        """

        email_payload = {
            "recipient_email": recipient_email,
            "subject": "HR assistant response",
            "body": body_html,
        }

        steps.append("send_email_attempted")
        email_result = email_tool.run(email_payload)

        state["email_result"] = email_result
        state["steps"] = steps
        return state

    # ------------------------------------------------------------------ #
    # Router: interpret planner decision
    # ------------------------------------------------------------------ #

    def route_from_planner(state: Dict[str, Any]) -> str:
        """
        Use the planner's chosen action to route to the next node.
        """
        action = (state.get("next_action") or "").strip().upper()

        if action == "BASIC_RETRIEVE":
            return "basic_retrieve"
        if action == "LOCAL_RETRIEVE":
            return "local_retrieve"
        if action == "ANSWER_FROM_CONTEXT":
            return "generate_answer"
        if action == "SEND_EMAIL":
            return "send_email"
        # FINISH or anything else
        return "end"

    # ------------------------------------------------------------------ #
    # Build the graph
    # ------------------------------------------------------------------ #

    graph = StateGraph(dict)

    # Nodes
    graph.add_node("plan", planner_node)
    graph.add_node("basic_retrieve", basic_retrieve_node)
    graph.add_node("local_retrieve", local_retrieve_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("send_email", send_email_node)

    # Entry point
    graph.set_entry_point("plan")

    # Conditional routing from planner
    graph.add_conditional_edges(
        "plan",
        route_from_planner,
        {
            "basic_retrieve": "basic_retrieve",
            "local_retrieve": "local_retrieve",
            "generate_answer": "generate_answer",
            "send_email": "send_email",
            "end": END,
        },
    )

    # After tools, always go back to planner, except email, which ends
    graph.add_edge("basic_retrieve", "plan")
    graph.add_edge("local_retrieve", "plan")
    graph.add_edge("generate_answer", "plan")
    graph.add_edge("send_email", END)

    return graph