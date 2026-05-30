import sys
import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

def check(name: str, response: httpx.Response, expected_status: int = 200):
    if response.status_code != expected_status:
        print(f"FAIL: {name}")
        sys.exit(1)
    else:
        print(f"OK: {name}")

def run():
    response = httpx.get(f"{BASE_URL}/health")
    check("GET /health", response)
    response = httpx.post(f"{BASE_URL}/analyze", json={"code_snippet": "print('hello')", "language": "python", "strictness_level": 1})
    check("POST /analyze with code snippet", response)
    response = httpx.post(f"{BASE_URL}/agent", json={"code_snippet": "print('hello')"})
    check("POST /agent with code snippet", response)

if __name__ == "__main__":
    run()