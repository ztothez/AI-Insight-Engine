"""IDOR — endpoint accepts user_id from path without auth check. OWASP A01."""

ID = "sec_broken_access_01"
CATEGORY = "security_owasp_a01_broken_access"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/users/<int:user_id>/orders")
def get_user_orders(user_id: int):
    # No authentication or authorization check
    # Any caller can read any user's orders just by changing the URL
    orders = db.query("SELECT * FROM orders WHERE user_id = %s", (user_id,))
    return jsonify(orders)
'''
EXPECTED = {
    "should_contain_violations": ["IDOR", "authorization"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}
