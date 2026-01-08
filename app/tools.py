from typing import List, Any, Dict
from .db import get_db

def list_tables() -> List[str]:
    """Return all non-internal SQLite table names."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def describe_table(table_name: str) -> List[Dict[str, Any]]:
    """Return column metadata for a given table."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name});")
    cols = []
    for cid, name, col_type, notnull, dflt_value, pk in cur.fetchall():
        cols.append(
            {
                "name": name,
                "type": col_type,
                "notnull": bool(notnull),
                "default": dflt_value,
                "primary_key": bool(pk),
            }
        )
    conn.close()
    return cols

def run_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT-style query and return rows as dicts."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    columns = [d[0] for d in cur.description] if cur.description else []
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return result

def validate_result(result: Any, intent: str) -> bool:
    """Placeholder validator, to be made smarter later."""
    return result is not None
