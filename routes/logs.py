"""
Log viewer routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import DownloadLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    level: Optional[str] = None,
    account_id: Optional[int] = None,
    task_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List logs with filtering and pagination."""
    query = select(DownloadLog).order_by(DownloadLog.timestamp.desc())

    filters = []
    if level:
        filters.append(DownloadLog.level == level)
    if account_id:
        filters.append(DownloadLog.account_id == account_id)
    if task_id:
        filters.append(DownloadLog.task_id == task_id)
    if search:
        filters.append(DownloadLog.message.ilike(f"%{search}%"))

    if filters:
        query = query.where(and_(*filters))

    # Count total
    count_query = select(func.count(DownloadLog.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "data": [
            {
                "id": log.id,
                "task_id": log.task_id,
                "account_id": log.account_id,
                "level": log.level,
                "message": log.message,
                "details": log.details,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("")
async def clear_logs(db: AsyncSession = Depends(get_db)):
    """Clear all logs."""
    await db.execute(DownloadLog.__table__.delete())
    return {"message": "Semua log berhasil dihapus"}
