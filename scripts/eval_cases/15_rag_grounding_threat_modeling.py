"""Trust-boundary issue — citation should come from threat modeling or security engineering."""

ID = "rag_grounding_threat_modeling_01"
CATEGORY = "rag_grounding"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''from flask import Flask, request

app = Flask(__name__)

@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    # Trust boundary violation: trusts client-supplied 'is_admin' flag
    user_id = request.json["user_id"]
    is_admin = request.json.get("is_admin", False)
    if is_admin:
        db.execute("DELETE FROM users WHERE id = %s", (user_id,))
        return {"status": "deleted"}
    return {"status": "forbidden"}, 403
'''
EXPECTED = {
    "should_contain_violations": ["Trust", "Access Control", "Authorization"],
    "security_score_max": 4.0,
    "should_have_citations": True,
    "expected_citation_sources_any": [
        "threat_modeling",
        "security_engineering",
        "secure_coding_principles",
    ],
}
