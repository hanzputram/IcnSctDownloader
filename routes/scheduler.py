"""
Schedule management routes.
"""
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ScheduleJob, Account, DownloadLog, LogLevel, SourceType

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


# --- Schemas ---

class ScheduleCreate(BaseModel):
    name: str
    source_type: str = "keyword"  # keyword or link
    source_value: str  # keyword string or newline-separated links
    asset_type: str = "icon"
    format: str = "png"
    max_items: int = 10
    account_id: Optional[int] = None
    cron_expression: str = "0 */6 * * *"  # every 6 hours


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    source_value: Optional[str] = None
    asset_type: Optional[str] = None
    format: Optional[str] = None
    max_items: Optional[int] = None
    account_id: Optional[int] = None
    cron_expression: Optional[str] = None


# --- Routes ---

@router.get("")
async def list_schedules(db: AsyncSession = Depends(get_db)):
    """List all schedules."""
    result = await db.execute(select(ScheduleJob).order_by(ScheduleJob.created_at.desc()))
    schedules = result.scalars().all()

    from services.scheduler import scheduler_service

    data = []
    for s in schedules:
        next_run = scheduler_service.get_next_run(s.id)
        data.append({
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "source_value": s.source_value,
            "asset_type": s.asset_type,
            "format": s.format,
            "max_items": s.max_items,
            "account_id": s.account_id,
            "cron_expression": s.cron_expression,
            "is_active": s.is_active,
            "total_downloaded": s.total_downloaded,
            "last_run": s.last_run.isoformat() if s.last_run else None,
            "next_run": next_run.isoformat() if next_run else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {"data": data, "total": len(data)}


@router.post("")
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new schedule."""
    # Validate cron expression
    parts = data.cron_expression.split()
    if len(parts) != 5:
        raise HTTPException(status_code=400, detail="Cron expression harus 5 bagian: menit jam hari bulan hari_minggu")

    schedule = ScheduleJob(
        name=data.name,
        source_type=data.source_type,
        source_value=data.source_value,
        asset_type=data.asset_type,
        format=data.format,
        max_items=data.max_items,
        account_id=data.account_id,
        cron_expression=data.cron_expression,
        is_active=True,
    )
    db.add(schedule)
    await db.flush()

    # Add to scheduler
    from services.scheduler import scheduler_service
    await scheduler_service.add_schedule(schedule)

    log = DownloadLog(
        account_id=data.account_id,
        level=LogLevel.INFO.value,
        message=f"Schedule created: {data.name} ({data.cron_expression})",
    )
    db.add(log)

    return {
        "id": schedule.id,
        "name": schedule.name,
        "message": "Schedule berhasil dibuat",
    }


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: int, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    """Update a schedule."""
    result = await db.execute(select(ScheduleJob).where(ScheduleJob.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule tidak ditemukan")

    if data.name is not None:
        schedule.name = data.name
    if data.source_value is not None:
        schedule.source_value = data.source_value
    if data.asset_type is not None:
        schedule.asset_type = data.asset_type
    if data.format is not None:
        schedule.format = data.format
    if data.max_items is not None:
        schedule.max_items = data.max_items
    if data.account_id is not None:
        schedule.account_id = data.account_id
    if data.cron_expression is not None:
        parts = data.cron_expression.split()
        if len(parts) != 5:
            raise HTTPException(status_code=400, detail="Invalid cron expression")
        schedule.cron_expression = data.cron_expression

    schedule.updated_at = datetime.datetime.utcnow()

    # Re-register with scheduler if active
    if schedule.is_active:
        from services.scheduler import scheduler_service
        await scheduler_service.remove_schedule(schedule_id)
        await scheduler_service.add_schedule(schedule)

    return {"message": "Schedule berhasil diupdate", "id": schedule_id}


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a schedule."""
    result = await db.execute(select(ScheduleJob).where(ScheduleJob.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule tidak ditemukan")

    from services.scheduler import scheduler_service
    await scheduler_service.remove_schedule(schedule_id)

    await db.delete(schedule)

    return {"message": "Schedule berhasil dihapus", "id": schedule_id}


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Enable or disable a schedule."""
    result = await db.execute(select(ScheduleJob).where(ScheduleJob.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule tidak ditemukan")

    schedule.is_active = not schedule.is_active
    schedule.updated_at = datetime.datetime.utcnow()

    from services.scheduler import scheduler_service
    await scheduler_service.toggle_schedule(schedule_id, schedule.is_active)

    status = "aktif" if schedule.is_active else "nonaktif"

    log = DownloadLog(
        account_id=schedule.account_id,
        level=LogLevel.INFO.value,
        message=f"Schedule '{schedule.name}' set to {status}",
    )
    db.add(log)

    return {
        "id": schedule_id,
        "is_active": schedule.is_active,
        "message": f"Schedule sekarang {status}",
    }


@router.post("/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Manually trigger a schedule to run immediately."""
    result = await db.execute(select(ScheduleJob).where(ScheduleJob.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule tidak ditemukan")

    from services.scheduler import scheduler_service
    import asyncio
    asyncio.create_task(scheduler_service._execute_job(schedule_id))

    log = DownloadLog(
        account_id=schedule.account_id,
        level=LogLevel.INFO.value,
        message=f"Schedule '{schedule.name}' triggered manually",
    )
    db.add(log)

    return {"message": f"Schedule '{schedule.name}' dijalankan sekarang", "id": schedule_id}
