"""
Proxy Pool Manager for IconScout Bot.
Auto-fetches free proxies from multiple public APIs, validates them,
and assigns them to accounts automatically.
"""
import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx

logger = logging.getLogger("iconscout.proxy")

# Proxy storage file
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROXY_POOL_FILE = DATA_DIR / "proxy_pool.json"


class ProxyInfo:
    """Represents a single proxy with metadata."""

    def __init__(self, host: str, port: int, protocol: str = "http", country: str = "??"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.country = country
        self.speed_ms: Optional[float] = None
        self.is_alive: bool = False
        self.last_checked: Optional[datetime] = None
        self.fail_count: int = 0
        self.assigned_to: Optional[int] = None  # account_id

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "speed_ms": self.speed_ms,
            "is_alive": self.is_alive,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "fail_count": self.fail_count,
            "assigned_to": self.assigned_to,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ProxyInfo":
        proxy = cls(
            host=data["host"],
            port=data["port"],
            protocol=data.get("protocol", "http"),
            country=data.get("country", "??"),
        )
        proxy.speed_ms = data.get("speed_ms")
        proxy.is_alive = data.get("is_alive", False)
        proxy.fail_count = data.get("fail_count", 0)
        proxy.assigned_to = data.get("assigned_to")
        if data.get("last_checked"):
            try:
                proxy.last_checked = datetime.fromisoformat(data["last_checked"])
            except (ValueError, TypeError):
                proxy.last_checked = None
        return proxy


class ProxyPoolManager:
    """
    Manages a pool of free proxies with auto-fetching, validation,
    and assignment capabilities.
    """

    # Free proxy API sources
    PROXY_SOURCES = [
        {
            "name": "ProxyScrape",
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=elite",
            "parser": "_parse_plain_text",
        },
        {
            "name": "ProxyList.Download",
            "url": "https://www.proxy-list.download/api/v1/get?type=https&anon=elite",
            "parser": "_parse_plain_text",
        },
        {
            "name": "GeoNode",
            "url": "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=https",
            "parser": "_parse_geonode",
        },
    ]

    # Validation target — use a lightweight endpoint instead of full IconScout page
    VALIDATION_URL = "https://httpbin.org/ip"
    VALIDATION_TIMEOUT = 15.0  # seconds — generous for free proxies

    def __init__(self):
        self._pool: Dict[str, ProxyInfo] = {}  # key = "host:port"
        self._lock = asyncio.Lock()
        self._last_refresh: Optional[datetime] = None
        self._refresh_interval = timedelta(minutes=30)
        self._load_from_file()

    def _load_from_file(self):
        """Load proxy pool from persistent JSON file."""
        if PROXY_POOL_FILE.exists():
            try:
                data = json.loads(PROXY_POOL_FILE.read_text(encoding="utf-8"))
                for key, proxy_data in data.items():
                    self._pool[key] = ProxyInfo.from_dict(proxy_data)
                logger.info(f"Loaded {len(self._pool)} proxies from cache file")
            except Exception as e:
                logger.warning(f"Failed to load proxy cache: {e}")

    def _save_to_file(self):
        """Persist proxy pool to JSON file."""
        try:
            data = {key: proxy.to_dict() for key, proxy in self._pool.items()}
            PROXY_POOL_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save proxy cache: {e}")

    # --- Proxy Fetching ---

    async def fetch_proxies_from_all_sources(self) -> List[ProxyInfo]:
        """Fetch proxies from all configured sources concurrently."""
        all_proxies = []
        tasks = []
        for source in self.PROXY_SOURCES:
            tasks.append(self._fetch_from_source(source))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Source {self.PROXY_SOURCES[i]['name']} failed: {result}")
            elif isinstance(result, list):
                all_proxies.extend(result)
                logger.info(f"Source {self.PROXY_SOURCES[i]['name']}: got {len(result)} proxies")

        logger.info(f"Total fetched from all sources: {len(all_proxies)} proxies")
        return all_proxies

    async def _fetch_from_source(self, source: Dict) -> List[ProxyInfo]:
        """Fetch proxies from a single source."""
        proxies = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(source["url"], follow_redirects=True)
                resp.raise_for_status()

                parser = getattr(self, source["parser"])
                proxies = parser(resp.text, resp)
        except Exception as e:
            logger.debug(f"Error fetching from {source['name']}: {e}")
            raise
        return proxies

    @staticmethod
    def _parse_plain_text(text: str, resp=None) -> List[ProxyInfo]:
        """Parse IP:PORT plain text list."""
        proxies = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        host = parts[0].strip()
                        port = int(parts[1].strip())
                        if 0 < port < 65536:
                            proxies.append(ProxyInfo(host=host, port=port, protocol="http"))
                    except (ValueError, IndexError):
                        continue
        return proxies

    @staticmethod
    def _parse_geonode(text: str, resp=None) -> List[ProxyInfo]:
        """Parse GeoNode JSON response."""
        proxies = []
        try:
            data = json.loads(text)
            for item in data.get("data", []):
                host = item.get("ip", "")
                port = item.get("port", "")
                protocols = item.get("protocols", ["http"])
                country = item.get("country", "??")
                if host and port:
                    try:
                        protocol = protocols[0] if protocols else "http"
                        proxies.append(ProxyInfo(
                            host=host,
                            port=int(port),
                            protocol=protocol,
                            country=country,
                        ))
                    except (ValueError, IndexError):
                        continue
        except json.JSONDecodeError:
            pass
        return proxies

    # --- Proxy Validation ---

    async def validate_proxy(self, proxy: ProxyInfo) -> bool:
        """Validate a single proxy by testing connection to IconScout."""
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(
                proxies={"http://": proxy.url, "https://": proxy.url},
                timeout=self.VALIDATION_TIMEOUT,
                verify=False,
            ) as client:
                resp = await client.get(
                    self.VALIDATION_URL,
                    follow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"},
                )
                elapsed = (time.monotonic() - start) * 1000  # ms

                if resp.status_code < 400:
                    proxy.is_alive = True
                    proxy.speed_ms = round(elapsed, 1)
                    proxy.fail_count = 0
                    proxy.last_checked = datetime.utcnow()
                    return True
        except Exception:
            pass

        proxy.is_alive = False
        proxy.fail_count += 1
        proxy.last_checked = datetime.utcnow()
        return False

    async def validate_batch(self, proxies: List[ProxyInfo], max_concurrent: int = 20) -> List[ProxyInfo]:
        """Validate a batch of proxies concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        alive = []

        async def _check(p: ProxyInfo):
            async with semaphore:
                if await self.validate_proxy(p):
                    alive.append(p)

        await asyncio.gather(*[_check(p) for p in proxies], return_exceptions=True)
        logger.info(f"Validation complete: {len(alive)}/{len(proxies)} alive")
        return alive

    # --- Pool Management ---

    async def refresh_pool(self, validate: bool = True) -> Dict[str, Any]:
        """Refresh the entire proxy pool: fetch + validate + cache."""
        async with self._lock:
            logger.info("Starting proxy pool refresh...")

            # Fetch from all sources
            raw_proxies = await self.fetch_proxies_from_all_sources()

            if not raw_proxies:
                logger.warning("No proxies fetched from any source")
                return {"fetched": 0, "alive": 0, "total_pool": len(self._pool)}

            # De-duplicate
            unique = {}
            for p in raw_proxies:
                key = f"{p.host}:{p.port}"
                if key not in unique and key not in self._pool:
                    unique[key] = p

            # Validate new proxies
            alive_proxies = []
            if validate and unique:
                alive_proxies = await self.validate_batch(list(unique.values()), max_concurrent=30)
            elif not validate:
                alive_proxies = list(unique.values())
                for p in alive_proxies:
                    p.is_alive = True  # assume alive until checked

            # Add alive proxies to pool
            for p in alive_proxies:
                key = f"{p.host}:{p.port}"
                self._pool[key] = p

            # Remove dead proxies with too many fails
            dead_keys = [k for k, v in self._pool.items() if v.fail_count >= 3 and not v.is_alive]
            for k in dead_keys:
                del self._pool[k]

            self._last_refresh = datetime.utcnow()
            self._save_to_file()

            stats = {
                "fetched": len(raw_proxies),
                "new_unique": len(unique),
                "alive": len(alive_proxies),
                "dead_removed": len(dead_keys),
                "total_pool": len(self._pool),
            }
            logger.info(f"Pool refresh complete: {stats}")
            return stats

    async def get_best_proxy(self, exclude_account_ids: List[int] = None) -> Optional[ProxyInfo]:
        """Get the best available proxy (fastest, not assigned)."""
        async with self._lock:
            available = [
                p for p in self._pool.values()
                if p.is_alive and p.assigned_to is None
            ]

            if exclude_account_ids:
                available = [
                    p for p in available
                    if p.assigned_to not in exclude_account_ids
                ]

            if not available:
                # Try any alive proxy even if assigned
                available = [p for p in self._pool.values() if p.is_alive]

            if not available:
                return None

            # Sort by speed (fastest first), None speeds last
            available.sort(key=lambda p: p.speed_ms if p.speed_ms is not None else 99999)
            return available[0]

    async def auto_assign_proxy(self, account_id: int) -> Optional[str]:
        """
        Auto-assign the best available proxy to an account.
        Returns the proxy URL or None if no proxy available.
        """
        # First try to get from existing pool
        proxy = await self.get_best_proxy()

        if not proxy:
            # Pool empty or all assigned — try refreshing
            logger.info("No available proxy, triggering pool refresh...")
            await self.refresh_pool(validate=True)
            proxy = await self.get_best_proxy()

        if proxy:
            async with self._lock:
                proxy.assigned_to = account_id
                self._save_to_file()
            logger.info(f"Auto-assigned proxy {proxy.url} to account #{account_id}")
            return proxy.url

        logger.warning(f"Could not auto-assign proxy to account #{account_id}: no alive proxies")
        return None

    async def release_proxy(self, account_id: int):
        """Release proxy assignment from an account."""
        async with self._lock:
            for proxy in self._pool.values():
                if proxy.assigned_to == account_id:
                    proxy.assigned_to = None
            self._save_to_file()

    async def rotate_proxy(self, account_id: int) -> Optional[str]:
        """Replace proxy for an account with a new one."""
        await self.release_proxy(account_id)
        return await self.auto_assign_proxy(account_id)

    def get_proxy_for_account(self, account_id: int) -> Optional[str]:
        """Get currently assigned proxy URL for an account (sync)."""
        for proxy in self._pool.values():
            if proxy.assigned_to == account_id:
                return proxy.url
        return None

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about the proxy pool."""
        alive = [p for p in self._pool.values() if p.is_alive]
        dead = [p for p in self._pool.values() if not p.is_alive]
        assigned = [p for p in self._pool.values() if p.assigned_to is not None]

        avg_speed = 0.0
        speeds = [p.speed_ms for p in alive if p.speed_ms is not None]
        if speeds:
            avg_speed = round(sum(speeds) / len(speeds), 1)

        return {
            "total": len(self._pool),
            "alive": len(alive),
            "dead": len(dead),
            "assigned": len(assigned),
            "avg_speed_ms": avg_speed,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
        }

    def get_pool_list(self) -> List[Dict[str, Any]]:
        """Get full proxy pool as list of dicts."""
        return [
            {**proxy.to_dict(), "url": proxy.url}
            for proxy in sorted(
                self._pool.values(),
                key=lambda p: (not p.is_alive, p.speed_ms or 99999),
            )
        ]


# Global singleton
proxy_manager = ProxyPoolManager()
