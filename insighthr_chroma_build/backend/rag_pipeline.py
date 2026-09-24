"""Local ChromaDB RAG pipeline using Gemini for embeddings and generation."""

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "chroma_db"))
COLLECTION_NAME = "hr_policy_documents"

RAG_SYSTEM_PROMPT = """You are an HR policy assistant.
Answer the user's question using ONLY the provided policy excerpts.
If the excerpts do not contain enough information, say that the policy documents do not provide enough information.
Do not invent company policies.
Always mention the policy source(s) you used.

Policy excerpts:
{context}

Question: {question}
"""


def get_embeddings():
    """Create Gemini embeddings for ChromaDB."""
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def get_vector_store() -> Chroma:
    """Open the persistent local Chroma collection."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embeddings(),
    )


def ingest_documents(docs_dir: str | Path = DOCS_DIR, reset: bool = True) -> int:
    """Chunk and embed all Markdown policy docs into local ChromaDB."""
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY is missing. Add it to backend/.env")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    all_chunks: list[Document] = []
    for filepath in sorted(docs_dir.glob("*.md")):
        source = filepath.stem.replace("_", " ").title()
        text = filepath.read_text(encoding="utf-8")
        for chunk_index, chunk in enumerate(splitter.split_text(text)):
            all_chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": source,
                        "file": filepath.name,
                        "chunk": chunk_index,
                    },
                )
            )

    if not all_chunks:
        raise ValueError(f"No .md policy documents found in {docs_dir}")

    if reset and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    vector_store = get_vector_store()
    vector_store.add_documents(all_chunks)
    return len(all_chunks)


def chroma_ready() -> bool:
    """Return True when the local Chroma collection contains vectors."""
    if not CHROMA_DIR.exists():
        return False
    try:
        collection = get_vector_store()._collection
        return collection.count() > 0
    except Exception:
        return False


def ensure_chroma() -> None:
    if not chroma_ready():
        n = ingest_documents(reset=True)
        print(f"ChromaDB initialized with {n} policy chunks.")


def query_rag(question: str, k: int = 4) -> dict:
    """Retrieve relevant policy chunks and generate a grounded Gemini answer."""
    ensure_chroma()
    vector_store = get_vector_store()
    retrieved_docs = vector_store.similarity_search(question, k=k)

    context = "\n\n".join(
        f"[{doc.metadata.get('source', 'Unknown')}]: {doc.page_content}"
        for doc in retrieved_docs
    )

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    prompt = RAG_SYSTEM_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)

    sources = sorted({doc.metadata.get("source", "Unknown") for doc in retrieved_docs})
    return {
        "answer": response.content,
        "source_type": "rag",
        "sources": sources,
        "retrieved_chunks": [
            {
                "source": doc.metadata.get("source", "Unknown"),
                "text": doc.page_content[:240] + ("..." if len(doc.page_content) > 240 else ""),
            }
            for doc in retrieved_docs
        ],
    }


if __name__ == "__main__":
    n = ingest_documents()
    print(f"Ingested {n} chunks into local ChromaDB at {CHROMA_DIR}.")
    print(query_rag("What is the overtime approval process?"))
