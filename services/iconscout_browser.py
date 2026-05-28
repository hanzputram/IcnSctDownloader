"""
IconScout Browser Automation Engine using Playwright.
Handles login, search, and download of assets via browser simulation.
Enhanced with multi-layer anti-detection stealth system.
"""
import asyncio
import json
import math
import os
import random
import re
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_async

from config import config

logger = logging.getLogger("iconscout.browser")


# ─── Anti-Ban: Fingerprint Pools ─────────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
    {"width": 2560, "height": 1440},
    {"width": 1680, "height": 1050},
]

TIMEZONES = [
    "Asia/Jakarta",
    "Asia/Singapore",
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "Asia/Tokyo",
    "Asia/Seoul",
    "Australia/Sydney",
    "Asia/Kolkata",
]

LOCALES = [
    "en-US", "en-GB", "id-ID", "de-DE", "fr-FR",
    "ja-JP", "ko-KR", "pt-BR", "es-ES", "zh-CN",
]

PLATFORMS = ["Win32", "MacIntel", "Linux x86_64"]

SCREEN_RESOLUTIONS = [
    (1920, 1080), (1536, 864), (1440, 900), (1366, 768),
    (1280, 720), (2560, 1440), (1680, 1050), (1600, 900),
]

WEBGL_VENDORS = ["Google Inc. (NVIDIA)", "Google Inc. (AMD)", "Google Inc. (Intel)", "Google Inc."]
WEBGL_RENDERERS = [
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)",
]


def _generate_fingerprint() -> Dict[str, Any]:
    """Generate a randomized browser fingerprint."""
    ua = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    screen = random.choice(SCREEN_RESOLUTIONS)
    platform = "Win32"
    if "Macintosh" in ua:
        platform = "MacIntel"
    elif "Linux" in ua:
        platform = "Linux x86_64"

    return {
        "user_agent": ua,
        "viewport": viewport,
        "timezone": random.choice(TIMEZONES),
        "locale": random.choice(LOCALES),
        "platform": platform,
        "screen_width": screen[0],
        "screen_height": screen[1],
        "color_depth": random.choice([24, 32]),
        "webgl_vendor": random.choice(WEBGL_VENDORS),
        "webgl_renderer": random.choice(WEBGL_RENDERERS),
        "hardware_concurrency": random.choice([2, 4, 8, 12, 16]),
        "device_memory": random.choice([2, 4, 8, 16]),
    }


# ─── Advanced Stealth JavaScript Injection ────────────────────────────────────

STEALTH_JS_TEMPLATE = """
// Override navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {{
    get: () => undefined,
    configurable: true
}});

// Override navigator.platform
Object.defineProperty(navigator, 'platform', {{
    get: () => '{platform}',
    configurable: true
}});

// Override navigator.hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {{
    get: () => {hardware_concurrency},
    configurable: true
}});

// Override navigator.deviceMemory
Object.defineProperty(navigator, 'deviceMemory', {{
    get: () => {device_memory},
    configurable: true
}});

// Override screen dimensions
Object.defineProperty(screen, 'width', {{ get: () => {screen_width} }});
Object.defineProperty(screen, 'height', {{ get: () => {screen_height} }});
Object.defineProperty(screen, 'availWidth', {{ get: () => {screen_width} }});
Object.defineProperty(screen, 'availHeight', {{ get: () => {screen_height} - 40 }});
Object.defineProperty(screen, 'colorDepth', {{ get: () => {color_depth} }});

// Override navigator.plugins (add realistic plugins)
Object.defineProperty(navigator, 'plugins', {{
    get: () => {{
        const plugins = [
            {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
            {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
            {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }},
        ];
        plugins.length = 3;
        return plugins;
    }},
    configurable: true
}});

// Spoof navigator.languages
Object.defineProperty(navigator, 'languages', {{
    get: () => ['{locale}', '{locale}'.split('-')[0]],
    configurable: true
}});

// Spoof chrome runtime
if (!window.chrome) {{
    window.chrome = {{
        runtime: {{ id: undefined }},
        loadTimes: function() {{}},
        csi: function() {{}},
        app: {{ isInstalled: false }},
    }};
}}

// Canvas fingerprint noise injection
const origToBlob = HTMLCanvasElement.prototype.toBlob;
const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;

HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {{
    const ctx = this.getContext('2d');
    if (ctx) {{
        const imageData = origGetImageData.call(ctx, 0, 0, this.width, this.height);
        for (let i = 0; i < imageData.data.length; i += 4) {{
            imageData.data[i] ^= (Math.random() * 2) | 0;
        }}
        ctx.putImageData(imageData, 0, 0);
    }}
    return origToBlob.call(this, callback, type, quality);
}};

HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
    const ctx = this.getContext('2d');
    if (ctx) {{
        try {{
            const imageData = origGetImageData.call(ctx, 0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] ^= (Math.random() * 2) | 0;
            }}
            ctx.putImageData(imageData, 0, 0);
        }} catch(e) {{}}
    }}
    return origToDataURL.call(this, type, quality);
}};

// WebGL vendor/renderer spoof
const origGetParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {{
    if (parameter === 37445) return '{webgl_vendor}';
    if (parameter === 37446) return '{webgl_renderer}';
    return origGetParameter.call(this, parameter);
}};

try {{
    const origGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) return '{webgl_vendor}';
        if (parameter === 37446) return '{webgl_renderer}';
        return origGetParameter2.call(this, parameter);
    }};
}} catch(e) {{}}

// Override Permissions API
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({{ state: Notification.permission }}) :
        originalQuery(parameters)
);

// Connection spoofing
Object.defineProperty(navigator, 'connection', {{
    get: () => ({{
        effectiveType: '4g',
        rtt: {rtt},
        downlink: {downlink},
        saveData: false,
    }}),
    configurable: true
}});
"""


class IconScoutBrowser:
    """Playwright-based browser automation for IconScout with advanced anti-detection."""

    BASE_URL = "https://iconscout.com"
    LOGIN_URL = "https://iconscout.com/login"
    SEARCH_URL = "https://iconscout.com/search"

    def __init__(self, proxy_url: Optional[str] = None):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._logged_in = False
        self._proxy_url = proxy_url
        self._fingerprint: Dict[str, Any] = {}
        self._cookie_dir = config.DOWNLOAD_DIR.parent / "data" / "cookies"
        self._cookie_dir.mkdir(parents=True, exist_ok=True)
        self._download_count_today = 0
        self._last_download_time = 0.0

    # ─── Human-Like Behavior Methods ──────────────────────────────────────

    async def _human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Wait a random human-like interval."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _human_mouse_move(self, page: Page, x: int, y: int, steps: int = 0):
        """Move mouse along a bezier curve to target position for realism."""
        if not steps:
            steps = random.randint(8, 20)

        # Get current mouse position (approximate from viewport center)
        current_x = random.randint(100, 400)
        current_y = random.randint(100, 400)

        # Control points for bezier curve
        cp1x = current_x + random.randint(-50, 50)
        cp1y = current_y + random.randint(-50, 50)
        cp2x = x + random.randint(-30, 30)
        cp2y = y + random.randint(-30, 30)

        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier interpolation
            bx = (1 - t) ** 3 * current_x + 3 * (1 - t) ** 2 * t * cp1x + 3 * (1 - t) * t ** 2 * cp2x + t ** 3 * x
            by = (1 - t) ** 3 * current_y + 3 * (1 - t) ** 2 * t * cp1y + 3 * (1 - t) * t ** 2 * cp2y + t ** 3 * y

            await page.mouse.move(bx, by)
            await asyncio.sleep(random.uniform(0.005, 0.025))

    async def _human_scroll(self, page: Page):
        """Simulate realistic scrolling behavior."""
        scroll_amount = random.randint(100, 500)
        direction = random.choice([1, 1, 1, -1])  # bias toward scrolling down
        steps = random.randint(3, 8)

        for _ in range(steps):
            delta = scroll_amount * direction + random.randint(-30, 30)
            await page.mouse.wheel(0, delta)
            await asyncio.sleep(random.uniform(0.1, 0.4))

    async def _simulate_reading(self, page: Page):
        """Simulate a user reading a page: scroll slowly, pause, hover."""
        # Small random scroll
        await page.mouse.wheel(0, random.randint(50, 200))
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Move mouse to a random position (reading)
        vp = self._fingerprint.get("viewport", {"width": 1920, "height": 1080})
        rand_x = random.randint(100, vp["width"] - 200)
        rand_y = random.randint(100, vp["height"] - 200)
        await self._human_mouse_move(page, rand_x, rand_y)
        await asyncio.sleep(random.uniform(0.3, 1.0))

    async def _random_idle(self, page: Page):
        """Random idle period simulating a human pausing."""
        idle_time = random.uniform(2.0, 6.0)
        # Occasionally move mouse slightly during idle
        if random.random() < 0.4:
            vp = self._fingerprint.get("viewport", {"width": 1920, "height": 1080})
            await self._human_mouse_move(
                page,
                random.randint(200, vp["width"] - 200),
                random.randint(200, vp["height"] - 200),
            )
        await asyncio.sleep(idle_time)

    # ─── Browser Lifecycle ────────────────────────────────────────────────

    async def _ensure_browser(self):
        """Start browser if not already running."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()

            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1920,1080",
            ]

            self._browser = await self._playwright.chromium.launch(
                headless=config.HEADLESS,
                args=launch_args,
            )
            logger.info("Browser launched (stealth mode)")

    async def _create_context(self, account_id: int = None):
        """Create a new browser context with randomized fingerprint."""
        await self._ensure_browser()

        # Generate unique fingerprint for this session
        self._fingerprint = _generate_fingerprint()
        fp = self._fingerprint

        context_options = {
            "viewport": fp["viewport"],
            "user_agent": fp["user_agent"],
            "locale": fp["locale"],
            "timezone_id": fp["timezone"],
            "accept_downloads": True,
            "color_scheme": random.choice(["light", "dark", "no-preference"]),
            "has_touch": False,
            "is_mobile": False,
            "java_script_enabled": True,
            "ignore_https_errors": True,
        }

        # Apply Proxy if configured for this account
        if self._proxy_url:
            context_options["proxy"] = {"server": self._proxy_url}
            logger.info(f"Using proxy: {self._proxy_url}")

        self._context = await self._browser.new_context(**context_options)

        # Inject advanced stealth scripts BEFORE any navigation
        stealth_js = STEALTH_JS_TEMPLATE.format(
            platform=fp["platform"],
            hardware_concurrency=fp["hardware_concurrency"],
            device_memory=fp["device_memory"],
            screen_width=fp["screen_width"],
            screen_height=fp["screen_height"],
            color_depth=fp["color_depth"],
            locale=fp["locale"],
            webgl_vendor=fp["webgl_vendor"],
            webgl_renderer=fp["webgl_renderer"],
            rtt=random.choice([50, 100, 150]),
            downlink=round(random.uniform(1.5, 10.0), 1),
        )

        await self._context.add_init_script(stealth_js)

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

        # Apply playwright-stealth as an additional layer
        await stealth_async(self._page)

        logger.info(
            f"Context created: UA={fp['user_agent'][:50]}... "
            f"VP={fp['viewport']} TZ={fp['timezone']} Locale={fp['locale']}"
        )

    async def _save_cookies(self, account_id: int):
        """Save cookies for session persistence."""
        if self._context and account_id:
            cookies = await self._context.cookies()
            cookie_file = self._cookie_dir / f"account_{account_id}.json"
            cookie_file.write_text(json.dumps(cookies, indent=2))
            logger.info(f"Saved cookies for account {account_id}")

    # ─── Login ────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str, account_id: int = None) -> Dict[str, Any]:
        """
        Login to IconScout with email and password.
        Returns dict with success status and message.
        """
        try:
            await self._create_context(account_id)

            # First check if already logged in via cookies
            await self._page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await self._human_delay(1.5, 3.0)

            # Simulate reading the homepage
            await self._simulate_reading(self._page)

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
            await self._human_delay(2.0, 4.0)

            # Simulate looking at the login page
            await self._simulate_reading(self._page)

            # Fill in login form
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
                        # Move mouse to element naturally
                        box = await elem.bounding_box()
                        if box:
                            await self._human_mouse_move(
                                self._page,
                                int(box["x"] + box["width"] / 2),
                                int(box["y"] + box["height"] / 2),
                            )
                        await elem.click()
                        await self._human_delay(0.3, 0.8)
                        # Type with human-like variable speed
                        for char in email:
                            await self._page.keyboard.type(char, delay=random.randint(40, 180))
                            if random.random() < 0.05:  # Occasional brief pause
                                await asyncio.sleep(random.uniform(0.2, 0.5))
                        email_filled = True
                        logger.info(f"Email filled using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not email_filled:
                return {"success": False, "message": "Tidak bisa menemukan field email di halaman login"}

            await self._human_delay(0.5, 1.5)

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
                        box = await elem.bounding_box()
                        if box:
                            await self._human_mouse_move(
                                self._page,
                                int(box["x"] + box["width"] / 2),
                                int(box["y"] + box["height"] / 2),
                            )
                        await elem.click()
                        await self._human_delay(0.3, 0.8)
                        for char in password:
                            await self._page.keyboard.type(char, delay=random.randint(50, 170))
                            if random.random() < 0.03:
                                await asyncio.sleep(random.uniform(0.1, 0.4))
                        password_filled = True
                        logger.info(f"Password filled using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not password_filled:
                return {"success": False, "message": "Tidak bisa menemukan field password di halaman login"}

            await self._human_delay(0.8, 2.0)

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
                        box = await btn.bounding_box()
                        if box:
                            await self._human_mouse_move(
                                self._page,
                                int(box["x"] + box["width"] / 2),
                                int(box["y"] + box["height"] / 2),
                            )
                        await self._human_delay(0.3, 1.0)
                        await btn.click(delay=random.randint(50, 150))
                        submitted = True
                        logger.info(f"Login submitted using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not submitted:
                await self._page.keyboard.press("Enter")

            # Wait for navigation with random human delay
            await self._human_delay(4.0, 7.0)

            # Check if login succeeded
            if await self._is_logged_in():
                self._logged_in = True
                if account_id:
                    await self._save_cookies(account_id)
                logger.info(f"Login successful for {email}")
                return {"success": True, "message": "Login berhasil!"}
            else:
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

            current_url = self._page.url
            if "/login" not in current_url and "/signup" not in current_url:
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

    # ─── Search ───────────────────────────────────────────────────────────

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
            search_url = f"{self.BASE_URL}/search/{keyword}?type={asset_type}&page={page}"
            logger.info(f"Searching: {search_url}")

            await self._page.goto(search_url, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await self._human_delay(2.0, 4.0)

            # Simulate browsing behavior
            await self._simulate_reading(self._page)
            await self._human_scroll(self._page)

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

                    name = ""
                    img = await elem.query_selector("img")
                    if img:
                        name = await img.get_attribute("alt") or ""

                    if not name:
                        name = await elem.text_content() or ""
                        name = name.strip()[:100]

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

    # ─── Download ─────────────────────────────────────────────────────────

    async def download_asset(
        self,
        asset_url: str,
        format: str = "png",
        save_dir: str = None,
    ) -> Dict[str, Any]:
        """
        Download a single asset from its IconScout page URL.
        Includes smart rate limiting and human-like behavior.
        """
        if not self._page:
            raise RuntimeError("Browser not initialized. Call login() first.")

        # Smart rate limiting: enforce minimum delay between downloads
        now = time.monotonic()
        elapsed_since_last = now - self._last_download_time
        min_gap = random.uniform(15.0, 45.0)  # 15-45 second cooldown per download
        if elapsed_since_last < min_gap and self._last_download_time > 0:
            wait_time = min_gap - elapsed_since_last
            logger.info(f"Rate limit: waiting {wait_time:.1f}s before next download")
            await asyncio.sleep(wait_time)

        save_path = Path(save_dir) if save_dir else config.DOWNLOAD_DIR
        save_path.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading asset: {asset_url} (format: {format})")

            # Navigate to asset page
            await self._page.goto(asset_url, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
            await self._human_delay(2.0, 4.0)

            # Simulate browsing the asset page naturally
            await self._simulate_reading(self._page)
            await self._random_idle(self._page)
            await self._human_scroll(self._page)

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

            # First try to find format selector
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
                        box = await fmt_btn.bounding_box()
                        if box:
                            await self._human_mouse_move(
                                self._page,
                                int(box["x"] + box["width"] / 2),
                                int(box["y"] + box["height"] / 2),
                            )
                        await self._human_delay(0.3, 0.8)
                        await fmt_btn.click(delay=random.randint(50, 150))
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
                        box = await btn.bounding_box()
                        if box:
                            await self._human_mouse_move(
                                self._page,
                                int(box["x"] + box["width"] / 2),
                                int(box["y"] + box["height"] / 2),
                            )
                        await self._human_delay(0.5, 1.5)

                        async with self._page.expect_download(timeout=30000) as download_info:
                            await btn.click(delay=random.randint(50, 150))

                        download = await download_info.value

                        suggested_name = download.suggested_filename
                        if suggested_name:
                            ext = Path(suggested_name).suffix
                            filename = f"{asset_name}{ext}"
                        else:
                            filename = f"{asset_name}.{format}"

                        file_path = save_path / filename

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

                        self._last_download_time = time.monotonic()
                        self._download_count_today += 1

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

                                    self._last_download_time = time.monotonic()

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

    # ─── Cleanup ──────────────────────────────────────────────────────────

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

    async def get_browser(self, account_id: int, proxy_url: Optional[str] = None) -> IconScoutBrowser:
        """Get or create a browser instance for an account."""
        async with self._lock:
            if account_id not in self._browsers:
                # Auto-fetch proxy from pool if not provided
                if not proxy_url:
                    try:
                        from services.proxy_manager import proxy_manager as pm
                        proxy_url = pm.get_proxy_for_account(account_id)
                    except Exception:
                        pass
                self._browsers[account_id] = IconScoutBrowser(proxy_url=proxy_url)
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
