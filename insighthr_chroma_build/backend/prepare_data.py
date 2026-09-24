"""One-command local setup for the HR SQLite DB and ChromaDB."""

from database import build_database
from rag_pipeline import ingest_documents

if __name__ == "__main__":
    print("Building SQLite database...")
    build_database()
    print("Building ChromaDB from HR policy documents...")
    n = ingest_documents(reset=True)
    print(f"Done. Indexed {n} policy chunks.")
