# InsightHR – Hybrid RAG + SQL HR Assistant

InsightHR is an AI-powered HR assistant that allows users to ask questions about employee data and HR policies using natural language.

It combines **SQL-based data retrieval** with **Retrieval-Augmented Generation (RAG)** to provide relevant and contextual answers.

## 🚀 Features

- Natural-language HR question answering
- Text-to-SQL for querying employee data
- RAG-based retrieval from HR policy documents
- Intelligent routing between SQL and document retrieval
- Semantic search using ChromaDB
- Gemini-powered embeddings and LLM responses
- React-based conversational interface
- Supabase integration
- Validation of generated SQL queries

## 🏗️ Architecture

The system routes user questions to the appropriate source:

```text
                    User Query
                        |
                        v
                LLM Query Router
                 /             \
                /               \
              SQL               RAG
               |                 |
               v                 v
        Employee Database   HR Policy Documents
               |                 |
               v                 v
            SQL Result       Retrieved Context
                \               /
                 \             /
                  v           v
                    LLM Response
                         |
                         v
                   User Interface
