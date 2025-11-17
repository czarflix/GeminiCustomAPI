"""Core Gemini UI automation logic using Playwright."""

import asyncio
import logging
import re
from typing import Optional, Tuple, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiAutomationError(Exception):
    """Base exception for Gemini automation errors."""
    pass


class SessionExpiredError(GeminiAutomationError):
    """Raised when Gemini session has expired."""
    pass


class QuotaExceededError(GeminiAutomationError):
    """Raised when Pro quota is exceeded."""
    pass


class UnexpectedUIStateError(GeminiAutomationError):
    """Raised when UI is not in expected state."""
    pass


class AutomationTimeoutError(GeminiAutomationError):
    """Raised when automation times out."""
    pass


# DOM Selectors based on the spec
SELECTORS = {
    # Model selection
    "model_pill": '[data-test-id="bard-mode-menu-button"]',
    "desktop_menu": '[data-test-id="desktop-nested-mode-menu"]',
    "mobile_menu": '[data-test-id="mobile-nested-mode-menu"]',
    "model_pro": '[data-test-id="bard-mode-option-2.5pro"]',
    "model_flash": '[data-test-id="bard-mode-option-2.5flash"]',

    # Text input
    "text_editor": 'div.ql-editor.textarea.new-input-ui[aria-label="Enter a prompt here"]',

    # File upload
    "upload_button": 'button[aria-label="Open upload file menu"]',
    "upload_card": '[data-test-id="upload-file-card-container"]',
    "upload_files_button": '[data-test-id="local-images-files-uploader-button"]',
    "hidden_file_selector": '.hidden-local-file-image-selector-button[xapfileselectortrigger]',

    # Send message
    "send_button": 'button[aria-label="Send message"]',

    # Response
    "message_container": 'message-content',
    "response_content": 'model-response-text',
}


# Quota error patterns
QUOTA_ERROR_PATTERNS = [
    r"reached your limit",
    r"usage limit",
    r"Gemini Advanced",
    r"try again later",
    r"upgrade to continue",
    r"temporarily unavailable",
]


def is_quota_error(text: str) -> bool:
    """
    Check if response text indicates Pro quota exceeded.

    Args:
        text: Response text to check

    Returns:
        True if quota error detected
    """
    text_lower = text.lower()
    for pattern in QUOTA_ERROR_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Quota error detected: matched pattern '{pattern}'")
            return True
    return False


async def ensure_gemini_ready(page: Page) -> None:
    """
    Ensure we're on Gemini chat screen and logged in.

    Args:
        page: Playwright page instance

    Raises:
        SessionExpiredError: If not logged in
        UnexpectedUIStateError: If UI is not ready
    """
    logger.info("Ensuring Gemini is ready...")

    # Navigate to Gemini
    try:
        await page.goto(settings.gemini_url, wait_until="networkidle")
    except Exception as e:
        logger.error(f"Failed to navigate to Gemini: {e}")
        raise UnexpectedUIStateError(f"Failed to load Gemini: {e}")

    # Wait a moment for page to settle
    await asyncio.sleep(1)

    # Check if we're on a login page
    current_url = page.url
    if "accounts.google.com" in current_url or "login" in current_url.lower():
        logger.error("Detected login page - session expired")
        raise SessionExpiredError(
            "Detected Google login page at gemini.google.com; please rerun login helper."
        )

    # Check for text editor (main chat interface)
    try:
        await page.wait_for_selector(SELECTORS["text_editor"], timeout=5000, state="visible")
        logger.info("Gemini chat interface ready")
    except PlaywrightTimeout:
        logger.error("Text editor not found - unexpected UI state")
        raise UnexpectedUIStateError(
            "Text editor not found. Gemini UI may have changed or session may be invalid."
        )


async def select_model(page: Page, model: str) -> None:
    """
    Select the specified model (Pro or Flash).

    Args:
        page: Playwright page instance
        model: "gemini-2.5-pro" or "gemini-2.5-flash"

    Raises:
        UnexpectedUIStateError: If model selection fails
    """
    logger.info(f"Selecting model: {model}")

    # Map model name to selector
    model_selector = SELECTORS["model_pro"] if "pro" in model.lower() else SELECTORS["model_flash"]

    try:
        # Click the model pill to open menu
        await page.locator(SELECTORS["model_pill"]).click()
        logger.debug("Clicked model pill")

        # Wait for menu to appear (try both desktop and mobile)
        menu_visible = False
        for menu_selector in [SELECTORS["desktop_menu"], SELECTORS["mobile_menu"]]:
            try:
                await page.wait_for_selector(menu_selector, timeout=2000, state="visible")
                logger.debug(f"Model menu appeared: {menu_selector}")
                menu_visible = True
                break
            except PlaywrightTimeout:
                continue

        if not menu_visible:
            raise UnexpectedUIStateError("Model selection menu did not appear")

        # Click the target model option
        await page.locator(model_selector).click()
        logger.info(f"Selected model: {model}")

        # Wait for menu to close
        await asyncio.sleep(1)

    except PlaywrightTimeout as e:
        logger.error(f"Timeout during model selection: {e}")
        raise UnexpectedUIStateError(f"Failed to select model: {e}")
    except Exception as e:
        logger.error(f"Error during model selection: {e}")
        raise UnexpectedUIStateError(f"Model selection failed: {e}")


async def upload_files(page: Page, file_paths: List[str]) -> None:
    """
    Upload files to Gemini via the upload menu.

    Args:
        page: Playwright page instance
        file_paths: List of local file paths to upload

    Raises:
        UnexpectedUIStateError: If file upload fails
    """
    logger.info(f"Uploading {len(file_paths)} file(s)...")

    try:
        # Click the upload button to open menu
        await page.locator(SELECTORS["upload_button"]).click()
        logger.debug("Clicked upload button")

        # Wait for upload card to appear
        await page.wait_for_selector(SELECTORS["upload_card"], timeout=3000, state="visible")
        logger.debug("Upload menu appeared")

        # Set up file chooser event handler
        async with page.expect_file_chooser() as fc_info:
            # Click "Upload files" button
            await page.locator(SELECTORS["upload_files_button"]).click()
            logger.debug("Clicked 'Upload files' button")

        file_chooser = await fc_info.value
        await file_chooser.set_files(file_paths)
        logger.info(f"Files selected: {file_paths}")

        # Wait for files to upload (look for upload indicators to disappear)
        await asyncio.sleep(2)

    except PlaywrightTimeout as e:
        logger.error(f"Timeout during file upload: {e}")
        raise UnexpectedUIStateError(f"File upload failed: {e}")
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        raise UnexpectedUIStateError(f"File upload error: {e}")


async def send_prompt(page: Page, prompt: str) -> None:
    """
    Type prompt and send message.

    Args:
        page: Playwright page instance
        prompt: The prompt text to send

    Raises:
        UnexpectedUIStateError: If sending fails
    """
    logger.info(f"Sending prompt (length: {len(prompt)})")

    try:
        # Locate the text editor
        editor = page.locator(SELECTORS["text_editor"])

        # Click to focus
        await editor.click()
        logger.debug("Focused text editor")

        # Clear any existing content
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")

        # Type the prompt
        await editor.fill(prompt)
        logger.debug("Prompt typed")

        # Wait a moment for UI to register the text
        await asyncio.sleep(0.5)

        # Click send button
        await page.locator(SELECTORS["send_button"]).click()
        logger.info("Prompt sent")

    except PlaywrightTimeout as e:
        logger.error(f"Timeout while sending prompt: {e}")
        raise UnexpectedUIStateError(f"Failed to send prompt: {e}")
    except Exception as e:
        logger.error(f"Error while sending prompt: {e}")
        raise UnexpectedUIStateError(f"Prompt sending error: {e}")


async def wait_for_response(page: Page, timeout_ms: int = None) -> Tuple[str, str]:
    """
    Wait for and extract Gemini's response.

    Args:
        page: Playwright page instance
        timeout_ms: Timeout in milliseconds (uses config default if not specified)

    Returns:
        Tuple of (response_text, raw_html)

    Raises:
        AutomationTimeoutError: If response takes too long
        UnexpectedUIStateError: If response cannot be extracted
    """
    timeout_ms = timeout_ms or settings.response_timeout
    logger.info(f"Waiting for response (timeout: {timeout_ms}ms)...")

    try:
        # Wait for a response to appear
        # Strategy: Wait for new message-content elements to appear
        # We'll look for model-response-text which contains the actual response

        # Wait a moment for the send to register
        await asyncio.sleep(2)

        # Wait for response content to appear and be complete
        # The response will be in a model-response-text element
        response_selector = SELECTORS["response_content"]

        # Wait for response element to be visible
        await page.wait_for_selector(response_selector, timeout=timeout_ms, state="visible")
        logger.debug("Response element appeared")

        # Wait for streaming to complete (check if still updating)
        # We'll wait a bit and check if content is still changing
        prev_text = ""
        stable_count = 0
        max_wait_iterations = timeout_ms // 1000  # Check every second

        for i in range(max_wait_iterations):
            # Get all response elements (take the last one, which is the latest)
            response_elements = page.locator(response_selector)
            count = await response_elements.count()

            if count == 0:
                await asyncio.sleep(1)
                continue

            # Get the last response
            last_response = response_elements.nth(count - 1)
            current_text = await last_response.inner_text()

            # Check if text has stabilized
            if current_text == prev_text and len(current_text) > 0:
                stable_count += 1
                if stable_count >= 2:  # Stable for 2 seconds
                    logger.info("Response stable and complete")
                    break
            else:
                stable_count = 0

            prev_text = current_text
            await asyncio.sleep(1)

        # Extract final response
        response_elements = page.locator(response_selector)
        count = await response_elements.count()

        if count == 0:
            raise UnexpectedUIStateError("No response received from Gemini")

        last_response = response_elements.nth(count - 1)
        response_text = await last_response.inner_text()
        raw_html = await last_response.inner_html()

        logger.info(f"Response received (length: {len(response_text)})")

        return response_text, raw_html

    except PlaywrightTimeout:
        logger.error("Timeout waiting for response")
        raise AutomationTimeoutError(f"No response received within {timeout_ms}ms")
    except Exception as e:
        logger.error(f"Error extracting response: {e}")
        raise UnexpectedUIStateError(f"Failed to extract response: {e}")


async def ask_gemini(
    page: Page,
    prompt: str,
    model: str = "gemini-2.5-pro",
    fallback_to_flash: bool = True,
    files: Optional[List[str]] = None
) -> Tuple[str, str, bool]:
    """
    High-level function to ask Gemini a question.

    Args:
        page: Playwright page instance
        prompt: The prompt to send
        model: Model to use ("gemini-2.5-pro" or "gemini-2.5-flash")
        fallback_to_flash: Whether to fallback to Flash if Pro quota exceeded
        files: Optional list of file paths to upload

    Returns:
        Tuple of (response_text, model_used, fallback_triggered)

    Raises:
        Various automation errors
    """
    # Ensure Gemini is ready
    await ensure_gemini_ready(page)

    # Select model
    await select_model(page, model)

    # Upload files if provided
    if files:
        await upload_files(page, files)

    # Send prompt
    await send_prompt(page, prompt)

    # Wait for response
    response_text, raw_html = await wait_for_response(page)

    # Check for quota error
    if is_quota_error(response_text):
        logger.warning("Pro quota exceeded detected")

        if model == "gemini-2.5-pro" and fallback_to_flash:
            logger.info("Attempting fallback to Flash...")

            # Switch to Flash
            await select_model(page, "gemini-2.5-flash")

            # Re-send the prompt (without files to simplify)
            await send_prompt(page, prompt)

            # Get new response
            response_text, raw_html = await wait_for_response(page)

            return response_text, "gemini-2.5-flash", True
        else:
            raise QuotaExceededError("Pro quota exceeded and fallback disabled")

    return response_text, model, False
