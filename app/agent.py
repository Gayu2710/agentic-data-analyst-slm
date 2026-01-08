import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from .tools import list_tables, describe_table, run_query, validate_result

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class Agent:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.steps: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.sql_used: str = ""

    def log_step(
        self,
        step_num: int,
        intent: str,
        tool: str,
        tool_input: Any,
        tool_output: Any,
        decision: str,
        error: str = None,
    ):
        step = {
            "step": step_num,
            "intent": intent,
            "tool": tool,
            "tool_input": tool_input,
            "tool_output": tool_output if tool_output is not None else [],
            "decision": decision,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }
        self.steps.append(step)
        return step

    def save_trace(self):
        trace = {
            "request_id": self.request_id,
            "steps": self.steps,
            "total_steps": len(self.steps),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
        }
        trace_path = LOGS_DIR / f"{self.request_id}.json"
        with open(trace_path, "w") as f:
            json.dump(trace, f, indent=2)
        return trace

    def query(self, user_question: str) -> Dict[str, Any]:
        step_num = 1

        # Step 1: Goal identification
        self.log_step(
            step_num=step_num,
            intent="Identify goal from user question",
            tool="none",
            tool_input={"question": user_question},
            tool_output="Goal identified: Analyze database to answer user query",
            decision="Proceed to schema exploration",
        )
        step_num += 1

        # Step 2: List available tables
        try:
            tables = list_tables()
            self.log_step(
                step_num=step_num,
                intent="Explore available tables in database",
                tool="list_tables",
                tool_input={},
                tool_output=tables,
                decision=f"Found {len(tables)} tables. Proceeding to describe relevant tables.",
            )
        except Exception as e:
            self.log_step(
                step_num=step_num,
                intent="Explore available tables",
                tool="list_tables",
                tool_input={},
                tool_output=None,
                decision="Error occurred, cannot proceed",
                error=str(e),
            )
            return {"error": f"Failed to list tables: {e}"}
        step_num += 1

        # Step 3: Describe key tables
        key_tables = [
            t for t in tables if t in ["orders", "customers", "order_items", "payments"]
        ]
        for table_name in key_tables[:2]:
            try:
                columns = describe_table(table_name)
                col_names = [c["name"] for c in columns]
                self.log_step(
                    step_num=step_num,
                    intent=f"Understand schema of {table_name} table",
                    tool="describe_table",
                    tool_input={"table": table_name},
                    tool_output=col_names,
                    decision=(
                        f"Table {table_name} has columns: "
                        f"{', '.join(col_names[:3])}... Proceeding to generate query."
                    ),
                )
                step_num += 1
            except Exception as e:
                self.log_step(
                    step_num=step_num,
                    intent=f"Describe {table_name}",
                    tool="describe_table",
                    tool_input={"table": table_name},
                    tool_output=None,
                    decision="Error occurred",
                    error=str(e),
                )
                step_num += 1

        # Step 4: Plan SQL query using Gemma (with fallback)
        sql_query = self._plan_sql_query(user_question)
        self.sql_used = sql_query
        self.log_step(
            step_num=step_num,
            intent="Plan SQL query based on question using LLM",
            tool="gemma_llm",
            tool_input={"question": user_question},
            tool_output=sql_query,
            decision="SQL query planned. Proceeding to execution.",
        )
        step_num += 1

        # Step 5: Execute query
        try:
            result = run_query(sql_query)
            self.log_step(
                step_num=step_num,
                intent="Execute SQL query",
                tool="run_query",
                tool_input={"sql": sql_query},
                tool_output=result[:5] if result else [],
                decision=f"Query executed successfully. Received {len(result)} rows.",
            )
        except Exception as e:
            self.log_step(
                step_num=step_num,
                intent="Execute SQL query",
                tool="run_query",
                tool_input={"sql": sql_query},
                tool_output=None,
                decision="Error occurred during query execution",
                error=str(e),
            )
            return {"error": f"Query execution failed: {e}", "sql_used": sql_query}
        step_num += 1

        # Step 6: Validate result
        is_valid = validate_result(result, user_question)
        self.log_step(
            step_num=step_num,
            intent="Validate query result against user intent",
            tool="validate_result",
            tool_input={"result": len(result), "intent": user_question},
            tool_output=f"Valid: {is_valid}",
            decision=(
                "Result validated. Preparing final answer."
                if is_valid
                else "Result validation failed, may need retry."
            ),
        )
        step_num += 1

        # Step 7: Prepare final answer
        final_answer = {
            "question": user_question,
            "answer": result,
            "num_rows": len(result),
            "status": "success",
            "sql_used": sql_query,
        }

        self.log_step(
            step_num=step_num,
            intent="Prepare final answer",
            tool="none",
            tool_input={},
            tool_output=final_answer,
            decision="Agent loop complete.",
        )

        self.save_trace()
        return final_answer

    # ---------- LLM + fallback ----------

    def _plan_sql_query(self, user_question: str) -> str:
        """
        Use Gemma (via llm.py) to generate SQL.
        Falls back to heuristic rules if LLM fails.
        """
        try:
            from .llm import generate_sql_from_question

            tables = list_tables()
            schema_lines = []
            for table_name in tables:
                try:
                    columns = describe_table(table_name)
                    col_desc = ", ".join(
                        [f"{c['name']} ({c['type']})" for c in columns]
                    )
                    schema_lines.append(f"Table '{table_name}': {col_desc}")
                except Exception:
                    pass

            schema_context = "\n".join(schema_lines)
            sql = generate_sql_from_question(user_question, schema_context)
            return sql

        except Exception as e:
            print(f"LLM SQL generation failed: {e}. Falling back to heuristics.")
            return self._fallback_sql_query(user_question)

    def _fallback_sql_query(self, question: str) -> str:
        """
        Your original heuristic logic (used only if Gemma fails).
        """
        question_lower = question.lower()

        if "order" in question_lower and "status" in question_lower:
            return (
                "SELECT order_status, COUNT(*) as num_orders "
                "FROM orders GROUP BY order_status ORDER BY num_orders DESC;"
            )
        elif "customer" in question_lower:
            return "SELECT COUNT(*) as total_customers FROM customers;"
        elif "payment" in question_lower:
            return (
                "SELECT payment_type, COUNT(*) as num_payments "
                "FROM payments GROUP BY payment_type ORDER BY num_payments DESC;"
            )
        else:
            return (
                "SELECT order_status, COUNT(*) as num_orders "
                "FROM orders GROUP BY order_status ORDER BY num_orders DESC;"
            )

