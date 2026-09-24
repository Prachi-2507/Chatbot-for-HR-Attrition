"""
Simple evaluation harness: runs a fixed set of test questions through the router,
checks routing accuracy against expected category, and prints a results table.

This is NOT a rigorous benchmark — it's a lightweight sanity-check suite that's
enough to demonstrate you thought about evaluation. For a stronger writeup, add
manual correctness grading (Y/N) per answer, or wire up RAGAS for the RAG half.
"""

from dotenv import load_dotenv
load_dotenv()

from router import route_query, classify_question
from database import build_database
from rag_pipeline import ensure_chroma

# (question, expected_category)
TEST_SET = [
    ("Which department has the highest attrition rate?", "sql"),
    ("What is the average monthly income for Sales Representatives?", "sql"),
    ("How many employees have low job satisfaction scores?", "sql"),
    ("What is the overtime approval process?", "rag"),
    ("How many PTO days do employees accrue per year?", "rag"),
    ("Can Lab Technicians work remotely?", "rag"),
    ("Why is attrition high in Sales, and what does our retention policy say about it?", "hybrid"),
    ("Is there a connection between overtime and attrition, and what does policy say we should do about it?", "hybrid"),
]


def run_eval():
    build_database()
    ensure_chroma()
    correct = 0
    print(f"{'Question':<70} {'Expected':<10} {'Got':<10} {'Match'}")
    print("-" * 105)

    for question, expected in TEST_SET:
        classification = classify_question(question)
        got = classification.get("category", "?")
        match = "✅" if got == expected else "❌"
        if got == expected:
            correct += 1

        truncated_q = (question[:67] + "...") if len(question) > 67 else question
        print(f"{truncated_q:<70} {expected:<10} {got:<10} {match}")

    accuracy = correct / len(TEST_SET) * 100
    print("-" * 105)
    print(f"Routing accuracy: {correct}/{len(TEST_SET)} ({accuracy:.1f}%)")


def run_full_answers():
    """Print full answers for manual quality review — paste results into your README."""
    build_database()
    ensure_chroma()
    for question, _ in TEST_SET:
        result = route_query(question)
        print(f"\nQ: {question}")
        print(f"Route: {result.get('source_type')}")
        print(f"A: {result.get('answer')[:400]}")
        print("-" * 80)


if __name__ == "__main__":
    print("=== Routing Accuracy Eval ===\n")
    run_eval()

    print("\n\n=== Full Answer Review (for manual grading) ===")
    run_full_answers()
