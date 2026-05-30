import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import BlockedInput

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin_key(x_admin_key: str = Header(None)):
    if not x_admin_key or x_admin_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/blocked-inputs")
async def list_blocked_inputs(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    result = await db.execute(select(BlockedInput))
    blocked_inputs = result.scalars().all()
    return [
        dict(
            id=bi.id,
            input_snippet=bi.input_snippet,
            reason=bi.reason,
            matched_pattern=bi.matched_pattern,
            client_ip=bi.client_ip,
            blocked_at=bi.blocked_at,
        )
        for bi in blocked_inputs
    ]