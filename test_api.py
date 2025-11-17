#!/usr/bin/env python3
"""
Simple test script for the Gemini Web API.

Make sure the API service is running before executing this script.
"""

import requests
import json
import sys


def test_api(base_url: str = "http://localhost:8000"):
    """Test the /ask endpoint with a simple prompt."""

    print("=" * 60)
    print("Testing Gemini Web API")
    print("=" * 60)
    print()

    # Check health
    print("1. Checking API health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        health = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Healthy: {health.get('healthy')}")
        print(f"   Browser Running: {health.get('browser_running')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
        print("Make sure the API service is running:")
        print("  python main.py")
        print()
        sys.exit(1)

    # Test with Flash (faster)
    print("2. Testing with Gemini 2.5 Flash...")
    test_prompt = "Write a short haiku about artificial intelligence."

    try:
        response = requests.post(
            f"{base_url}/ask",
            json={
                "prompt": test_prompt,
                "model": "gemini-2.5-flash",
                "fallback_to_flash": True,
            },
            timeout=60,
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   Model Requested: {result['model_requested']}")
            print(f"   Model Used: {result['model_used']}")
            print(f"   Fallback Triggered: {result['fallback_triggered']}")
            print(f"   Latency: {result['meta']['latency_ms']}ms")
            print()
            print("   Response:")
            print("   " + "-" * 56)
            for line in result['response_text'].split('\n'):
                print(f"   {line}")
            print("   " + "-" * 56)
            print()
            print("✓ Test passed!")
        else:
            print(f"   ERROR: {response.text}")
            sys.exit(1)

    except requests.exceptions.Timeout:
        print("   ERROR: Request timed out")
        sys.exit(1)
    except Exception as e:
        print(f"   ERROR: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("All tests passed! API is working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
