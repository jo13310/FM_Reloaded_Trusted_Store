# FM Reloaded Download Tracking Worker

This Cloudflare Worker provides secure download tracking for the FM Reloaded Mod Store without exposing GitHub tokens to end users.

## Why Cloudflare Workers?

- **Security**: GitHub token stays server-side, never exposed to users
- **Free**: Cloudflare's free tier includes 100,000 requests/day
- **Fast**: Edge computing with global CDN
- **Bot Protection**: Built-in Cloudflare security
- **Rate Limiting**: Prevents abuse with KV storage

## Setup Instructions

### 1. Create Cloudflare Account

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up for free account
3. Verify email

### 2. Create Worker

1. Go to **Workers & Pages** in Cloudflare dashboard
2. Click **Create Worker**
3. Name it: `fm-reloaded-tracker`
4. Click **Deploy**

### 3. Configure Worker

1. Click **Edit Code**
2. Delete the default code
3. Copy and paste the contents of `worker.js`
4. Click **Save and Deploy**

### 4. Set Environment Variables

1. Go to **Settings** → **Variables**
2. Add the following **Secrets** (encrypted):

| Name | Value | Description |
|------|-------|-------------|
| `GITHUB_TOKEN` | `ghp_xxx...` | Your GitHub personal access token |
| `GITHUB_OWNER` | `jo13310` | GitHub username |
| `GITHUB_REPO` | `FM_Reloaded_Trusted_Store` | Repository name |

#### How to generate GitHub token:

1. Go to: https://github.com/settings/tokens/new
2. **Note**: FM Reloaded Download Tracking
3. **Expiration**: 1 year (or No expiration)
4. **Scopes**: Select `repo` (Full control of private repositories)
5. Click **Generate token**
6. Copy the token (starts with `ghp_`)
7. Paste into Cloudflare as `GITHUB_TOKEN` secret

### 5. Enable Rate Limiting (Optional but Recommended)

1. Go to **Settings** → **Bindings**
2. Click **Add Binding**
3. **Type**: KV Namespace
4. **Variable name**: `RATE_LIMIT_KV`
5. Click **Create new namespace**: `fm-track-rate-limits`
6. **Save**

This enables 1-hour rate limiting per IP per mod.

### 6. Get Worker URL

Your worker will be available at:
```
https://fm-reloaded-tracker.{your-subdomain}.workers.dev
```

Example:
```
https://fm-reloaded-tracker.myaccount.workers.dev/download
```

### 7. Update FM Reloaded App (Optional)

If you're self-hosting, update the default URL in `mod_store_api.py`:

```python
# Line 434
tracking_api_url = "https://your-worker-url.workers.dev/download"
```

Or users can set it in their `config.json`:

```json
{
  "tracking_api_url": "https://your-worker-url.workers.dev/download"
}
```

## Testing

### Test with curl:

```bash
curl -X POST https://fm-reloaded-tracker.{your-subdomain}.workers.dev/download \
  -H "Content-Type: application/json" \
  -d '{"mod_name":"Arthur'\''s - PoV Camera Mod"}'
```

Expected response:
```json
{
  "success": true,
  "mod_name": "Arthur's - PoV Camera Mod"
}
```

### Check logs:

1. Go to Worker in Cloudflare dashboard
2. Click **Logs** tab (real-time)
3. Test download from FM Reloaded app
4. See increment logs appear

## Security Features

✅ **No tokens in app code**
- GitHub token stored encrypted in Cloudflare

✅ **Rate limiting**
- 1 increment per IP per mod per hour
- Prevents spam and abuse

✅ **Bot protection**
- Cloudflare's bot detection
- Challenge pages for suspicious traffic

✅ **Audit trail**
- All changes logged in git history
- Cloudflare logs all requests

✅ **CORS enabled**
- Allows requests from FM Reloaded app
- Can restrict to specific domains if needed

## Monitoring

### View Analytics:

1. Go to Worker → **Metrics**
2. See:
   - Requests per day
   - Success rate
   - Response times
   - Errors

### Check GitHub commits:

```bash
git log --oneline --grep="Increment download count"
```

## Troubleshooting

### Worker returns 500 error

**Check:**
- GitHub token is set correctly in secrets
- Token has `repo` scope
- Token hasn't expired

### Rate limiting not working

**Check:**
- KV namespace is bound correctly
- Variable name is exactly `RATE_LIMIT_KV`

### Downloads not incrementing

**Check logs:**
1. Cloudflare dashboard → Worker → Logs
2. Look for error messages
3. Verify mod name matches exactly

## Cost

**Cloudflare Workers Free Tier:**
- 100,000 requests/day
- 10ms CPU time per request
- Unlimited bandwidth

**For FM Reloaded:**
- ~1000 downloads/day = 1000 requests
- Well within free tier limits

## Custom Domain (Optional)

To use your own domain instead of `workers.dev`:

1. Add domain to Cloudflare
2. Go to Worker → **Triggers**
3. Click **Add Custom Domain**
4. Enter: `track.fmreloaded.com`
5. Update app to use new URL

## Support

For issues:
- GitHub: https://github.com/jo13310/FM_Reloaded/issues
- Discord: [Link to FM Reloaded Discord]

## License

Same as FM Reloaded project.
