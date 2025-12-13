# XM Spotify Sync

Automatically sync tracks from XM Radio stations to Spotify playlists.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   XM Playlist   │────▶│     Backend     │────▶│     Spotify     │
│   (xmplaylist   │     │    (FastAPI)    │     │      API        │
│      .com)      │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    Frontend     │
                        │    (Flask)      │
                        └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.13+
- [mise](https://mise.jdx.dev/) (for tool management)
- A Spotify Developer account

### 2. Clone and Setup

```bash
git clone <repo-url>
cd xmplaylist

# Install dependencies (handled by mise)
mise install
```

### 3. Spotify Authentication Setup

This is the most important step. Follow these instructions carefully.

#### Step 1: Create a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create App"
3. Fill in:
   - App name: `xmplaylist` (or any name)
   - App description: Anything
   - Redirect URI: Add your callback URL (see below)
4. Check the "Web API" checkbox
5. Accept Terms of Service and click "Save"

#### Step 2: Configure Redirect URI

For **local development in a DevContainer/DevPod**, you can't use `localhost` because the browser runs on your host machine while the server runs in the container.

**Option A: Use a public URL you control**
- Add your public URL to Spotify's Redirect URIs (e.g., `https://yoursite.com/callback`)
- The callback doesn't need to do anything - you'll just copy the code from the URL

**Option B: Use localhost (if running natively)**
- Add `http://localhost:8888/callback` to Spotify's Redirect URIs
- Note: Spotify allows `http://` for localhost specifically

#### Step 3: Create your `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Spotify OAuth (from Developer Dashboard)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=https://your-callback-url/

# Target playlist (just the ID, not the full URL!)
# From: https://open.spotify.com/playlist/2l5SCIiH1cjeZQ4TQ7PAAF?si=...
# Use:  2l5SCIiH1cjeZQ4TQ7PAAF
SPOTIFY_PLAYLIST_ID=your_playlist_id

# XM Station to sync from
XM_STATION=lifewithjohnmayer

# Optional settings
SYNC_INTERVAL=7200
LOG_LEVEL=INFO
```

#### Step 4: Get your Refresh Token

**Method A: Using the auth helper (native/localhost)**

```bash
mise run auth
```

This opens a browser, you authorize, and it gives you the refresh token.

**Method B: Manual flow (DevContainer/DevPod)**

1. Run the auth helper to get the authorization URL:
   ```bash
   mise run auth
   ```

2. Copy the URL it prints and open it in your browser

3. Authorize the app in Spotify

4. You'll be redirected to your callback URL with a `code` parameter:
   ```
   https://your-callback-url/?code=AQA7Rsw-TFLvhIS3Mv6MRA...
   ```

5. Copy the entire `code` value (everything after `code=`)

6. Run the exchange script:
   ```bash
   python exchange_code.py
   ```
   
   Paste the code when prompted. It will give you the refresh token.

7. Add the refresh token to your `.env`:
   ```env
   SPOTIFY_REFRESH_TOKEN=AQDxxxxxxxxxxxxxxx...
   ```

### 4. Run the Application

```bash
# Run backend only
mise run backend

# Run frontend only  
mise run frontend

# Run both (if configured)
mise run dev
```

The backend will be available at `http://localhost:22112`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/status` | GET | Get sync service status |
| `/api/v1/sync` | POST | Trigger manual sync |
| `/api/v1/tracks` | GET | Get recent XM tracks |
| `/health` | GET | Health check |

## Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPOTIFY_CLIENT_ID` | Yes | - | Spotify OAuth Client ID |
| `SPOTIFY_CLIENT_SECRET` | Yes | - | Spotify OAuth Client Secret |
| `SPOTIFY_PLAYLIST_ID` | Yes | - | Target playlist ID |
| `SPOTIFY_REDIRECT_URI` | No | `http://localhost:8888/callback` | OAuth callback URL |
| `SPOTIFY_REFRESH_TOKEN` | Yes* | - | OAuth refresh token (*after initial auth) |
| `XM_STATION` | No | `lifewithjohnmayer` | XM station slug |
| `SYNC_INTERVAL` | No | `7200` | Sync interval in seconds |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Development

### Project Structure

```
xmplaylist/
├── src/
│   ├── backend/           # FastAPI backend
│   │   └── src/backend/
│   │       ├── api/       # API routes
│   │       ├── core/      # Interfaces (SOLID)
│   │       ├── models/    # Pydantic models
│   │       ├── providers/ # XM & Spotify providers
│   │       └── services/  # Sync service
│   └── frontend/          # Flask frontend
├── kubernetes/            # K8s manifests
├── .env.example
├── docker-compose.yaml
└── mise.toml
```

### Running Tests

```bash
mise run test
```

### Linting

```bash
mise run lint
```

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

See `kubernetes/` directory for manifests. Designed for GitOps deployment with Flux.

## Troubleshooting

### "Field required" validation errors

Make sure all required environment variables are set in `.env`. The error will tell you which fields are missing.

### "Invalid redirect URI"

Your `SPOTIFY_REDIRECT_URI` in `.env` must exactly match one of the URIs configured in your Spotify Developer Dashboard.

### OAuth code expired

Authorization codes expire quickly (usually within minutes). If you get an error exchanging the code, start the auth flow again.

### Can't reach localhost from DevContainer

Use a public callback URL instead. See the authentication section above.
### Re-create images example

docker compose build backend
docker tag xmplaylist-backend ghcr.io/YOUR_USERNAME/xm-spotify-sync-backend:v0.1.1
docker push ghcr.io/YOUR_USERNAME/xm-spotify-sync-backend:v0.1.1


## License

MIT
