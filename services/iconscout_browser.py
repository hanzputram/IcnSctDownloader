"""
IconScout Browser Automation Engine using Playwright.
Handles login, search, and download of assets via browser simulation.
"""
import asyncio
import json
import os
import random
import re
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout

from config import config

logger = logging.getLogger("iconscout.browser")


class IconScoutBrowser:
    """Playwright-based browser automation for IconScout."""

    BASE_URL = "https://iconscout.com"
    LOGIN_URL = "https://iconscout.com/login"
    SEARCH_URL = "https://iconscout.com/search"

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._logged_in = False
        self._cookie_dir = config.DOWNLOAD_DIR.parent / "data" / "cookies"
        self._cookie_dir.mkdir(parents=True, exist_ok=True)

    async def _ensure_browser(self):
        """Start browser if not already running."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=config.HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            logger.info("Browser launched successfully")

    async def _create_context(self, account_id: int = None):
        """Create a new browser context, loading cookies if available."""
        await self._ensure_browser()

        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "accept_downloads": True,
        }

        self._context = await self._browser.new_context(**context_options)

        # Load saved cookies if available
        if account_id:
            cookie_file = self._cookie_dir / f"account_{account_id}.json"
            if cookie_file.exists():
                try:
                    cookies = json.loads(cookie_file.read_text())
                    await self._context.add_cookies(cookies)
                    logger.info(f"Loaded cookies for account {account_id}")
                except Exception as e:
                    logger.warning(f"Failed to load cookies: {e}")

        self._page = await self._context.new_page()

        # Stealth: mask webdriver detection
        await self._page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

    async def _save_cookies(self, account_id: int):
        """Save cookies for session persistence."""
        if self._context and account_id:
            cookies = await self._context.cookies()
            cookie_file = self._cookie_dir / f"account_{account_id}.json"
            cookie_file.write_text(json.dumps(cookies, indent=2))
            logger.info(f"Saved cookies for account {account_id}")

    async def login(self, email: str, password: str, account_id: int = None) -> Dict[str, Any]:
        """
        Login to IconScout with email and password.
        Returns dict with success status and message.
        """
        try:
            await self._create_context(account_id)

            # First check if already logged in via cookies
            await self._page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await asyncio.sleep(2)

            # Check if already logged in
            if await self._is_logged_in():
                self._logged_in = True
                if account_id:
                    await self._save_cookies(account_id)
                logger.info(f"Already logged in via cookies for {email}")
                return {"success": True, "message": "Login berhasil (via cookies)"}

            # Navigate to login page
            logger.info(f"Attempting login for {email}")
            await self._page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await asyncio.sleep(2)

            # Fill in login form
            # Try different selectors for email input
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                '#email',
                'input[data-testid="email"]',
            ]

            email_filled = False
            for selector in email_selectors:
                try:
                    elem = await self._page.wait_for_selector(selector, timeout=3000)
                    if elem:
                        await elem.fill(email)
                        email_filled = True
                        logger.info(f"Email filled using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not email_filled:
                return {"success": False, "message": "Tidak bisa menemukan field email di halaman login"}

            # Fill password
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                '#password',
            ]

            password_filled = False
            for selector in password_selectors:
                try:
                    elem = await self._page.wait_for_selector(selector, timeout=3000)
                    if elem:
                        await elem.fill(password)
                        password_filled = True
                        logger.info(f"Password filled using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not password_filled:
                return {"success": False, "message": "Tidak bisa menemukan field password di halaman login"}

            # Click login button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
            ]

            submitted = False
            for selector in submit_selectors:
                try:
                    btn = await self._page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        await btn.click()
                        submitted = True
                        logger.info(f"Login submitted using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not submitted:
                # Try pressing Enter as fallback
                await self._page.keyboard.press("Enter")

            # Wait for navigation
            await asyncio.sleep(5)

            # Check if login succeeded
            if await self._is_logged_in():
                self._logged_in = True
                if account_id:
                    await self._save_cookies(account_id)
                logger.info(f"Login successful for {email}")
                return {"success": True, "message": "Login berhasil!"}
            else:
                # Check for error messages
                error_text = await self._get_error_message()
                msg = error_text if error_text else "Login gagal. Periksa email dan password Anda."
                logger.warning(f"Login failed for {email}: {msg}")
                return {"success": False, "message": msg}

        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}")
            return {"success": False, "message": f"Error saat login: {str(e)}"}

    async def _is_logged_in(self) -> bool:
        """Check if the user is currently logged in."""
        try:
            # Check for common logged-in indicators
            indicators = [
                'a[href*="/profile"]',
                'a[href*="/account"]',
                'a[href*="/dashboard"]',
                '.user-avatar',
                '[data-testid="user-menu"]',
                'img[alt*="avatar" i]',
                'button[aria-label*="account" i]',
            ]
            for selector in indicators:
                try:
                    elem = await self._page.wait_for_selector(selector, timeout=2000)
                    if elem:
                        return True
                except PlaywrightTimeout:
                    continue

            # Also check if login page is NOT present
            current_url = self._page.url
            if "/login" not in current_url and "/signup" not in current_url:
                # Check for cookie presence
                cookies = await self._context.cookies()
                auth_cookies = [c for c in cookies if "token" in c["name"].lower() or "session" in c["name"].lower() or "auth" in c["name"].lower()]
                if auth_cookies:
                    return True

            return False
        except Exception:
            return False

    async def _get_error_message(self) -> Optional[str]:
        """Try to extract error message from the page."""
        try:
            error_selectors = [
                '.error-message',
                '.alert-danger',
                '[role="alert"]',
                '.text-danger',
                '.error',
            ]
            for selector in error_selectors:
                try:
                    elem = await self._page.wait_for_selector(selector, timeout=1000)
                    if elem:
                        return await elem.text_content()
                except PlaywrightTimeout:
                    continue
        except Exception:
            pass
        return None

    async def search_assets(
        self,
        keyword: str,
        asset_type: str = "icon",
        page: int = 1,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search IconScout for assets by keyword.
        Returns list of asset info dicts.
        """
        if not self._page:
            raise RuntimeError("Browser not initialized. Call login() first.")

        results = []
        try:
            # Build search URL
            search_url = f"{self.BASE_URL}/search/{keyword}?type={asset_type}&page={page}"
            logger.info(f"Searching: {search_url}")

            await self._page.goto(search_url, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await asyncio.sleep(3)

            # Wait for results to load
            await self._page.wait_for_selector(
                '.search-results, .asset-grid, .item-card, [class*="card"], [class*="asset"]',
                timeout=10000
            )

            # Extract asset links
            asset_elements = await self._page.query_selector_all(
                'a[href*="/icon/"], a[href*="/illustration/"], a[href*="/3d/"], a[href*="/lottie-animation/"]'
            )

            seen_urls = set()
            for elem in asset_elements[:max_results]:
                try:
                    href = await elem.get_attribute("href")
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # Get asset name from text or alt
                    name = ""
                    img = await elem.query_selector("img")
                    if img:
                        name = await img.get_attribute("alt") or ""

                    if not name:
                        name = await elem.text_content() or ""
                        name = name.strip()[:100]

                    # Determine asset type from URL
                    detected_type = "icon"
                    if "/illustration/" in href:
                        detected_type = "illustration"
                    elif "/3d/" in href:
                        detected_type = "3d"
                    elif "/lottie-animation/" in href:
                        detected_type = "lottie"

                    full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

                    results.append({
                        "url": full_url,
                        "name": name or f"Asset from {keyword}",
                        "type": detected_type,
                    })
                except Exception as e:
                    logger.debug(f"Error extracting asset: {e}")
                    continue

            logger.info(f"Found {len(results)} assets for '{keyword}'")

        except PlaywrightTimeout:
            logger.warning(f"Timeout searching for '{keyword}'")
        except Exception as e:
            logger.error(f"Search error: {e}")

        return results

    async def download_asset(
        self,
        asset_url: str,
        format: str = "png",
        save_dir: str = None,
    ) -> Dict[str, Any]:
        """
        Download a single asset from its IconScout page URL.
        Returns dict with file_path, file_size, and status info.
        """
        if not self._page:
            raise RuntimeError("Browser not initialized. Call login() first.")

        save_path = Path(save_dir) if save_dir else config.DOWNLOAD_DIR
        save_path.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading asset: {asset_url} (format: {format})")

            # Navigate to asset page
            await self._page.goto(asset_url, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await asyncio.sleep(2)

            # Extract asset name from page
            asset_name = "unknown_asset"
            try:
                title_elem = await self._page.query_selector("h1")
                if title_elem:
                    asset_name = await title_elem.text_content()
                    asset_name = re.sub(r'[^\w\s-]', '', asset_name).strip()
                    asset_name = re.sub(r'\s+', '_', asset_name)[:80]
            except Exception:
                pass

            if not asset_name or asset_name == "unknown_asset":
                # Try to extract from URL
                parts = asset_url.rstrip("/").split("/")
                asset_name = parts[-1] if parts else "asset"

            # Try to find and click the download button
            download_button_selectors = [
                f'button:has-text("{format.upper()}")',
                'button:has-text("Download")',
                'a:has-text("Download")',
                '[class*="download"]',
                'button[class*="download"]',
                '.download-btn',
                '#download-btn',
            ]

            # First try to find format selector if it exists
            format_selectors = [
                f'[data-format="{format}"]',
                f'button:has-text("{format.upper()}")',
                f'a:has-text("{format.upper()}")',
                f'label:has-text("{format.upper()}")',
            ]

            for selector in format_selectors:
                try:
                    fmt_btn = await self._page.wait_for_selector(selector, timeout=2000)
                    if fmt_btn:
                        await fmt_btn.click()
                        await asyncio.sleep(1)
                        logger.info(f"Selected format: {format}")
                        break
                except PlaywrightTimeout:
                    continue

            # Click download button and wait for download
            downloaded_file = None

            for selector in download_button_selectors:
                try:
                    btn = await self._page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        # Set up download listener
                        async with self._page.expect_download(timeout=30000) as download_info:
                            await btn.click()

                        download = await download_info.value

                        # Determine filename
                        suggested_name = download.suggested_filename
                        if suggested_name:
                            ext = Path(suggested_name).suffix
                            filename = f"{asset_name}{ext}"
                        else:
                            filename = f"{asset_name}.{format}"

                        # Save file
                        file_path = save_path / filename

                        # Handle duplicate names
                        counter = 1
                        original_path = file_path
                        while file_path.exists():
                            stem = original_path.stem
                            suffix = original_path.suffix
                            file_path = save_path / f"{stem}_{counter}{suffix}"
                            counter += 1

                        await download.save_as(str(file_path))
                        file_size = file_path.stat().st_size

                        logger.info(f"Downloaded: {filename} ({file_size} bytes)")

                        downloaded_file = {
                            "success": True,
                            "file_path": str(file_path),
                            "file_name": filename,
                            "file_size": file_size,
                            "asset_name": asset_name,
                            "format": format,
                            "message": f"Download berhasil: {filename}",
                        }
                        break
                except PlaywrightTimeout:
                    continue
                except Exception as e:
                    logger.debug(f"Download attempt failed with selector {selector}: {e}")
                    continue

            if downloaded_file:
                return downloaded_file

            # Fallback: Try to download image directly
            try:
                img_selectors = [
                    '.asset-preview img',
                    '.item-preview img',
                    'img[class*="preview"]',
                    'img[class*="asset"]',
                    '.detail-page img',
                    'main img[src*="iconscout"]',
                ]

                for img_selector in img_selectors:
                    img = await self._page.query_selector(img_selector)
                    if img:
                        src = await img.get_attribute("src")
                        if src and src.startswith("http"):
                            # Download via HTTP
                            import httpx
                            async with httpx.AsyncClient() as client:
                                resp = await client.get(src, follow_redirects=True, timeout=30.0)
                                if resp.status_code == 200:
                                    content_type = resp.headers.get("content-type", "")
                                    ext = ".png"
                                    if "svg" in content_type:
                                        ext = ".svg"
                                    elif "json" in content_type:
                                        ext = ".json"

                                    filename = f"{asset_name}{ext}"
                                    file_path = save_path / filename
                                    file_path.write_bytes(resp.content)
                                    file_size = file_path.stat().st_size

                                    return {
                                        "success": True,
                                        "file_path": str(file_path),
                                        "file_name": filename,
                                        "file_size": file_size,
                                        "asset_name": asset_name,
                                        "format": ext.lstrip("."),
                                        "message": f"Download berhasil (direct): {filename}",
                                    }
            except Exception as e:
                logger.debug(f"Direct download fallback failed: {e}")

            return {
                "success": False,
                "message": "Tidak bisa menemukan tombol download. Coba format lain atau periksa URL.",
            }

        except Exception as e:
            logger.error(f"Download error for {asset_url}: {e}")
            return {
                "success": False,
                "message": f"Error saat download: {str(e)}",
            }

    async def close(self):
        """Close browser and cleanup."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._logged_in = False


# Global browser instance manager
class BrowserManager:
    """Manages browser instances per account for concurrent downloads."""

    def __init__(self):
        self._browsers: Dict[int, IconScoutBrowser] = {}
        self._lock = asyncio.Lock()

    async def get_browser(self, account_id: int) -> IconScoutBrowser:
        """Get or create a browser instance for an account."""
        async with self._lock:
            if account_id not in self._browsers:
                self._browsers[account_id] = IconScoutBrowser()
            return self._browsers[account_id]

    async def close_browser(self, account_id: int):
        """Close browser for a specific account."""
        async with self._lock:
            if account_id in self._browsers:
                await self._browsers[account_id].close()
                del self._browsers[account_id]

    async def close_all(self):
        """Close all browser instances."""
        async with self._lock:
            for browser in self._browsers.values():
                await browser.close()
            self._browsers.clear()
            logger.info("All browsers closed")


browser_manager = BrowserManager()
