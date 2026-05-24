"""MD5 used for password hashing — OWASP A02 Cryptographic Failures."""

ID = "sec_weak_crypto_01"
CATEGORY = "security_owasp_a02_crypto_failures"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''import hashlib

def hash_password(password: str) -> str:
    """Hash a user password before storing it in the database."""
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash
'''
EXPECTED = {
    "should_contain_violations": ["Crypto", "Hash"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}
