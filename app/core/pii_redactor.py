import re

REDACTION_PATTERNS = [
    (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '[REDACTED_EMAIL]'),
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED_IP]'),
    (r'(?i)(api_key|secret|token|bearer)\s*[=:]\s*["\']?[A-Za-z0-9\-_]{20,}["\']?', '[REDACTED_API_KEY]'),
    (r'\bpassword\b\s*=\s*["\'][^"\']*["\']', '[REDACTED_PASSWORD]')
]

def redact(text: str) -> str:
    for pattern, replacement in REDACTION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text