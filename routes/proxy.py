"""
Proxy management API routes.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.proxy_manager import proxy_manager

logger = logging.getLogger("iconscout.routes.proxy")

router = APIRouter(prefix="/api/proxy", tags=["proxy"])


class ProxyTestRequest(BaseModel):
    proxy_url: str


@router.get("/pool")
async def get_proxy_pool():
    """Get all proxies in the pool with status."""
    pool = proxy_manager.get_pool_list()
    return {"data": pool, "total": len(pool)}


@router.get("/stats")
async def get_proxy_stats():
    """Get proxy pool statistics."""
    return proxy_manager.get_pool_stats()


@router.post("/refresh")
async def refresh_proxy_pool():
    """Trigger a full proxy pool refresh (fetch + validate)."""
    try:
        result = await proxy_manager.refresh_pool(validate=True)
        return {"message": "Pool berhasil di-refresh", **result}
    except Exception as e:
        logger.error(f"Pool refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal refresh pool: {str(e)}")


@router.post("/test")
async def test_proxy(data: ProxyTestRequest):
    """Test a specific proxy URL."""
    from services.proxy_manager import ProxyInfo

    # Parse proxy URL
    url = data.proxy_url.strip()
    try:
        # Extract host:port from URL like http://1.2.3.4:8080
        if "://" in url:
            parts = url.split("://", 1)[1]
        else:
            parts = url
        host, port_str = parts.split(":")
        port = int(port_str.rstrip("/"))
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Format proxy tidak valid. Gunakan format: http://host:port")

    proxy = ProxyInfo(host=host, port=port)
    is_alive = await proxy_manager.validate_proxy(proxy)

    return {
        "proxy_url": proxy.url,
        "is_alive": is_alive,
        "speed_ms": proxy.speed_ms,
        "message": "Proxy aktif ✅" if is_alive else "Proxy mati ❌",
    }
