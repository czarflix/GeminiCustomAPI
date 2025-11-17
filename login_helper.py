#!/usr/bin/env python3
"""
Login helper for Gemini Web API Wrapper.

Run this script once to authenticate with your Google account.
The session will be saved in the browser profile for use by the API service.
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


async def login_helper():
    """Open browser for manual login to Gemini."""
    print("=" * 60)
    print("Gemini Web API - Login Helper")
    print("=" * 60)
    print()
    print("This will open a browser window where you can:")
    print("  1. Log in to your Google account")
    print("  2. Complete 2FA if required")
    print("  3. Access Gemini and verify it works")
    print()
    print(f"Your session will be saved to: {settings.profile_path}")
    print()
    print("Press Ctrl+C in this terminal to exit when you're done logging in.")
    print("=" * 60)
    print()

    # Ensure profile directory exists
    settings.profile_path.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        print("Launching browser...")
        print()

        # Launch browser in headful mode with persistent context
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(settings.profile_path),
            headless=False,  # Always visible for login
            viewport={"width": 1920, "height": 1080},
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        # Create a new page
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to Gemini
        print(f"Navigating to {settings.gemini_url}")
        print()
        await page.goto(settings.gemini_url)

        print("Browser opened! Please complete the following steps:")
        print()
        print("  1. Log in with your Google account if prompted")
        print("  2. Complete any 2FA verification")
        print("  3. Make sure you can see the Gemini chat interface")
        print("  4. Optionally, send a test message to verify it works")
        print()
        print("When done, close the browser or press Ctrl+C here.")
        print("=" * 60)
        print()

        try:
            # Wait indefinitely until user closes browser or presses Ctrl+C
            while True:
                await asyncio.sleep(1)
                # Check if browser is still open
                if not page or page.is_closed():
                    break
        except KeyboardInterrupt:
            print("\n\nLogin helper interrupted by user.")

        print()
        print("=" * 60)
        print("Login process complete!")
        print()
        print(f"Session saved to: {settings.profile_path}")
        print()
        print("You can now start the API service with:")
        print("  python main.py")
        print()
        print("Or with uvicorn:")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("=" * 60)

        # Close browser if still open
        if not page.is_closed():
            await context.close()


if __name__ == "__main__":
    try:
        asyncio.run(login_helper())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
