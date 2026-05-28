"""
Account management routes.
"""
import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database import get_db
from models import Account, AccountStatus, DownloadLog, LogLevel

logger = logging.getLogger("iconscout.routes.accounts")

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


# --- Pydantic Schemas ---

class AccountCreate(BaseModel):
    email: str
    password: str
    plan_type: str = "unlimited"
    proxy_url: Optional[str] = None
    auto_proxy: bool = True  # Auto-assign proxy by default


class AccountUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    plan_type: Optional[str] = None
    status: Optional[str] = None
    proxy_url: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    email: str
    status: str
    plan_type: str
    downloads_count: int
    proxy_url: Optional[str] = None
    last_used: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# --- Routes ---

@router.get("")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """List all accounts."""
    result = await db.execute(select(Account).order_by(Account.created_at.desc()))
    accounts = result.scalars().all()

    return {
        "data": [
            {
                "id": acc.id,
                "email": acc.email,
                "status": acc.status,
                "plan_type": acc.plan_type,
                "downloads_count": acc.downloads_count,
                "proxy_url": acc.proxy_url,
                "last_used": acc.last_used.isoformat() if acc.last_used else None,
                "created_at": acc.created_at.isoformat() if acc.created_at else None,
            }
            for acc in accounts
        ],
        "total": len(accounts),
    }


@router.post("")
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db)):
    """Add a new IconScout account with optional auto-proxy assignment."""
    # Check if email already exists
    existing = await db.execute(select(Account).where(Account.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    # Encrypt password
    fernet = config.get_fernet()
    encrypted_pw = fernet.encrypt(data.password.encode()).decode()

    # Determine proxy
    proxy_url = data.proxy_url if data.proxy_url else None

    # Auto-assign proxy if requested and no manual proxy provided
    if data.auto_proxy and not proxy_url:
        try:
            from services.proxy_manager import proxy_manager
            # We need to flush the account first to get its ID, so we'll assign proxy after
            proxy_url = None  # Will be assigned after account creation
        except Exception as e:
            logger.warning(f"Proxy manager not available: {e}")

    account = Account(
        email=data.email,
        encrypted_password=encrypted_pw,
        plan_type=data.plan_type,
        status=AccountStatus.ACTIVE.value,
        proxy_url=proxy_url,
    )
    db.add(account)
    await db.flush()

    # Auto-assign proxy AFTER we have the account ID
    assigned_proxy = None
    if data.auto_proxy and not data.proxy_url:
        try:
            from services.proxy_manager import proxy_manager
            assigned_proxy = await proxy_manager.auto_assign_proxy(account.id)
            if assigned_proxy:
                account.proxy_url = assigned_proxy
                logger.info(f"Auto-assigned proxy {assigned_proxy} to account #{account.id}")
        except Exception as e:
            logger.warning(f"Auto-proxy assignment failed: {e}")

    # Log
    proxy_msg = f" (Proxy: {assigned_proxy})" if assigned_proxy else ""
    log = DownloadLog(
        account_id=account.id,
        level=LogLevel.INFO.value,
        message=f"Account added: {data.email}{proxy_msg}",
    )
    db.add(log)

    return {
        "id": account.id,
        "email": account.email,
        "status": account.status,
        "proxy_url": account.proxy_url,
        "message": f"Account berhasil ditambahkan{proxy_msg}",
    }


@router.put("/{account_id}")
async def update_account(account_id: int, data: AccountUpdate, db: AsyncSession = Depends(get_db)):
    """Update an account."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account tidak ditemukan")

    if data.email is not None:
        account.email = data.email
    if data.password is not None:
        fernet = config.get_fernet()
        account.encrypted_password = fernet.encrypt(data.password.encode()).decode()
    if data.plan_type is not None:
        account.plan_type = data.plan_type
    if data.status is not None:
        account.status = data.status
    if data.proxy_url is not None:
        account.proxy_url = data.proxy_url if data.proxy_url else None

    account.updated_at = datetime.datetime.utcnow()

    return {"message": "Account berhasil diupdate", "id": account_id}


@router.delete("/{account_id}")
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an account and release its proxy."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account tidak ditemukan")

    # Release proxy from pool
    try:
        from services.proxy_manager import proxy_manager
        await proxy_manager.release_proxy(account_id)
    except Exception as e:
        logger.debug(f"Could not release proxy: {e}")

    await db.delete(account)

    return {"message": "Account berhasil dihapus", "id": account_id}


@router.post("/{account_id}/test")
async def test_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Test login for an account."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account tidak ditemukan")

    # Decrypt password
    fernet = config.get_fernet()
    password = fernet.decrypt(account.encrypted_password.encode()).decode()

    # Test login
    from services.iconscout_browser import browser_manager

    browser = await browser_manager.get_browser(account.id, proxy_url=account.proxy_url)
    login_result = await browser.login(account.email, password, account.id)

    # Update account status based on result
    if login_result["success"]:
        account.status = AccountStatus.ACTIVE.value
        account.last_used = datetime.datetime.utcnow()

        log = DownloadLog(
            account_id=account.id,
            level=LogLevel.SUCCESS.value,
            message=f"Login test berhasil: {account.email}",
        )
    else:
        account.status = AccountStatus.ERROR.value

        log = DownloadLog(
            account_id=account.id,
            level=LogLevel.ERROR.value,
            message=f"Login test gagal: {account.email} - {login_result['message']}",
        )

    db.add(log)

    # Close browser after test
    await browser_manager.close_browser(account.id)

    return login_result


@router.post("/{account_id}/refresh-proxy")
async def refresh_proxy(account_id: int, db: AsyncSession = Depends(get_db)):
    """Rotate/refresh proxy for an account."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account tidak ditemukan")

    try:
        from services.proxy_manager import proxy_manager
        new_proxy = await proxy_manager.rotate_proxy(account_id)

        if new_proxy:
            account.proxy_url = new_proxy
            account.updated_at = datetime.datetime.utcnow()

            log = DownloadLog(
                account_id=account.id,
                level=LogLevel.INFO.value,
                message=f"Proxy di-rotate: {new_proxy}",
            )
            db.add(log)

            return {
                "success": True,
                "proxy_url": new_proxy,
                "message": f"Proxy berhasil di-refresh: {new_proxy}",
            }
        else:
            return {
                "success": False,
                "message": "Tidak ada proxy tersedia saat ini. Coba refresh pool terlebih dahulu.",
            }
    except Exception as e:
        logger.error(f"Proxy refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal refresh proxy: {str(e)}")
