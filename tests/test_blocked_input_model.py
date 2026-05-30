"""Smoke test for the BlockedInput model.

This doesn't hit a real database — it just verifies the model is
syntactically valid and has the columns we expect.
"""
from app.db.models import BlockedInput, Base


def test_model_is_registered():
    assert BlockedInput.__tablename__ == "blocked_inputs"
    assert "blocked_inputs" in Base.metadata.tables


def test_required_columns_exist():
    cols = {c.name for c in BlockedInput.__table__.columns}
    required = {
        "id",
        "blocked_at",
        "client_ip",
        "reason",
        "matched_pattern",
        "input_snippet",
        "input_length",
        "user_agent",
    }
    missing = required - cols
    assert not missing, f"Missing columns: {missing}"


def test_nullable_constraints():
    table = BlockedInput.__table__
    # These columns must NOT be nullable — they're required for audit
    assert not table.c.blocked_at.nullable
    assert not table.c.reason.nullable
    assert not table.c.input_snippet.nullable
    assert not table.c.input_length.nullable

    # These can be null (we may not always have them)
    assert table.c.client_ip.nullable
    assert table.c.matched_pattern.nullable
    assert table.c.user_agent.nullable


def test_indexed_columns():
    table = BlockedInput.__table__
    indexed = {c.name for c in table.columns if c.index}
    # blocked_at and reason are the two highest-traffic query columns
    assert "blocked_at" in indexed
    assert "reason" in indexed
