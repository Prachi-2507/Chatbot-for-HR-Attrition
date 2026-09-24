# InsightHR — Hybrid RAG + SQL with LangChain, ChromaDB, and Gemini

InsightHR is a portfolio project that answers HR questions using both:

- **Structured employee data** in SQLite
- **Unstructured HR policy documents** in ChromaDB
- **LangChain** for the application workflow
- **Gemini** for routing, SQL generation, RAG answers, and synthesis
- **React + FastAPI** for the interface/API

The bundled dataset is `data/hr_attrition.csv` (1,470 rows × 32 columns).

## Architecture

```text
User
  ↓
React UI
  ↓
FastAPI
  ↓
LangChain Router
  ├── SQL → Gemini text-to-SQL → SQLite
  ├── RAG → Gemini Embeddings → ChromaDB → Gemini answer
  └── Hybrid → SQL + RAG → Gemini synthesis
```

## Requirements

- Windows/macOS/Linux
- Python **3.14 is supported by this build**
- Node.js 18+
- A Google AI Studio API key

Current package versions were selected for the Python 3.14 setup. ChromaDB publishes a CPython 3.9+ ABI3 wheel, and current pandas releases publish CPython 3.14 wheels.

## Setup on Windows

Open the project folder in VS Code, then open a terminal.

### 1. Create the virtual environment

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Create `.env`

From `backend`:

```powershell
copy .env.example .env
```

Open `backend/.env` and replace:

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
```

with your Google AI Studio key.

### 4. Build SQLite + ChromaDB

```powershell
python prepare_data.py
```

This creates:

```text
data/hr_attrition.db
chroma_db/
```

### 5. Start backend

```powershell
uvicorn main:app --reload --port 8000
```

Keep this terminal open.

### 6. Start frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the localhost URL printed by Vite.

## Test questions

### SQL

- Which department has the highest attrition rate?
- What is the average monthly income of employees who left?
- How many employees work overtime?

### RAG

- What is the overtime approval process?
- How many PTO days do employees accrue?
- Can employees work remotely?

### Hybrid

- Why is attrition high in Sales, and what does the retention policy recommend?
- Is there a relationship between overtime and attrition, and what does policy say?

## Important

Do not commit `backend/.env`, API keys, `venv/`, `chroma_db/`, or `*.db` files to GitHub.

The HR policy Markdown files included in `docs/` are demo policy documents. The employee dataset is the bundled `HR_Employee_Cleaned.csv` supplied for this project.
