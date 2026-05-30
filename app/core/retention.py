import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models import AnalysisRequest, AnalysisResponse, BlockedInput
from loguru import logger


RETENTION_DAYS = 90

async def purge_old_records(db: AsyncSession) -> None:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)
    subquery = select(AnalysisRequest.id).where(AnalysisRequest.created_at < cutoff)
    r1 = await db.execute(delete(AnalysisResponse).where(AnalysisResponse.request_id.in_(subquery)))
    logger.info(f"Purged {r1.rowcount} analysis responses")
    r2 = await db.execute(delete(AnalysisRequest).where(AnalysisRequest.created_at < cutoff))
    logger.info(f"Purged {r2.rowcount} analysis requests")
    r3 = await db.execute(delete(BlockedInput).where(BlockedInput.blocked_at < cutoff))
    logger.info(f"Purged {r3.rowcount} blocked inputs")
    await db.commit()