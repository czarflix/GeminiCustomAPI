# Quick Start Guide

Get up and running with the Gemini Web API Wrapper in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- A Google account with access to Gemini

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Initial Setup (One-Time)

Authenticate with your Google account:

```bash
python login_helper.py
```

This will:
1. Open a browser window
2. Let you log in to Google/Gemini
3. Save your session for future use

Once logged in and you see the Gemini chat interface, you can close the browser.

## Start the API Service

```bash
python main.py
```

The API will start at `http://localhost:8000`

## Test It

In a new terminal:

```bash
python test_api.py
```

Or with curl:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, Gemini!", "model": "gemini-2.5-flash"}'
```

## API Endpoints

### POST /ask

Send a prompt to Gemini.

**Request:**
```json
{
  "prompt": "Your question here",
  "model": "gemini-2.5-pro",
  "fallback_to_flash": true
}
```

**Response:**
```json
{
  "model_requested": "gemini-2.5-pro",
  "model_used": "gemini-2.5-pro",
  "fallback_triggered": false,
  "response_text": "Gemini's response...",
  "meta": {
    "latency_ms": 5000
  }
}
```

### GET /health

Check service health.

### GET /docs

Interactive API documentation (Swagger UI).

## Models

- `gemini-2.5-pro` - More capable, subject to usage limits
- `gemini-2.5-flash` - Faster, higher rate limits

## Automatic Fallback

When `fallback_to_flash: true` (default), the service will:
1. Try with the requested model
2. If Pro quota is exceeded, automatically retry with Flash
3. Return the Flash response with `fallback_triggered: true`

## Troubleshooting

**"Session expired" error:**
```bash
python login_helper.py
```

**Want to see the browser (debug mode):**

Edit `.env`:
```
HEADLESS=false
```

**API not responding:**

Check if it's running:
```bash
curl http://localhost:8000/health
```

## What's Next?

- See [README.md](README.md) for full documentation
- Visit `http://localhost:8000/docs` for interactive API docs
- Check the `/app` directory for implementation details

## Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP POST /ask
       ▼
┌─────────────────┐
│  FastAPI Server │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Browser Manager     │  (Playwright)
│ - Persistent Profile│
│ - Single Page       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Gemini Automation   │
│ - Model Selection   │
│ - Send Prompt       │
│ - Read Response     │
│ - Quota Detection   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Gemini Web UI       │  (gemini.google.com)
└─────────────────────┘
```

## Important Notes

- **One request at a time:** The service processes requests sequentially for stability
- **Session persistence:** Your Google session is stored locally in `./storage/`
- **No API key needed:** Uses your personal Gemini web access
- **Rate limits apply:** Subject to Gemini web UI rate limits
- **UI changes:** May break if Google significantly updates Gemini's interface

## Support

For issues or questions:
- Check the logs in the console
- Try running with `HEADLESS=false` to see what's happening
- Re-authenticate with `python login_helper.py`

Enjoy using Gemini programmatically! 🚀
