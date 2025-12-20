# Testing Square Webhooks Locally

Square webhooks require a publicly accessible HTTPS endpoint. This guide shows how to expose your localhost server for testing.

## Option 1: ngrok (Recommended)

ngrok creates a secure tunnel to your localhost server.

### Installation

```bash
# macOS (using Homebrew)
brew install ngrok

# Or download from https://ngrok.com/download
```

### Basic Setup

1. **Start your backend server:**
   ```bash
   cd backend
   python server.py
   # Server should be running on http://localhost:8000
   ```

2. **Start ngrok tunnel:**
   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL:**
   ngrok will display something like:
   ```
   Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
   ```
   Copy the `https://` URL (not the http:// one).

### Configure Square Webhook

1. Go to [Square Developer Dashboard](https://developer.squareup.com/apps)
2. Navigate to **Webhooks** settings
3. Add webhook URL: `https://abc123.ngrok-free.app/api/v1/webhooks/square`
4. Subscribe to **payment.updated** events
5. Copy the **Webhook Signature Secret** and add to your `.env`:
   ```bash
   SQUARE_WEBHOOK_SIGNATURE_SECRET=your_secret_here
   ```

### ngrok Account (Recommended for Testing)

**Free tier:**
- Random subdomain each time (changes on restart)
- Good for quick tests

**Paid tier:**
- Fixed domain (e.g., `https://myapp.ngrok.io`)
- Better for ongoing development

### ngrok Configuration File (Optional)

Create `~/.ngrok2/ngrok.yml` to persist settings:

```yaml
version: "2"
authtoken: your_ngrok_auth_token
tunnels:
  bikepacking-api:
    proto: http
    addr: 8000
    inspect: true
```

Then run: `ngrok start bikepacking-api`

## Option 2: Cloudflare Tunnel (Free Alternative)

Cloudflare Tunnel provides free, stable tunnels with fixed domains.

### Installation

```bash
# macOS
brew install cloudflare/cloudflare/cloudflared
```

### Setup

```bash
# Create a tunnel (one-time setup)
cloudflared tunnel create bikepacking-dev

# Run tunnel
cloudflared tunnel --url http://localhost:8000
```

This gives you a URL like: `https://bikepacking-dev.trycloudflare.com`

## Option 3: VS Code Port Forwarding (If using VS Code)

If you're using VS Code with remote development:
1. Right-click on port 8000 in the "Ports" panel
2. Select "Port Visibility" → "Public"
3. Copy the forwarded URL

## Testing the Webhook

### 1. Test with Square Test Notification

Square allows you to send test notifications from the dashboard:
1. Go to Square Developer Dashboard → Webhooks
2. Find your webhook subscription
3. Click "Send Test Event"
4. Check your server logs for the incoming webhook

### 2. Test with Actual Payment (Sandbox)

1. Use Square's sandbox environment
2. Create a test payment link with metadata: `{"book_id": "1"}`
3. Complete a test payment
4. Check server logs and database for the purchase record

### 3. Monitor Webhook Delivery

Square Dashboard shows:
- Webhook delivery status
- Response codes
- Retry attempts
- Request/response details

### Check Server Logs

Your FastAPI server will log webhook events:
```bash
# In your terminal running the server
INFO: Processed Square webhook event abc123: {'processed': True, ...}
```

## Troubleshooting

### Webhook Not Received

1. **Check ngrok is running:**
   ```bash
   # Visit http://localhost:4040 (ngrok web interface)
   # You'll see all HTTP requests in real-time
   ```

2. **Verify URL is correct:**
   - Must use `https://` (not `http://`)
   - Must include full path: `/api/v1/webhooks/square`
   - Check for typos

3. **Check Square webhook logs:**
   - Square Dashboard → Webhooks → Your webhook → Delivery Logs
   - Look for error responses (401, 500, etc.)

### Signature Verification Failing

1. **Verify environment variable:**
   ```bash
   # Check .env file has:
   SQUARE_WEBHOOK_SIGNATURE_SECRET=your_actual_secret
   ```

2. **Restart server after adding env var:**
   ```bash
   # Server must be restarted to load new env vars
   ```

3. **Check header name:**
   - Square uses: `x-square-hmacsha256-signature`
   - Code should match exactly

### ngrok Free Tier Warning Banner

ngrok free tier shows a warning page on first visit. You have two options:

1. **Click through manually once** (then webhooks work)
2. **Use ngrok's inspection bypass** (requires account):
   ```bash
   ngrok http 8000 --request-header-add "ngrok-skip-browser-warning: true"
   ```
   However, Square won't send this header, so the first webhook might fail.

**Solution:** Visit the ngrok URL in a browser first, click through the warning, then webhooks should work.

## Security Considerations

### Development Only
- These tools expose your local server to the internet
- **Only use for testing, never in production**
- Disable the tunnel when not testing

### Production Deployment
For production, use:
- Proper HTTPS (SSL certificate)
- Fixed domain (e.g., `api.yourdomain.com`)
- Reverse proxy (nginx, Caddy, etc.)
- Firewall rules
- Rate limiting

## Quick Start Checklist

- [ ] Install ngrok: `brew install ngrok`
- [ ] Start backend server: `python backend/server.py`
- [ ] Start ngrok: `ngrok http 8000`
- [ ] Copy HTTPS URL from ngrok
- [ ] Add webhook in Square Dashboard with full URL
- [ ] Add `SQUARE_WEBHOOK_SIGNATURE_SECRET` to `.env`
- [ ] Restart backend server
- [ ] Send test notification from Square Dashboard
- [ ] Check server logs for webhook receipt
- [ ] Verify purchase record in database

## Example Workflow

```bash
# Terminal 1: Start backend
cd backend
python server.py

# Terminal 2: Start ngrok
ngrok http 8000

# Copy the https:// URL (e.g., https://abc123.ngrok-free.app)

# Add to Square Dashboard webhook URL:
# https://abc123.ngrok-free.app/api/v1/webhooks/square

# Test it:
# 1. Send test notification from Square Dashboard
# 2. Check Terminal 1 for webhook logs
# 3. Check database: SELECT * FROM book_purchases;
```


