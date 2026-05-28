"""
Scheduler service using APScheduler.
Manages cron-based download schedules.
"""
import asyncio
import logging
import random
from datetime import datetime
from typing import Optional, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database import async_session
from models import ScheduleJob, DownloadTask, DownloadLog, Account, TaskStatus, SourceType, LogLevel

logger = logging.getLogger("iconscout.scheduler")


class SchedulerService:
    """Manages scheduled download jobs."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._running_jobs: Dict[int, bool] = {}

    async def start(self):
        """Start the scheduler and load existing jobs from DB."""
        self.scheduler.start()
        logger.info("Scheduler started")

        # Load existing active schedules
        async with async_session() as session:
            result = await session.execute(
                select(ScheduleJob).where(ScheduleJob.is_active == True)
            )
            jobs = result.scalars().all()

            for job in jobs:
                self._add_job_to_scheduler(job)
                logger.info(f"Loaded schedule: {job.name} (ID: {job.id})")

    def _add_job_to_scheduler(self, job: ScheduleJob):
        """Add a schedule job to APScheduler."""
        try:
            cron_parts = job.cron_expression.split()
            if len(cron_parts) != 5:
                logger.error(f"Invalid cron expression for job {job.id}: {job.cron_expression}")
                return

            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4],
            )

            self.scheduler.add_job(
                self._execute_job,
                trigger=trigger,
                id=f"schedule_{job.id}",
                args=[job.id],
                replace_existing=True,
                name=job.name,
            )

        except Exception as e:
            logger.error(f"Failed to add job {job.id} to scheduler: {e}")

    async def _execute_job(self, schedule_id: int):
        """Execute a scheduled download job."""
        if self._running_jobs.get(schedule_id, False):
            logger.warning(f"Job {schedule_id} is already running, skipping")
            return

        self._running_jobs[schedule_id] = True

        try:
            async with async_session() as session:
                # Get schedule details
                result = await session.execute(
                    select(ScheduleJob).where(ScheduleJob.id == schedule_id)
                )
                job = result.scalar_one_or_none()

                if not job or not job.is_active:
                    logger.info(f"Job {schedule_id} is inactive, skipping")
                    return

                # Log job start
                log = DownloadLog(
                    level=LogLevel.INFO.value,
                    message=f"Scheduled job '{job.name}' started",
                    account_id=job.account_id,
                )
                session.add(log)

                # Get account for login
                account = None
                if job.account_id:
                    acc_result = await session.execute(
                        select(Account).where(Account.id == job.account_id)
                    )
                    account = acc_result.scalar_one_or_none()

                if not account:
                    # Use first active account
                    acc_result = await session.execute(
                        select(Account).where(Account.status == "active").limit(1)
                    )
                    account = acc_result.scalar_one_or_none()

                if not account:
                    log = DownloadLog(
                        level=LogLevel.ERROR.value,
                        message=f"No active account found for job '{job.name}'",
                    )
                    session.add(log)
                    await session.commit()
                    return

                # Import here to avoid circular imports
                from services.iconscout_browser import browser_manager

                browser = await browser_manager.get_browser(account.id, proxy_url=account.proxy_url)

                # Decrypt password
                fernet = config.get_fernet()
                password = fernet.decrypt(account.encrypted_password.encode()).decode()

                # Login
                login_result = await browser.login(account.email, password, account.id)
                if not login_result["success"]:
                    log = DownloadLog(
                        level=LogLevel.ERROR.value,
                        message=f"Login failed for job '{job.name}': {login_result['message']}",
                        account_id=account.id,
                    )
                    session.add(log)
                    await session.commit()
                    return

                downloaded_count = 0

                if job.source_type == SourceType.KEYWORD.value:
                    # Search and download
                    assets = await browser.search_assets(
                        keyword=job.source_value,
                        asset_type=job.asset_type,
                        max_results=job.max_items,
                    )

                    for asset in assets:
                        if downloaded_count >= job.max_items:
                            break

                        # Create task record
                        task = DownloadTask(
                            account_id=account.id,
                            source_type=SourceType.KEYWORD.value,
                            source_value=asset["url"],
                            asset_name=asset["name"],
                            asset_type=asset["type"],
                            format=job.format,
                            status=TaskStatus.RUNNING.value,
                            schedule_id=schedule_id,
                        )
                        session.add(task)
                        await session.flush()

                        # Download
                        result = await browser.download_asset(
                            asset_url=asset["url"],
                            format=job.format,
                        )

                        if result.get("success"):
                            task.status = TaskStatus.COMPLETED.value
                            task.file_path = result.get("file_path")
                            task.file_size = result.get("file_size")
                            task.completed_at = datetime.utcnow()
                            downloaded_count += 1

                            log = DownloadLog(
                                task_id=task.id,
                                account_id=account.id,
                                level=LogLevel.SUCCESS.value,
                                message=f"Downloaded: {asset['name']}",
                            )
                            session.add(log)
                        else:
                            task.status = TaskStatus.FAILED.value
                            task.error_message = result.get("message", "Unknown error")

                            log = DownloadLog(
                                task_id=task.id,
                                account_id=account.id,
                                level=LogLevel.ERROR.value,
                                message=f"Failed: {asset['name']} - {result.get('message')}",
                            )
                            session.add(log)

                        # Random delay between downloads
                        delay = random.uniform(config.DOWNLOAD_DELAY_MIN, config.DOWNLOAD_DELAY_MAX)
                        await asyncio.sleep(delay)

                elif job.source_type == SourceType.LINK.value:
                    # Download from link list
                    links = [l.strip() for l in job.source_value.split("\n") if l.strip()]

                    for link in links[:job.max_items]:
                        if downloaded_count >= job.max_items:
                            break

                        task = DownloadTask(
                            account_id=account.id,
                            source_type=SourceType.LINK.value,
                            source_value=link,
                            format=job.format,
                            status=TaskStatus.RUNNING.value,
                            schedule_id=schedule_id,
                        )
                        session.add(task)
                        await session.flush()

                        result = await browser.download_asset(
                            asset_url=link,
                            format=job.format,
                        )

                        if result.get("success"):
                            task.status = TaskStatus.COMPLETED.value
                            task.file_path = result.get("file_path")
                            task.file_size = result.get("file_size")
                            task.asset_name = result.get("asset_name")
                            task.completed_at = datetime.utcnow()
                            downloaded_count += 1

                            log = DownloadLog(
                                task_id=task.id,
                                account_id=account.id,
                                level=LogLevel.SUCCESS.value,
                                message=f"Downloaded: {result.get('asset_name', link)}",
                            )
                            session.add(log)
                        else:
                            task.status = TaskStatus.FAILED.value
                            task.error_message = result.get("message")

                            log = DownloadLog(
                                task_id=task.id,
                                account_id=account.id,
                                level=LogLevel.ERROR.value,
                                message=f"Failed: {link} - {result.get('message')}",
                            )
                            session.add(log)

                        delay = random.uniform(config.DOWNLOAD_DELAY_MIN, config.DOWNLOAD_DELAY_MAX)
                        await asyncio.sleep(delay)

                # Update schedule stats
                job.last_run = datetime.utcnow()
                job.total_downloaded += downloaded_count

                # Update account download count
                account.downloads_count += downloaded_count
                account.last_used = datetime.utcnow()

                # Final log
                log = DownloadLog(
                    level=LogLevel.INFO.value,
                    message=f"Job '{job.name}' completed: {downloaded_count} items downloaded",
                    account_id=account.id,
                )
                session.add(log)

                await session.commit()
                logger.info(f"Job {schedule_id} completed: {downloaded_count} items")

        except Exception as e:
            logger.error(f"Job {schedule_id} failed: {e}")
            try:
                async with async_session() as session:
                    log = DownloadLog(
                        level=LogLevel.ERROR.value,
                        message=f"Job {schedule_id} error: {str(e)}",
                    )
                    session.add(log)
                    await session.commit()
            except Exception:
                pass
        finally:
            self._running_jobs[schedule_id] = False

    async def add_schedule(self, schedule: ScheduleJob):
        """Add a new schedule to the scheduler."""
        self._add_job_to_scheduler(schedule)
        logger.info(f"Added schedule: {schedule.name} (ID: {schedule.id})")

    async def remove_schedule(self, schedule_id: int):
        """Remove a schedule from the scheduler."""
        job_id = f"schedule_{schedule_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule: {schedule_id}")
        except Exception as e:
            logger.warning(f"Could not remove job {job_id}: {e}")

    async def toggle_schedule(self, schedule_id: int, active: bool):
        """Enable or disable a schedule."""
        if active:
            async with async_session() as session:
                result = await session.execute(
                    select(ScheduleJob).where(ScheduleJob.id == schedule_id)
                )
                job = result.scalar_one_or_none()
                if job:
                    self._add_job_to_scheduler(job)
        else:
            await self.remove_schedule(schedule_id)

    def get_next_run(self, schedule_id: int) -> Optional[datetime]:
        """Get next scheduled run time."""
        job_id = f"schedule_{schedule_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None

    async def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


# Global scheduler instance
scheduler_service = SchedulerService()
