"""Command injection via subprocess shell=True — OWASP A03."""

ID = "sec_command_injection_01"
CATEGORY = "security_owasp_a03_injection"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''import subprocess

def ping_host(hostname: str) -> str:
    """Ping a hostname and return the output."""
    result = subprocess.run(
        f"ping -c 3 {hostname}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
'''
EXPECTED = {
    "should_contain_violations": ["Command Injection"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}
