# api/routes/feedback.py

from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.agent.tools.feedback_tool import FeedbackTool

router = APIRouter(prefix="/feedback", tags=["feedback"])

feedback_tool = FeedbackTool()  # logs to logs/feedback.jsonl by default


class FeedbackRequest(BaseModel):
    user_id: str
    role: Literal["admin", "hr", "employee"]
    question: str
    answer: str
    rating: int  # e.g. -1, 0, 1 or 1–5
    comment: Optional[str] = None
    context_sources: Optional[List[str]] = None


@router.post("/")
def submit_feedback(req: FeedbackRequest):
    feedback_tool.submit(
        user_id=req.user_id,
        role=req.role,
        question=req.question,
        answer=req.answer,
        rating=req.rating,
        comment=req.comment,
        context_sources=req.context_sources,
    )
    return {"status": "ok"}