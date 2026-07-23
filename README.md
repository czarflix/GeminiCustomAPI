# Gemini Web-UI Automation Wrapper

A local-only FastAPI experiment that drives the Gemini web UI using Playwright automation. It is not an official Gemini API, SDK, or service integration; it depends on the current web UI and an operator-owned browser session.

## Features

- **Model Selection**: Choose between Gemini 2.5 Pro and 2.5 Flash
- **Automatic Fallback**: Automatically falls back to Flash when Pro quota is exhausted
- **File Upload Support**: Upload files to Gemini (documents, images, code)
- **Persistent Session**: Uses your Google account session stored in a persistent browser profile
- **Browser-session based**: Uses a persistent local profile rather than embedding a provider credential

## Safety and scope

This project is for controlled local experiments. Keep the browser profile out of version control, do not run the service on a public interface, and review Google's current terms and automation policies before use. UI changes, login challenges, quotas, concurrency, account state, and provider availability can break the wrapper. It has no claim of production reliability, provider permission, or access to a stable model API.

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

3. Copy `.env.example` to `.env` and adjust settings if needed:

```bash
cp .env.example .env
```

## Initial Setup (One-time Login)

Before running the API service, you need to authenticate with your Google account:

```bash
python login_helper.py
```

This will open a browser window where you can:
1. Log in to your Google account
2. Complete 2FA if required
3. Verify you can access Gemini

Once logged in successfully, close the browser. Your session will be saved in `./storage/playwright_profile/`.

## Running the Service

Start the FastAPI server:

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Usage

### POST /ask

Send a prompt to Gemini and get a response.

**Request Body:**

```json
{
  "prompt": "Explain quantum computing in simple terms",
  "model": "gemini-2.5-pro",
  "fallback_to_flash": true,
  "files": []
}
```

**Parameters:**

- `prompt` (string, required): The prompt to send to Gemini
- `model` (string, optional): Model to use - `"gemini-2.5-pro"` or `"gemini-2.5-flash"` (default: `"gemini-2.5-pro"`)
- `fallback_to_flash` (boolean, optional): Automatically fallback to Flash if Pro quota exceeded (default: `true`)
- `files` (array, optional): List of file paths to upload (not implemented in v1)

**Success Response:**

```json
{
  "model_requested": "gemini-2.5-pro",
  "model_used": "gemini-2.5-pro",
  "fallback_triggered": false,
  "response_text": "Quantum computing is...",
  "raw_response_html": "<div>...</div>",
  "meta": {
    "latency_ms": 5432
  }
}
```

**Error Response:**

```json
{
  "error": "gemini_session_expired",
  "details": "Detected Google login page; please rerun login helper."
}
```

**Error Types:**

- `gemini_session_expired`: Need to re-authenticate (run `login_helper.py`)
- `pro_quota_exceeded`: Pro quota exceeded and fallback disabled
- `automation_timeout`: Operation timed out
- `unexpected_ui_state`: Gemini UI state not recognized

### Example with cURL

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about coding",
    "model": "gemini-2.5-flash"
  }'
```

### Example with Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "prompt": "What is the meaning of life?",
        "model": "gemini-2.5-pro",
        "fallback_to_flash": True
    }
)

result = response.json()
print(result["response_text"])
```

## Architecture

- **FastAPI**: REST API server
- **Playwright**: Browser automation framework
- **Persistent Browser Context**: Maintains Google account session across restarts
- **Single-threaded**: One request at a time (thread-safe with asyncio locks)

## Limitations

- **Single Request at a Time**: Currently processes one request at a time for stability
- **Session Persistence**: Requires manual re-authentication if Google session expires
- **Web UI Dependent**: Breaks if Gemini significantly changes their UI structure
- **No Streaming**: Waits for complete response before returning

## Troubleshooting

**Session Expired Error:**
```bash
python login_helper.py
```

**Selector Not Found:**
- Gemini may have updated their UI
- Check the selectors in `app/gemini_automation.py`
- File an issue with details

**Browser Crashes:**
- Service will attempt to recreate the browser
- Check logs in console for details

**Headless Issues:**
- Set `HEADLESS=false` in `.env` to debug visually

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models for API
│   ├── browser_manager.py   # Playwright browser lifecycle
│   └── gemini_automation.py # Gemini UI automation logic
├── login_helper.py          # One-time login script
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT

## Disclaimer

This tool automates the Gemini web interface for personal use. It is not affiliated with or endorsed by Google. Use responsibly and in accordance with Google's Terms of Service.
