"""FastAPI server for the InsightHR hybrid RAG + SQL assistant."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import build_database
from rag_pipeline import ensure_chroma
from router import route_query

app = FastAPI(title="InsightHR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    source_type: str
    routing: dict | None = None
    rag_sources: list[str] | None = None


@app.on_event("startup")
def startup():
    build_database()
    ensure_chroma()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        result = route_query(request.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ChatResponse(
        answer=result.get("answer", ""),
        source_type=result.get("source_type", "unknown"),
        routing=result.get("routing"),
        rag_sources=result.get("rag_sources") or result.get("sources"),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
