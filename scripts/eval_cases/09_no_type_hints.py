"""No type hints, no docstrings — maintainability issues."""

ID = "clean_no_type_hints_01"
CATEGORY = "clean_code_violation"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''def fetch_user(user_id):
    user = db.get(user_id)
    if user:
        return user
    return None

def update_user(user_id, data):
    user = fetch_user(user_id)
    if not user:
        return False
    for key, value in data.items():
        user[key] = value
    db.save(user)
    return True

def process(items):
    results = []
    for item in items:
        result = transform(item)
        if result:
            results.append(result)
    return results
'''
EXPECTED = {
    "maintainability_score_max": 7.5,
    "should_contain_violations": [["type hint", "type", "annotation", "docstring"]],
    "should_have_citations": True,
}
