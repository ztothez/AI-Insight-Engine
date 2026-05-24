"""SQL injection in f-string — should be flagged as OWASP A03."""

ID = "sec_sql_injection_01"
CATEGORY = "security_owasp_a03_injection"
LANGUAGE = "python"
STRICTNESS = 3

CODE = '''import sqlite3
from typing import Any

def search_customers(db_path: str, search: str, status: str = "active") -> list[dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = f"""
        SELECT id, full_name, email, company, status, created_at
        FROM customers
        WHERE status = '{status}'
          AND (
              full_name LIKE '%{search}%'
              OR email LIKE '%{search}%'
              OR company LIKE '%{search}%'
          )
        ORDER BY created_at DESC
        LIMIT 25
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    return [dict(row) for row in rows]
'''

EXPECTED = {
    "should_contain_violations": ["SQL Injection"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}