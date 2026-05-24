"""Hardcoded API key in source — OWASP A07 Identification & Auth Failures."""

ID = "sec_hardcoded_secret_01"
CATEGORY = "security_owasp_a07_auth_failures"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''import requests

API_KEY = "sk-prod-9f8e7d6c5b4a3210fedcba9876543210"
STRIPE_SECRET = "sk_live_51HxJpYKZvKuYvKuYvKuY"

def fetch_user_data(user_id: int) -> dict:
    response = requests.get(
        f"https://api.example.com/users/{user_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    return response.json()
'''
EXPECTED = {
    "should_contain_violations": ["Hardcoded", "Secret"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}
