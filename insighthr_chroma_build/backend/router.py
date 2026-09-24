"""LLM router for SQL, RAG, and hybrid HR questions."""

import json
import os
import re

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from sql_agent import query_sql
from rag_pipeline import query_rag

load_dotenv()

ROUTER_PROMPT = """Classify the following HR question into exactly one category:

- sql: Answerable from structured employee data such as attrition, department comparisons,
  income, tenure, job satisfaction, demographics, counts, or employee characteristics.
- rag: Answerable from HR policy documents such as overtime, PTO, remote work, retention,
  approval processes, or policy rules.
- hybrid: Requires BOTH structured employee data AND policy context.

Respond with ONLY JSON:
{{"category":"sql|rag|hybrid","reasoning":"one short sentence"}}

Question: {question}
"""

SYNTHESIS_PROMPT = """You are an HR analytics assistant. Combine the following two pieces of information into one
clear answer. Distinguish employee-data findings from policy guidance. Do not invent information.

Question: {question}

Data finding:
{sql_answer}

Policy context:
{rag_answer}

Give a concise, useful answer and mention policy sources when available.
"""


def get_llm():
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
def classify_question(question: str) -> dict:
    response = get_llm().invoke(
        ROUTER_PROMPT.format(question=question)
    )

    content = response.content

    if isinstance(content, list):
        raw = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ).strip()
    else:
        raw = str(content).strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)

        if parsed.get("category") not in {"sql", "rag", "hybrid"}:
            raise ValueError("Invalid category")

        return parsed

    except (json.JSONDecodeError, ValueError):
        return {
            "category": "hybrid",
            "reasoning": "Fallback because router output was not valid JSON."
        }


def route_query(question: str) -> dict:
    classification = classify_question(question)
    category = classification["category"]

    if category == "sql":
        result = query_sql(question)
        result["routing"] = classification
        return result

    if category == "rag":
        result = query_rag(question)
        result["routing"] = classification
        return result

    sql_result = query_sql(question)
    rag_result = query_rag(question)
    synthesis = get_llm().invoke(
        SYNTHESIS_PROMPT.format(
            question=question,
            sql_answer=sql_result["answer"],
            rag_answer=rag_result["answer"],
        )
    )

    synthesis_content = synthesis.content

    if isinstance(synthesis_content, list):
        synthesis_answer = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in synthesis_content
        )
    else:
        synthesis_answer = str(synthesis_content)

    synthesis_answer = synthesis_answer.strip()

    return {
        "answer": synthesis_answer,
        "source_type": "hybrid",
        "routing": classification,
        "sql_component": sql_result["answer"],
        "rag_component": rag_result["answer"],
        "rag_sources": rag_result.get("sources", []),
    }