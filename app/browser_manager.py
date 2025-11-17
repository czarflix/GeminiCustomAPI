"""Playwright browser lifecycle management with persistent profile."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from app.config import settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser instance with persistent profile."""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """
        Start Playwright and launch browser with persistent context.

        Raises:
            Exception: If browser fails to start
        """
        logger.info("Starting Playwright browser manager...")

        # Ensure profile directory exists
        profile_path = settings.profile_path
        profile_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using browser profile: {profile_path}")

        # Start Playwright
        self.playwright = await async_playwright().start()

        # Launch browser with persistent context
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=settings.headless,
            viewport={"width": 1920, "height": 1080},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
            # Set timeouts
            slow_mo=50,  # Slow down by 50ms to be more human-like
        )

        # Create a new page
        self.page = await self.context.new_page()

        # Set default timeouts
        self.page.set_default_timeout(settings.selector_timeout)
        self.page.set_default_navigation_timeout(settings.page_load_timeout)

        logger.info("Browser started successfully")

    async def stop(self) -> None:
        """Stop Playwright and close browser."""
        logger.info("Stopping browser manager...")

        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("Browser stopped")

    async def restart(self) -> None:
        """Restart the browser (useful for recovery from crashes)."""
        logger.warning("Restarting browser...")
        await self.stop()
        await asyncio.sleep(2)
        await self.start()

    async def get_page(self) -> Page:
        """
        Get the current page, ensuring browser is running.

        Returns:
            Page: The Playwright page instance

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page or self.page.is_closed():
            raise RuntimeError("Browser not started or page closed")
        return self.page

    async def acquire_lock(self):
        """Acquire the automation lock (for single-threaded execution)."""
        await self._lock.acquire()

    def release_lock(self):
        """Release the automation lock."""
        if self._lock.locked():
            self._lock.release()

    @property
    def is_running(self) -> bool:
        """Check if browser is running."""
        return (
            self.playwright is not None
            and self.context is not None
            and self.page is not None
            and not self.page.is_closed()
        )


# Global browser manager instance
browser_manager = BrowserManager()
