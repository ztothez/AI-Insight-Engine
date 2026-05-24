"""One-shot: create the blocked_inputs table in the running Postgres.

Run once after adding the BlockedInput model. Safe to re-run — uses CREATE
TABLE IF NOT EXISTS semantics under the hood (via metadata.create_all).
"""
import asyncio
from app.db.database import engine
from app.db.models import Base


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Schema sync complete")


if __name__ == "__main__":
    asyncio.run(main())
