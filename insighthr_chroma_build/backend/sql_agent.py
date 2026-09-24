"""LangChain-powered text-to-SQL workflow for the HR employee dataset."""

import json
import re
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import create_engine, text

from database import get_connection_string

load_dotenv()

SQL_SYSTEM_GUIDANCE = """You are a careful HR data analyst.
You have access to one SQLite table named employees.
Use only columns that actually exist in the schema.

Important dataset facts:
- Attrition is encoded as 1 = employee left and 0 = employee stayed.
- The dataset contains 1,470 employee records and 32 columns.
- Only SELECT queries are allowed.

When asked for an attrition rate, calculate:
SUM(CASE WHEN Attrition = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)

Return ONLY a JSON object with this shape:
{{"sql": "SELECT ...", "explanation": "short explanation"}}
"""


def get_llm():
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def get_schema() -> str:
    """Read the actual SQLite schema so the model does not invent columns."""
    engine = create_engine(get_connection_string())
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
    return "\n".join(f"- {row[1]} ({row[2]})" for row in rows)


def clean_json(raw) -> dict:
    if isinstance(raw, list):
        raw = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in raw
        )
    else:
        raw = str(raw)

    raw = raw.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)

def validate_sql(sql: str) -> str:
    """Allow only a single read-only SELECT statement against employees."""
    sql = sql.strip().rstrip(";").strip()
    if not sql.lower().startswith("select"):
        raise ValueError("Generated SQL is not a SELECT statement.")
    if ";" in sql:
        raise ValueError("Multiple SQL statements are not allowed.")
    forbidden = r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma)\b"
    if re.search(forbidden, sql, flags=re.I):
        raise ValueError("Unsafe SQL operation detected.")
    if "employees" not in sql.lower():
        raise ValueError("Generated SQL must query the employees table.")
    return sql

def query_sql(question: str) -> dict:
    """Generate safe SQL with Gemini, execute it, then summarize the result with Gemini."""
    schema = get_schema()

    prompt = f"""{SQL_SYSTEM_GUIDANCE}

Actual schema:
{schema}

User question:
{question}
"""

    response = get_llm().invoke(prompt)
    content = response.content

    if isinstance(content, list):
        raw = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    else:
        raw = str(content)

    plan = clean_json(raw)
    sql = validate_sql(plan["sql"])

    engine = create_engine(get_connection_string())

    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()

    result_text = json.dumps(
        [dict(row) for row in rows],
        default=str
    )

    answer_prompt = f"""You are an HR analytics assistant.
Answer the user's question using ONLY the SQL result below.
If the result is empty, say no matching records were found.
Mention the relevant numbers clearly and do not invent data.

Question: {question}
SQL: {sql}
SQL result: {result_text}
"""

    answer_content = get_llm().invoke(answer_prompt).content

    if isinstance(answer_content, list):
        answer = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in answer_content
        )
    else:
        answer = str(answer_content)

    answer = answer.strip()

    return {
        "answer": answer,
        "source_type": "sql",
        "sql": sql,
        "rows": [dict(row) for row in rows],
    }
