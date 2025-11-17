#!/usr/bin/env python3
"""
Main entry point for Gemini Web API Wrapper.

Usage:
    python main.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Gemini Web API Wrapper")
    print("=" * 60)
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Headless: {settings.headless}")
    print(f"Profile: {settings.profile_path}")
    print("=" * 60)
    print()
    print("API will be available at:")
    print(f"  http://localhost:{settings.port}")
    print(f"  http://localhost:{settings.port}/docs (Swagger UI)")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )
