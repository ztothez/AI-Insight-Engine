"""SQL injection query — citation MUST come from a security book, not clean_code."""

ID = "rag_grounding_sql_security_01"
CATEGORY = "rag_grounding"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''def login(username: str, password: str):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return db.execute(query).fetchone()
'''
EXPECTED = {
    "should_contain_violations": ["SQL Injection"],
    "security_score_max": 5.0,
    "should_have_citations": True,
    "expected_citation_sources_any": [
        "web_application_hackers_handbook",
        "secure_coding_principles",
        "web_security",
    ],
}
