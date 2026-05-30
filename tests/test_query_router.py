"""Unit tests for the /audit query router."""
import pytest

from app.core.query_router import route, RouteTarget


class TestRouting:

    def test_code_snippet_goes_to_rag(self):
        code = "def login(user, password):\n    return db.execute(f'SELECT * FROM users WHERE u={user}')"
        assert route(code) == RouteTarget.RAG

    def test_question_goes_to_agent(self):
        query = "What is the risk of using f-strings in SQL?"
        assert route(query) == RouteTarget.AGENT

    def test_how_question_goes_to_agent(self):
        query = "How complex is a function with 5 nested loops?"
        assert route(query) == RouteTarget.AGENT

    def test_long_code_with_question_word_in_comment_still_rag(self):
        # 200+ chars of code, even with "what" in a comment, stays RAG
        code = """def process(items):
    # What this does: iterates and transforms
    results = []
    for item in items:
        results.append(transform(item))
    for item in items:
        results.append(validate(item))
    return results"""
        assert route(code) == RouteTarget.RAG

    def test_short_question_with_code_goes_to_agent(self):
        query = "Should I use this: def foo(): return 1"
        assert route(query) == RouteTarget.AGENT