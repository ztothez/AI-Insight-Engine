const API_BASE = '';

export async function analyzeCode(codeSnippet, strictnessLevel) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code_snippet: codeSnippet,
      language: 'python',
      strictness_level: strictnessLevel,
    }),
  });

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    const err = new Error(body.detail || res.statusText || 'Request failed');
    err.status = res.status;
    err.detail = body.detail;
    throw err;
  }

  return body;
}

export async function runAgent(codeSnippet) {
  const res = await fetch(`${API_BASE}/agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code_snippet: codeSnippet }),
  });

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    const err = new Error(body.detail || res.statusText || 'Request failed');
    err.status = res.status;
    err.detail = body.detail;
    throw err;
  }

  return body;
}

export function parseApiError(err) {
  if (err.status === 400) {
    return {
      title: 'Invalid input',
      message:
        typeof err.detail === 'string'
          ? err.detail
          : "Your input doesn't appear to be a code snippet. Submit Python code to analyze.",
      recovery: 'Try the sample snippet or paste a Python function.',
    };
  }
  if (err.status === 429) {
    return {
      title: 'Rate limit reached',
      message: 'You can run 5 analyses per minute. Please wait before trying again.',
      recovery: 'Wait about 60 seconds, then retry.',
      rateLimited: true,
    };
  }
  if (err.status === 503) {
    return {
      title: 'Service unavailable',
      message: 'The analysis service is temporarily unavailable.',
      recovery: 'Click Retry in a moment.',
      retry: true,
    };
  }
  return {
    title: 'Something went wrong',
    message: err.message || 'An unexpected error occurred.',
    recovery: 'Check that the API is running and try again.',
    retry: true,
  };
}
