from typing import TypedDict, List, Optional


class AgentState(TypedDict, total=False):
    # Core I/O
    question: str
    context: List[str]
    answer: str

    # Reasoning / control
    intent: Optional[str]
    needs_retrieval: bool
    retrieval_attempts: int

    is_complete: bool
    error: str
    steps: List[str]

    # Internal bookkeeping
    original_question: str
    context_is_relevant: bool
    answer_is_valid: bool