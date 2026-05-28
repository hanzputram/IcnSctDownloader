"""
IconScout API v3 Client (Optional).
Used when API credentials are available as an alternative to browser automation.
"""
import logging
from typing import Optional, List, Dict, Any

import httpx

from config import config

logger = logging.getLogger("iconscout.api")


class IconScoutAPI:
    """REST client for IconScout API v3."""

    BASE_URL = "https://api.iconscout.com/v3"

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or config.ICONSCOUT_API_CLIENT_ID
        self.client_secret = client_secret or config.ICONSCOUT_API_CLIENT_SECRET
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Client-ID": self.client_id,
                    "Client-Secret": self.client_secret,
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def search(
        self,
        query: str,
        asset_type: str = "icon",
        page: int = 1,
        per_page: int = 20,
        price: str = "free",
    ) -> Dict[str, Any]:
        """
        Search for assets.
        asset_type: icon, illustration, 3d, lottie
        """
        if not self.is_configured:
            return {"error": "API not configured", "data": []}

        try:
            client = await self._get_client()
            params = {
                "query": query,
                "asset": asset_type,
                "page": page,
                "per_page": per_page,
                "price": price,
            }

            response = await client.get("/search", params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("response", {}).get("items", {}).get("data", [])

            results = []
            for item in items:
                results.append({
                    "uuid": item.get("uuid"),
                    "name": item.get("name", "Unknown"),
                    "slug": item.get("slug", ""),
                    "type": asset_type,
                    "url": f"https://iconscout.com/{asset_type}/{item.get('slug', '')}",
                    "preview_url": item.get("urls", {}).get("png_128", ""),
                })

            return {
                "total": data.get("response", {}).get("items", {}).get("total", 0),
                "data": results,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"API error: {e.response.status_code}", "data": []}
        except Exception as e:
            logger.error(f"API search error: {e}")
            return {"error": str(e), "data": []}

    async def download(self, item_uuid: str, format: str = "png") -> Dict[str, Any]:
        """
        Download an asset by UUID.
        Returns download URL or binary content info.
        """
        if not self.is_configured:
            return {"error": "API not configured"}

        try:
            client = await self._get_client()
            response = await client.post(
                f"/items/{item_uuid}/api-download",
                json={"format": format},
            )
            response.raise_for_status()
            data = response.json()

            download_url = data.get("response", {}).get("download", {}).get("url", "")

            return {
                "success": True,
                "download_url": download_url,
                "uuid": item_uuid,
                "format": format,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"API download error: {e.response.status_code}")
            return {"success": False, "error": f"Download failed: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"API download error: {e}")
            return {"success": False, "error": str(e)}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Global API instance
iconscout_api = IconScoutAPI()
