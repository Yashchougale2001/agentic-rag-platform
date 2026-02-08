
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agent.graph_agent import build_basic_hr_agent

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    steps: list
    context_sources: list


# Initialize once
compiled_graph: Any = build_basic_hr_agent().compile()


@router.post("/", response_model=QueryResponse)
def query_chatbot(req: QueryRequest):
    try:
        result = compiled_graph.invoke({"question": req.question})

        answer = result.get("answer", "")
        steps = result.get("steps", [])
        context = result.get("context", [])

        sources = [ 
            d.get("metadata", {}).get("source", "unknown")
            for d in context
        ]

        return QueryResponse(
            answer=answer,
            steps=steps,
            context_sources=sorted(set(sources)),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
