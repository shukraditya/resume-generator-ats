# Deployment Guide

## Overview

This app now uses **in-memory caching** and **streaming PDF generation** - no persistent disk required. This simplifies deployment on all platforms.

## Option 1: Render (Recommended - Easiest)

**Pros:** Free tier, simple setup, no disk configuration needed
**Cons:** Slower cold starts, build takes ~5 mins (LaTeX install)

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub
   - Create New → Web Service
   - Connect your repo

3. **Configure Service**
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     apt-get update && apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended && pip install -r requirements.txt
     ```
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variable**
   - Go to Environment tab
   - Add `KIMI_API_KEY` = your_kimi_api_key

5. **Deploy**
   - Click Manual Deploy → Deploy Latest Commit
   - Wait ~5 mins (LaTeX installation takes time)

**Note:** No disk configuration needed - files are streamed directly to browser.

---

## Option 2: Fly.io (Faster, More Control)

**Pros:** Faster boots, Docker-based, generous free tier
**Cons:** Requires Fly CLI, slightly more setup

### Steps:

1. **Install Fly CLI**
   ```bash
   brew install flyctl  # macOS
   # OR
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Create App** (from repo root)
   ```bash
   fly apps create resume-toolchain
   ```

4. **Set Secrets**
   ```bash
   fly secrets set KIMI_API_KEY=your_kimi_api_key
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```
   - First deploy takes ~10 mins (Docker build with LaTeX)
   - Subsequent deploys are faster

6. **Open App**
   ```bash
   fly open
   ```

**Note:** No volume creation needed - the app is stateless.

---

## Option 3: Self-Hosted (VPS / EC2 / Droplet)

If you have a server:

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended python3-pip

# Clone repo
git clone <your-repo>
cd resume-toolchain

# Install Python deps
pip install -r requirements.txt

# Set env var
export KIMI_API_KEY=your_key

# Run
uvicorn main:app --host 0.0.0.0 --port 8000
```

Use `systemd` or `pm2` to keep it running, `nginx` as reverse proxy.

---

## Architecture Changes

### Caching Strategy

The app now uses an **in-memory cache** for performance:

| Cache Type | Key | TTL | Stored |
|------------|-----|-----|--------|
| PDF | SHA256 of normalized resume | None (deterministic) | PDF bytes + LaTeX source |
| ATS | SHA256 of normalized resume | 1 hour | Analysis report |

Cache benefits:
- Second conversion of same resume → instant PDF download
- Second analysis of same resume → instant results (within 1 hour)
- Response headers include `X-Cache: HIT/MISS`

### Streaming PDF Generation

- PDFs are generated in a temporary directory
- Immediately streamed to browser as `StreamingResponse`
- No files written to disk
- Temp directory auto-cleanup via context manager

---

## Important Notes

### LaTeX Size
- TeX Live is ~1-2GB installed
- Docker image will be large (~2GB)
- Build times are longer because of this

### Free Tier Limits
| Platform | Memory | Sleep | Notes |
|----------|--------|-------|-------|
| Render | 512MB | After 15min | 750 hours/month |
| Fly.io | 256MB shared | After ~5min | $5 credit/month |

For LaTeX compilation, you may need 1GB+ RAM. If builds fail with "Out of memory", upgrade to paid tier ($5-7/month).

### API Key Security
Never commit `.env` files. Set `KIMI_API_KEY` via the platform's secret/environment variable system.

---

## Quick Test After Deploy

1. Open the deployed URL
2. Paste your markdown resume
3. Click "Generate LaTeX + PDF"
4. PDF should download immediately
5. Try ATS analysis with your Kimi API key set
6. Run the same resume again - should be faster (cached)

Check cache status:
```bash
curl https://your-app.com/cache-status
```

---

## Troubleshooting

**"pdflatex not found"**
- Render: Check build logs, apt install may have failed
- Fly: Docker build may have cached incorrectly, run `fly deploy --no-cache`

**"Out of memory" during PDF generation**
- LaTeX needs ~512MB+ RAM
- Upgrade to paid tier or use a VPS with more RAM

**Files not persisting between deploys**
- This is expected! The app is stateless by design.
- Users download files immediately; no server storage.

**Kimi API errors**
- Check `KIMI_API_KEY` is set correctly
- Verify key has credits at platform.moonshot.cn
