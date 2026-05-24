"""XSS via f-string in render_template_string — should be flagged as OWASP A03."""

ID = "sec_xss_01"
CATEGORY = "security_owasp_a03_injection"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route("/greet")
def greet():
    name = request.args.get("name", "Guest")
    # Vulnerable to XSS if 'name' is not properly sanitized
    return render_template_string(f"<h1>Hello, {name}!</h1>")
'''
EXPECTED = {
    "should_contain_violations": ["XSS"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}
