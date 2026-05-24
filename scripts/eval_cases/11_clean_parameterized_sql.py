"""Parameterized SQL — the correct way. Should NOT be flagged."""

ID = "neg_clean_parameterized_sql_01"
CATEGORY = "negative_clean_secure_code"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''import sqlite3
from typing import Any

def get_user_by_id(db_path: str, user_id: int) -> dict[str, Any] | None:
    """Fetch a single user by ID using parameterized SQL."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT id, email, full_name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
'''
EXPECTED = {
    "should_contain_violations": [],
    "security_score_min": 8.0,
    "should_have_citations": True,
}
