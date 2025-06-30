# Weather Backend: OpenWeatherMap API Key Setup

## Local Development

1. Copy `.env.example` to `.env` in the `weather_backend` directory:
   ```
   cp .env.example .env
   ```
2. The `.env` file should include your OpenWeatherMap API key:
   ```
   OPENWEATHERMAP_API_KEY=e292f7de32e889f55d4f863fd0303c20
   ```
3. The backend loads this key using `python-dotenv`. No changes to code are needed if the `.env` exists.

## Production

- **RECOMMENDED:** Set the `OPENWEATHERMAP_API_KEY` as an environment variable in your deployment platform (do NOT use `.env` in production).
- The backend reads `OPENWEATHERMAP_API_KEY` from the environment for all requests.

## Backend Behavior

- If the API key is missing, backend routes return a 502 error with a message indicating misconfiguration.
- The API key is never exposed to frontend or logs.

## Security Note

- NEVER commit a real `.env` file with secrets to version control.
- Only commit `.env.example` for reference.

---
