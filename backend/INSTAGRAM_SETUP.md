# Instagram Integration Setup Guide

## For Instagram Business Account Connected to Personal Facebook Profile

### What You Need

1. **Facebook App** with Instagram Graph API product
   - App ID
   - App Secret
   - Client Token (optional, for server-to-server)

2. **User Access Token** with these permissions:
   - `instagram_basic` - Access basic Instagram account info
   - `pages_read_engagement` - Read page engagement data
   - `pages_show_list` - List pages you manage
   - `business_management` - Access business account info (if needed)

3. **Instagram Business Account ID** (numeric ID, not username)

### Step-by-Step Setup

#### Step 1: Create/Configure Facebook App
1. Go to https://developers.facebook.com/apps/
2. Create a new app or select existing app
3. Add "Instagram Graph API" product
4. Note your App ID and App Secret

#### Step 2: Get User Access Token
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app
3. Add permissions: `instagram_basic`, `pages_read_engagement`, `pages_show_list`
4. Click "Generate Access Token"
5. Copy the token

#### Step 3: Exchange for Long-Lived Token (60 days)
```bash
curl "http://localhost:8000/api/v1/instagram/token/exchange?short_lived_token=YOUR_SHORT_LIVED_TOKEN"
```

Save the returned `access_token` as `INSTAGRAM_ACCESS_TOKEN` in your `.env`

#### Step 4: Find Your Instagram Business Account ID

**Option A: Using the API endpoint**
```bash
curl "http://localhost:8000/api/v1/instagram/debug/find-account"
```

**Option B: Using Graph API Explorer**
1. Go to https://developers.facebook.com/tools/explorer/
2. Use query: `me/accounts?fields=instagram_business_account`
3. Find the `id` field in the `instagram_business_account` object

**Option C: If connected to a Facebook Page**
```bash
curl "http://localhost:8000/api/v1/instagram/page/YOUR_PAGE_ID/instagram"
```

#### Step 5: Update .env File
```bash
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
INSTAGRAM_USER_ID=your_instagram_business_account_id  # Optional - will auto-detect if not set
```

#### Step 6: Test the Integration
```bash
# Test user info
curl http://localhost:8000/api/v1/instagram/user

# Test media/posts
curl "http://localhost:8000/api/v1/instagram/media?limit=5"
```

### Important Notes

- **Instagram Business Account Required**: Only Business or Creator accounts can use the Graph API
- **Token Expiration**: Long-lived tokens expire in 60 days. Use `/api/v1/instagram/token/refresh` to refresh
- **Auto-Detection**: The code will try to auto-detect your Instagram Account ID if not set
- **Permissions**: Make sure your token has all required permissions

### Troubleshooting

- **"An active access token must be used"**: Token expired or invalid. Get a new token.
- **"Object does not exist"**: Check permissions or verify the account ID is correct.
- **"Access token does not contain a valid app ID"**: Token was generated for a different app.
