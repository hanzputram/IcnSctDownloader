"""
Download task routes.
"""
import asyncio
import random
import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database import get_db, async_session
from models import Account, DownloadTask, DownloadLog, TaskStatus, SourceType, LogLevel, AccountStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# --- Schemas ---

class SingleDownloadRequest(BaseModel):
    url: str
    format: str = "png"
    account_id: Optional[int] = None


class BulkDownloadRequest(BaseModel):
    urls: List[str]
    format: str = "png"
    account_id: Optional[int] = None


class SearchDownloadRequest(BaseModel):
    keyword: str
    asset_type: str = "icon"
    format: str = "png"
    max_items: int = 10
    account_id: Optional[int] = None


# --- Background download worker ---

async def _run_download(task_id: int, url: str, format: str, account_id: int):
    """Background worker for downloading a single asset."""
    from services.iconscout_browser import browser_manager

    async with async_session() as db:
        try:
            # Get account
            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()
            if not account:
                await db.execute(
                    update(DownloadTask).where(DownloadTask.id == task_id).values(
                        status=TaskStatus.FAILED.value,
                        error_message="Account tidak ditemukan",
                    )
                )
                await db.commit()
                return

            fernet = config.get_fernet()
            password = fernet.decrypt(account.encrypted_password.encode()).decode()

            browser = await browser_manager.get_browser(account_id)

            # Login if needed
            login_result = await browser.login(account.email, password, account_id)
            if not login_result["success"]:
                await db.execute(
                    update(DownloadTask).where(DownloadTask.id == task_id).values(
                        status=TaskStatus.FAILED.value,
                        error_message=f"Login gagal: {login_result['message']}",
                    )
                )
                log = DownloadLog(
                    task_id=task_id,
                    account_id=account_id,
                    level=LogLevel.ERROR.value,
                    message=f"Login failed: {login_result['message']}",
                )
                db.add(log)
                await db.commit()
                return

            # Update task to running
            await db.execute(
                update(DownloadTask).where(DownloadTask.id == task_id).values(
                    status=TaskStatus.RUNNING.value,
                )
            )
            await db.commit()

            # Download
            dl_result = await browser.download_asset(asset_url=url, format=format)

            if dl_result.get("success"):
                await db.execute(
                    update(DownloadTask).where(DownloadTask.id == task_id).values(
                        status=TaskStatus.COMPLETED.value,
                        file_path=dl_result.get("file_path"),
                        file_size=dl_result.get("file_size"),
                        asset_name=dl_result.get("asset_name"),
                        completed_at=datetime.datetime.utcnow(),
                    )
                )

                # Update account stats
                account.downloads_count += 1
                account.last_used = datetime.datetime.utcnow()

                log = DownloadLog(
                    task_id=task_id,
                    account_id=account_id,
                    level=LogLevel.SUCCESS.value,
                    message=f"Downloaded: {dl_result.get('asset_name', url)}",
                    details=f"File: {dl_result.get('file_path')}, Size: {dl_result.get('file_size')} bytes",
                )
                db.add(log)

                # Upload to cloud if enabled
                if config.GOOGLE_DRIVE_ENABLED:
                    from services.cloud_upload import cloud_service
                    upload_result = await cloud_service.upload_file(
                        file_path=dl_result["file_path"],
                        folder_name="IconScout",
                    )
                    if upload_result.get("success"):
                        await db.execute(
                            update(DownloadTask).where(DownloadTask.id == task_id).values(
                                cloud_url=upload_result.get("web_link"),
                            )
                        )
                        log = DownloadLog(
                            task_id=task_id,
                            account_id=account_id,
                            level=LogLevel.SUCCESS.value,
                            message=f"Uploaded to Drive: {dl_result.get('asset_name')}",
                        )
                        db.add(log)
            else:
                await db.execute(
                    update(DownloadTask).where(DownloadTask.id == task_id).values(
                        status=TaskStatus.FAILED.value,
                        error_message=dl_result.get("message", "Download failed"),
                    )
                )
                log = DownloadLog(
                    task_id=task_id,
                    account_id=account_id,
                    level=LogLevel.ERROR.value,
                    message=f"Download failed: {dl_result.get('message')}",
                )
                db.add(log)

            await db.commit()

        except Exception as e:
            try:
                await db.execute(
                    update(DownloadTask).where(DownloadTask.id == task_id).values(
                        status=TaskStatus.FAILED.value,
                        error_message=str(e),
                    )
                )
                log = DownloadLog(
                    task_id=task_id,
                    account_id=account_id,
                    level=LogLevel.ERROR.value,
                    message=f"Error: {str(e)}",
                )
                db.add(log)
                await db.commit()
            except Exception:
                pass


async def _run_bulk_download(task_ids: List[int], urls: List[str], format: str, account_id: int):
    """Background worker for bulk downloads with delays."""
    for i, (task_id, url) in enumerate(zip(task_ids, urls)):
        await _run_download(task_id, url, format, account_id)

        # Random delay between downloads
        if i < len(urls) - 1:
            delay = random.uniform(config.DOWNLOAD_DELAY_MIN, config.DOWNLOAD_DELAY_MAX)
            await asyncio.sleep(delay)


async def _run_search_download(keyword: str, asset_type: str, format: str, max_items: int, account_id: int):
    """Background worker for search + download."""
    from services.iconscout_browser import browser_manager

    async with async_session() as db:
        try:
            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()
            if not account:
                return

            fernet = config.get_fernet()
            password = fernet.decrypt(account.encrypted_password.encode()).decode()

            browser = await browser_manager.get_browser(account_id)
            login_result = await browser.login(account.email, password, account_id)

            if not login_result["success"]:
                log = DownloadLog(
                    account_id=account_id,
                    level=LogLevel.ERROR.value,
                    message=f"Search download: Login failed - {login_result['message']}",
                )
                db.add(log)
                await db.commit()
                return

            # Search
            assets = await browser.search_assets(
                keyword=keyword,
                asset_type=asset_type,
                max_results=max_items,
            )

            log = DownloadLog(
                account_id=account_id,
                level=LogLevel.INFO.value,
                message=f"Search '{keyword}': Found {len(assets)} assets",
            )
            db.add(log)
            await db.commit()

            # Download each
            for i, asset in enumerate(assets[:max_items]):
                task = DownloadTask(
                    account_id=account_id,
                    source_type=SourceType.KEYWORD.value,
                    source_value=asset["url"],
                    asset_name=asset["name"],
                    asset_type=asset["type"],
                    format=format,
                    status=TaskStatus.RUNNING.value,
                )
                db.add(task)
                await db.flush()

                dl_result = await browser.download_asset(
                    asset_url=asset["url"],
                    format=format,
                )

                if dl_result.get("success"):
                    task.status = TaskStatus.COMPLETED.value
                    task.file_path = dl_result.get("file_path")
                    task.file_size = dl_result.get("file_size")
                    task.completed_at = datetime.datetime.utcnow()

                    account.downloads_count += 1
                    account.last_used = datetime.datetime.utcnow()

                    log = DownloadLog(
                        task_id=task.id,
                        account_id=account_id,
                        level=LogLevel.SUCCESS.value,
                        message=f"Downloaded: {asset['name']}",
                    )
                    db.add(log)

                    # Cloud upload
                    if config.GOOGLE_DRIVE_ENABLED:
                        from services.cloud_upload import cloud_service
                        upload_result = await cloud_service.upload_file(
                            file_path=dl_result["file_path"],
                            folder_name="IconScout",
                        )
                        if upload_result.get("success"):
                            task.cloud_url = upload_result.get("web_link")
                else:
                    task.status = TaskStatus.FAILED.value
                    task.error_message = dl_result.get("message")

                    log = DownloadLog(
                        task_id=task.id,
                        account_id=account_id,
                        level=LogLevel.ERROR.value,
                        message=f"Failed: {asset['name']} - {dl_result.get('message')}",
                    )
                    db.add(log)

                await db.commit()

                if i < len(assets) - 1:
                    delay = random.uniform(config.DOWNLOAD_DELAY_MIN, config.DOWNLOAD_DELAY_MAX)
                    await asyncio.sleep(delay)

        except Exception as e:
            try:
                log = DownloadLog(
                    account_id=account_id,
                    level=LogLevel.ERROR.value,
                    message=f"Search download error: {str(e)}",
                )
                db.add(log)
                await db.commit()
            except Exception:
                pass


# --- Helper ---

async def _get_active_account(db: AsyncSession, account_id: Optional[int] = None) -> Account:
    """Get a specific or first active account."""
    if account_id:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Account tidak ditemukan")
        return account

    result = await db.execute(
        select(Account).where(Account.status == AccountStatus.ACTIVE.value).limit(1)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="Tidak ada account aktif. Tambahkan account terlebih dahulu.")
    return account


# --- Routes ---

@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List download tasks with optional status filter."""
    query = select(DownloadTask).order_by(DownloadTask.created_at.desc())

    if status:
        query = query.where(DownloadTask.status == status)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Get total count
    count_query = select(func.count(DownloadTask.id))
    if status:
        count_query = count_query.where(DownloadTask.status == status)
    total = (await db.execute(count_query)).scalar()

    return {
        "data": [
            {
                "id": t.id,
                "account_id": t.account_id,
                "source_type": t.source_type,
                "source_value": t.source_value,
                "asset_name": t.asset_name,
                "asset_type": t.asset_type,
                "format": t.format,
                "status": t.status,
                "file_path": t.file_path,
                "file_size": t.file_size,
                "cloud_url": t.cloud_url,
                "error_message": t.error_message,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ],
        "total": total,
    }


@router.post("/download")
async def single_download(
    data: SingleDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start downloading a single asset from a URL."""
    account = await _get_active_account(db, data.account_id)

    task = DownloadTask(
        account_id=account.id,
        source_type=SourceType.LINK.value,
        source_value=data.url,
        format=data.format,
        status=TaskStatus.PENDING.value,
    )
    db.add(task)
    await db.flush()

    log = DownloadLog(
        task_id=task.id,
        account_id=account.id,
        level=LogLevel.INFO.value,
        message=f"Task created: {data.url}",
    )
    db.add(log)

    background_tasks.add_task(_run_download, task.id, data.url, data.format, account.id)

    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Download task dimulai",
    }


@router.post("/bulk-download")
async def bulk_download(
    data: BulkDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start downloading multiple assets from URLs."""
    account = await _get_active_account(db, data.account_id)

    task_ids = []
    for url in data.urls:
        task = DownloadTask(
            account_id=account.id,
            source_type=SourceType.LINK.value,
            source_value=url.strip(),
            format=data.format,
            status=TaskStatus.PENDING.value,
        )
        db.add(task)
        await db.flush()
        task_ids.append(task.id)

    log = DownloadLog(
        account_id=account.id,
        level=LogLevel.INFO.value,
        message=f"Bulk download started: {len(data.urls)} items",
    )
    db.add(log)

    background_tasks.add_task(_run_bulk_download, task_ids, data.urls, data.format, account.id)

    return {
        "task_ids": task_ids,
        "total": len(data.urls),
        "message": f"Bulk download dimulai: {len(data.urls)} items",
    }


@router.post("/search-download")
async def search_download(
    data: SearchDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Search by keyword and download results."""
    account = await _get_active_account(db, data.account_id)

    log = DownloadLog(
        account_id=account.id,
        level=LogLevel.INFO.value,
        message=f"Search download: '{data.keyword}' (type: {data.asset_type}, max: {data.max_items})",
    )
    db.add(log)

    background_tasks.add_task(
        _run_search_download,
        data.keyword,
        data.asset_type,
        data.format,
        data.max_items,
        account.id,
    )

    return {
        "keyword": data.keyword,
        "asset_type": data.asset_type,
        "max_items": data.max_items,
        "message": f"Search download dimulai: '{data.keyword}'",
    }


@router.get("/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get task details."""
    result = await db.execute(select(DownloadTask).where(DownloadTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan")

    return {
        "id": task.id,
        "account_id": task.account_id,
        "source_type": task.source_type,
        "source_value": task.source_value,
        "asset_name": task.asset_name,
        "asset_type": task.asset_type,
        "format": task.format,
        "status": task.status,
        "file_path": task.file_path,
        "file_size": task.file_size,
        "cloud_url": task.cloud_url,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.delete("/{task_id}")
async def cancel_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a pending task."""
    result = await db.execute(select(DownloadTask).where(DownloadTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan")

    if task.status in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
        task.status = TaskStatus.CANCELLED.value
        return {"message": "Task dibatalkan", "id": task_id}

    return {"message": f"Task sudah {task.status}, tidak bisa dibatalkan", "id": task_id}
