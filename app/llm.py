import json
from typing import List
import ollama

MODEL_NAME = "gemma3:4b"  # or "llama3" etc., but must exist in Ollama


def _chat_with_model(system_prompt: str, user_content: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response["message"]["content"].strip()


def generate_sql_from_question(question: str, schema_context: str) -> str:
    system_prompt = (
        "You are an expert SQL query generator for an SQLite database. "
        "Only return a single SELECT SQL query, no explanations or markdown. "
        "Use only the tables and columns from the given schema. "
        "Limit results to at most 100 rows."
    )

    user_content = f"""Schema:
{schema_context}

Question: {question}

Return ONLY the SQL query:"""

    sql = _chat_with_model(system_prompt, user_content)

    if sql.startswith("```"):
        parts = sql.split("```")
        if len(parts) >= 2:
            sql = parts[1]
        if sql.strip().startswith("sql"):
            sql = sql[3:]
    return sql.strip().rstrip(";") + ";"


def generate_answer_summary(question: str, query_result: List[dict], sql_used: str) -> str:
    system_prompt = (
        "You are a helpful data analyst. "
        "Explain SQL query results in 2-3 sentences for a business user."
    )

    result_text = json.dumps(query_result[:10], indent=2)

    user_content = f"""User question: {question}

SQL used:
{sql_used}

First 10 rows of result (JSON):
{result_text}

Explain the key insights in 2-3 short sentences:"""

    summary = _chat_with_model(system_prompt, user_content)
    return summary.strip()
