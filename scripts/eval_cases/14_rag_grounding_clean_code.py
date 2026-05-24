"""Pythonic decorator pattern — citation should come from a clean-code book."""

ID = "rag_grounding_clean_code_01"
CATEGORY = "rag_grounding"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''def timing_decorator(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.3f}s")
        return result
    return wrapper

@timing_decorator
def slow_function():
    import time
    time.sleep(1)
'''
EXPECTED = {
    "maintainability_score_min": 6.0,
    "should_have_citations": True,
    "expected_citation_sources_any": [
        "clean_code_python",
        "software_engineering_python",
    ],
}
