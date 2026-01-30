from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agent.agent_core import ITRAGAgentCore
from src.agent.graph_agent import build_it_graph_agent

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    use_agent: bool = True


class QueryResponse(BaseModel):
    answer: str
    steps: list
    context_sources: list


# Initialize once
core_agent = ITRAGAgentCore()
compiled_graph: Any = build_it_graph_agent().compile()


@router.post("/", response_model=QueryResponse)
def query_chatbot(req: QueryRequest):
    try:
        if req.use_agent:
            result = compiled_graph.invoke({"question": req.question})
            answer = result.get("answer", "")
            steps = result.get("steps", [])
            context = result.get("context", [])
        else:
            state = core_agent.run_rag(req.question)
            answer = state.answer
            steps = state.steps
            context = state.context

        sources = []
        for d in context:
            src = d.get("metadata", {}).get("source", "unknown")
            sources.append(src)

        return QueryResponse(
            answer=answer,
            steps=steps,
            context_sources=list(sorted(set(sources))),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))