"""
Dashboard statistics routes.
"""
import datetime
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query

from database import get_db
from models import Account, DownloadTask, ScheduleJob, DownloadLog, TaskStatus, AccountStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview statistics."""
    # Total tasks
    total_tasks = (await db.execute(select(func.count(DownloadTask.id)))).scalar() or 0

    # Items downloaded (completed)
    items_downloaded = (await db.execute(
        select(func.count(DownloadTask.id)).where(DownloadTask.status == TaskStatus.COMPLETED.value)
    )).scalar() or 0

    # Active accounts
    active_accounts = (await db.execute(
        select(func.count(Account.id)).where(Account.status == AccountStatus.ACTIVE.value)
    )).scalar() or 0

    # Total accounts
    total_accounts = (await db.execute(select(func.count(Account.id)))).scalar() or 0

    # Active schedules
    active_schedules = (await db.execute(
        select(func.count(ScheduleJob.id)).where(ScheduleJob.is_active == True)
    )).scalar() or 0

    # Failed tasks
    failed_tasks = (await db.execute(
        select(func.count(DownloadTask.id)).where(DownloadTask.status == TaskStatus.FAILED.value)
    )).scalar() or 0

    # Pending tasks
    pending_tasks = (await db.execute(
        select(func.count(DownloadTask.id)).where(DownloadTask.status == TaskStatus.PENDING.value)
    )).scalar() or 0

    # Running tasks
    running_tasks = (await db.execute(
        select(func.count(DownloadTask.id)).where(DownloadTask.status == TaskStatus.RUNNING.value)
    )).scalar() or 0

    # Total file size (in MB)
    total_size_bytes = (await db.execute(
        select(func.sum(DownloadTask.file_size)).where(DownloadTask.file_size.isnot(None))
    )).scalar() or 0
    total_size_mb = round(total_size_bytes / (1024 * 1024), 2)

    # Today's downloads
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_downloads = (await db.execute(
        select(func.count(DownloadTask.id)).where(
            and_(
                DownloadTask.status == TaskStatus.COMPLETED.value,
                DownloadTask.completed_at >= today,
            )
        )
    )).scalar() or 0

    return {
        "total_tasks": total_tasks,
        "items_downloaded": items_downloaded,
        "active_accounts": active_accounts,
        "total_accounts": total_accounts,
        "active_schedules": active_schedules,
        "failed_tasks": failed_tasks,
        "pending_tasks": pending_tasks,
        "running_tasks": running_tasks,
        "total_size_mb": total_size_mb,
        "today_downloads": today_downloads,
    }


@router.get("/activity")
async def get_activity(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get download activity data for chart."""
    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=days)

    # Get all completed tasks in range
    result = await db.execute(
        select(DownloadTask.completed_at)
        .where(
            and_(
                DownloadTask.status == TaskStatus.COMPLETED.value,
                DownloadTask.completed_at >= start_date,
                DownloadTask.completed_at.isnot(None),
            )
        )
        .order_by(DownloadTask.completed_at)
    )
    tasks = result.scalars().all()

    # Group by date
    daily_counts = {}
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        daily_counts[date_str] = 0
        current += datetime.timedelta(days=1)

    for completed_at in tasks:
        if completed_at:
            date_str = completed_at.strftime("%Y-%m-%d")
            if date_str in daily_counts:
                daily_counts[date_str] += 1

    labels = list(daily_counts.keys())
    values = list(daily_counts.values())

    return {
        "labels": labels,
        "values": values,
        "total": sum(values),
        "days": days,
    }


@router.get("/format-breakdown")
async def get_format_breakdown(db: AsyncSession = Depends(get_db)):
    """Get breakdown of downloaded formats."""
    result = await db.execute(
        select(DownloadTask.format, func.count(DownloadTask.id).label("count"))
        .where(DownloadTask.status == TaskStatus.COMPLETED.value)
        .group_by(DownloadTask.format)
        .order_by(func.count(DownloadTask.id).desc())
    )
    rows = result.all()

    formats = []
    total = 0
    for row in rows:
        fmt, count = row
        formats.append({"format": fmt or "unknown", "count": count})
        total += count

    return {
        "data": formats,
        "total": total,
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get recent download activity logs."""
    result = await db.execute(
        select(DownloadLog)
        .order_by(DownloadLog.timestamp.desc())
        .limit(limit)
    )
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
        ]
    }
