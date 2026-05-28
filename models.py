"""
SQLAlchemy ORM models for IconScout Bot.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from database import Base


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    BANNED = "banned"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, enum.Enum):
    LINK = "link"
    KEYWORD = "keyword"


class LogLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    encrypted_password = Column(Text, nullable=False)
    cookie_data = Column(Text, nullable=True)
    status = Column(String(20), default=AccountStatus.ACTIVE.value)
    proxy_url = Column(String(255), nullable=True)
    plan_type = Column(String(50), default="unlimited")
    downloads_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tasks = relationship("DownloadTask", back_populates="account", cascade="all, delete-orphan")
    schedules = relationship("ScheduleJob", back_populates="account", cascade="all, delete-orphan")


class DownloadTask(Base):
    __tablename__ = "download_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    source_type = Column(String(20), default=SourceType.LINK.value)
    source_value = Column(Text, nullable=False)  # URL or keyword
    asset_name = Column(String(500), nullable=True)
    asset_type = Column(String(50), nullable=True)  # icon, illustration, 3d, lottie
    format = Column(String(20), default="png")
    status = Column(String(20), default=TaskStatus.PENDING.value)
    file_path = Column(Text, nullable=True)
    file_size = Column(Float, nullable=True)  # in bytes
    cloud_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    schedule_id = Column(Integer, ForeignKey("schedule_jobs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    account = relationship("Account", back_populates="tasks")
    schedule = relationship("ScheduleJob", back_populates="tasks")
    logs = relationship("DownloadLog", back_populates="task", cascade="all, delete-orphan")


class ScheduleJob(Base):
    __tablename__ = "schedule_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(20), default=SourceType.KEYWORD.value)
    source_value = Column(Text, nullable=False)  # keyword or comma-separated links
    asset_type = Column(String(50), default="icon")
    format = Column(String(20), default="png")
    max_items = Column(Integer, default=10)  # max items to download per run
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    cron_expression = Column(String(100), nullable=False)  # e.g. "0 */6 * * *"
    is_active = Column(Boolean, default=True)
    total_downloaded = Column(Integer, default=0)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account = relationship("Account", back_populates="schedules")
    tasks = relationship("DownloadTask", back_populates="schedule")


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("download_tasks.id"), nullable=True)
    account_id = Column(Integer, nullable=True)
    level = Column(String(20), default=LogLevel.INFO.value)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("DownloadTask", back_populates="logs")
