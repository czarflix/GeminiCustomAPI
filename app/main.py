"""FastAPI application for Gemini Web API Wrapper."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app.browser_manager import browser_manager
from app.config import settings
from app.models import AskRequest, AskResponse, ErrorResponse, ResponseMeta
from app.gemini_automation import (
    ask_gemini,
    SessionExpiredError,
    QuotaExceededError,
    UnexpectedUIStateError,
    AutomationTimeoutError,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting Gemini Web API Wrapper...")
    try:
        await browser_manager.start()
        logger.info("Browser manager started successfully")

        # Verify Gemini session
        page = await browser_manager.get_page()
        from app.gemini_automation import ensure_gemini_ready

        try:
            await ensure_gemini_ready(page)
            logger.info("Gemini session verified - ready to accept requests")
        except SessionExpiredError:
            logger.error(
                "Gemini session expired! Please run 'python login_helper.py' to authenticate."
            )
        except Exception as e:
            logger.warning(f"Could not verify Gemini session: {e}")

    except Exception as e:
        logger.error(f"Failed to start browser manager: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    await browser_manager.stop()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Gemini Web API Wrapper",
    description="Local-only API wrapper for Gemini web UI using Playwright automation",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "service": "Gemini Web API Wrapper",
        "version": "1.0.0",
        "status": "running" if browser_manager.is_running else "browser_not_ready",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    is_healthy = browser_manager.is_running

    return {
        "healthy": is_healthy,
        "browser_running": browser_manager.is_running,
        "timestamp": time.time(),
    }


@app.post(
    "/ask",
    response_model=AskResponse,
    responses={
        200: {"model": AskResponse},
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def ask_endpoint(request: AskRequest):
    """
    Send a prompt to Gemini and get a response.

    Args:
        request: AskRequest with prompt, model, and options

    Returns:
        AskResponse with Gemini's response

    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()

    # Validate model
    valid_models = ["gemini-2.5-pro", "gemini-2.5-flash"]
    if request.model not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model. Must be one of: {valid_models}",
        )

    # Check if browser is running
    if not browser_manager.is_running:
        logger.error("Browser not running - attempting to restart")
        try:
            await browser_manager.start()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Browser service unavailable: {str(e)}",
            )

    # Acquire lock for single-threaded execution
    await browser_manager.acquire_lock()

    try:
        page = await browser_manager.get_page()

        # Call the automation
        response_text, model_used, fallback_triggered = await ask_gemini(
            page=page,
            prompt=request.prompt,
            model=request.model,
            fallback_to_flash=request.fallback_to_flash,
            files=request.files,
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Build response
        return AskResponse(
            model_requested=request.model,
            model_used=model_used,
            fallback_triggered=fallback_triggered,
            response_text=response_text,
            raw_response_html=None,  # Optionally include raw HTML
            meta=ResponseMeta(latency_ms=latency_ms),
        )

    except SessionExpiredError as e:
        logger.error(f"Session expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "gemini_session_expired",
                "details": str(e),
            },
        )

    except QuotaExceededError as e:
        logger.warning(f"Quota exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "pro_quota_exceeded",
                "details": str(e),
            },
        )

    except UnexpectedUIStateError as e:
        logger.error(f"Unexpected UI state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "unexpected_ui_state",
                "details": str(e),
            },
        )

    except AutomationTimeoutError as e:
        logger.error(f"Automation timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "automation_timeout",
                "details": str(e),
            },
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        # Attempt to restart browser on unexpected errors
        try:
            await browser_manager.restart()
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "details": str(e),
            },
        )

    finally:
        # Always release lock
        browser_manager.release_lock()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
