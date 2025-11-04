# Streamlit Secrets Configuration Guide

This guide explains how to configure secrets for the LNRS Database Application when deploying to Streamlit Community Cloud.

---

## What Are Secrets?

Secrets are sensitive configuration values (like database tokens) that should never be committed to git. Streamlit provides a secure way to store these values in your deployed app.

---

## How to Add Secrets in Streamlit Cloud

### Step 1: Access Secrets Configuration

1. Go to https://share.streamlit.io/
2. Find your deployed app
3. Click the menu (⋮) next to your app
4. Select "Settings"
5. Click "Secrets" in the left sidebar

### Step 2: Add Secrets

Copy and paste the configuration below into the secrets editor, replacing the placeholder values with your actual credentials:

```toml
# Database Mode
# Use "motherduck" for production deployment
# Use "local" only for testing (not recommended for deployed apps)
DATABASE_MODE = "motherduck"

# MotherDuck Database Name
# This is the name of your database in MotherDuck
database_name = "lnrs_weca"

# MotherDuck Authentication Token
# Get this from: https://app.motherduck.com/ → Settings → Access Tokens
motherduck_token = "YOUR_MOTHERDUCK_TOKEN_HERE"
```

### Step 3: Get Your MotherDuck Token

**If you don't have a token yet:**

1. Go to https://app.motherduck.com/
2. Sign in to your account
3. Click your profile icon (top right)
4. Select "Settings"
5. Navigate to "Access Tokens" in the left sidebar
6. Either:
   - Copy an existing token, OR
   - Click "Create New Token"
   - Give it a descriptive name (e.g., "LNRS Streamlit App")
   - Copy the generated token

7. Paste the token into the `motherduck_token` field in your secrets

**IMPORTANT:**
- Store this token securely
- Never commit it to git
- Never share it publicly
- Keep a backup copy in a secure password manager

### Step 4: Save Secrets

1. Click "Save" button in the secrets editor
2. Streamlit will automatically restart your app
3. Wait 30-60 seconds for the app to reload
4. Verify the app loads correctly with new secrets

---

## Local Development Secrets

For local development and testing, you can create a local secrets file:

**File:** `.streamlit/secrets.toml` (already in `.gitignore`)

```toml
# Local Secrets for Testing
# DO NOT COMMIT THIS FILE TO GIT!

# For local MotherDuck testing
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"
motherduck_token = "YOUR_MOTHERDUCK_TOKEN_HERE"
```

**Note:** The `.env` file in the project root takes priority over Streamlit secrets during local development.

---

## Environment Variable Priority

The application checks for configuration in this order:

1. **`.env` file** (local development - highest priority)
2. **Streamlit secrets** (deployed apps and local testing)
3. **Auto-detect** (defaults to "local" if nothing found)

### Local Development
```bash
# .env file
DATABASE_MODE="local"    # Or "motherduck" for cloud testing
```

### Deployed Production
```toml
# Streamlit Cloud Secrets
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"
motherduck_token = "your_actual_token"
```

---

## Secrets Configuration Reference

### DATABASE_MODE

**Purpose:** Determines which database connection to use

**Valid Values:**
- `"motherduck"` - Connect to MotherDuck cloud database (production)
- `"local"` - Connect to local DuckDB file (development only)

**Example:**
```toml
DATABASE_MODE = "motherduck"
```

**When to use each mode:**
- Use `"motherduck"` for all deployed apps
- Use `"local"` for local development only
- Never use `"local"` in Streamlit Cloud (no persistent storage)

---

### database_name

**Purpose:** The name of your database in MotherDuck

**Valid Values:** Any existing MotherDuck database name (string)

**Example:**
```toml
database_name = "lnrs_weca"
```

**Notes:**
- Must exactly match your MotherDuck database name
- Case-sensitive
- For this project, always use `"lnrs_weca"`

---

### motherduck_token

**Purpose:** Authentication token for connecting to MotherDuck

**Format:** Long JWT token string (starts with `eyJ...`)

**Example:**
```toml
motherduck_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI..."
```

**Security Notes:**
- Never commit this token to git
- Never share this token publicly
- Never include in screenshots or documentation
- Store securely in password manager
- Rotate every 6-12 months
- Revoke immediately if compromised

**Getting a New Token:**
1. Go to https://app.motherduck.com/
2. Settings → Access Tokens
3. Create New Token
4. Copy immediately (only shown once)
5. Store securely

---

## Verifying Secrets Configuration

After configuring secrets, verify they work correctly:

### Method 1: Check Dashboard (Easiest)

1. Load your deployed app
2. Look at the dashboard (home page)
3. Check the info box at the top:
   - Should show: `MODE: MOTHERDUCK | Database: lnrs_weca`
   - Should NOT show: `MODE: LOCAL`

### Method 2: Check Logs

1. Go to Streamlit Cloud dashboard
2. Settings → Logs
3. Look for connection messages:
   - ✅ Good: `[OK] Connected to MOTHERDUCK database: lnrs_weca`
   - ❌ Bad: `Connection failed` or `Token invalid`

### Method 3: Test CRUD Operations

1. Navigate to any page (e.g., Measures)
2. Try creating a test record
3. Refresh the page
4. Verify the record still exists
5. If it persists, MotherDuck connection is working correctly

---

## Troubleshooting Secrets

### Problem: "Connection Failed" Error

**Possible Causes:**
- MotherDuck token is incorrect or expired
- Database name is misspelled
- `DATABASE_MODE` is set to wrong value

**Solutions:**
1. Verify token at https://app.motherduck.com/ (should let you sign in)
2. Check database name exactly matches: `lnrs_weca`
3. Ensure `DATABASE_MODE = "motherduck"` (with quotes)
4. Try creating a new token
5. Click "Save" in secrets editor and wait for restart

---

### Problem: App Shows "MODE: LOCAL" Instead of "MOTHERDUCK"

**Cause:** Configuration not loaded or overridden

**Solutions:**
1. Check secrets configuration exists
2. Verify `DATABASE_MODE = "motherduck"` is set
3. Click "Save" in secrets editor
4. Wait 30-60 seconds for app restart
5. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
6. Check logs for configuration loading errors

---

### Problem: "Data Not Persisting" After App Restart

**Cause:** App is in local mode (ephemeral storage)

**Solutions:**
1. Verify MODE shows "MOTHERDUCK" in dashboard
2. Check secrets configuration is correct
3. Reboot app: Settings → Reboot app
4. Test again after reboot
5. Check MotherDuck web UI - data should appear there

---

### Problem: "Token Expired" Error

**Cause:** MotherDuck token has expired

**Solutions:**
1. Go to https://app.motherduck.com/
2. Settings → Access Tokens
3. Create new token
4. Update `motherduck_token` in Streamlit secrets
5. Save and wait for restart

---

## Security Best Practices

### DO:
- ✅ Store tokens only in Streamlit Cloud secrets interface
- ✅ Keep `.env` and `.streamlit/secrets.toml` in `.gitignore`
- ✅ Use different tokens for dev and production (if needed)
- ✅ Rotate tokens every 6-12 months
- ✅ Revoke old tokens after rotation
- ✅ Store backup copy in secure password manager

### DON'T:
- ❌ Never commit secrets to git
- ❌ Never share tokens publicly or in chat
- ❌ Never include tokens in screenshots
- ❌ Never use production tokens for testing
- ❌ Never store tokens in plaintext on your computer
- ❌ Never share your MotherDuck account credentials

---

## Example: Complete Secrets Configuration

Here's a complete, working secrets configuration:

```toml
# Production Secrets Configuration for LNRS Database App
# Add this to Streamlit Cloud: Settings → Secrets

# Database Configuration
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"

# MotherDuck Authentication
# Replace with your actual token from https://app.motherduck.com/
motherduck_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InlvdXJfZW1haWxAZXhhbXBsZS5jb20iLCJzZXNzaW9uIjoieW91cl9zZXNzaW9uX2lkIiwicGF0IjoieW91cl9wYXRfdG9rZW4iLCJ1c2VySWQiOiJ5b3VyX3VzZXJfaWQiLCJpc3MiOiJtZF9wYXQiLCJyZWFkT25seSI6ZmFsc2UsImlhdCI6MTczMDgzODU3Mn0.your_signature_here"
```

**After adding:**
1. Click "Save"
2. Wait for app restart (30-60 seconds)
3. Verify app loads correctly
4. Check dashboard shows "MODE: MOTHERDUCK"

---

## Need Help?

If you're having trouble configuring secrets:

1. **Check the logs:** Streamlit Cloud → Settings → Logs
2. **Verify token works:** Try signing into https://app.motherduck.com/ with your account
3. **Review documentation:** See `DEPLOYMENT.md` for full deployment guide
4. **Test locally first:** Use `.streamlit/secrets.toml` locally to test configuration
5. **Start over:** Delete all secrets, re-add them carefully, ensuring no extra spaces or typos

---

**Remember:** Secrets are sensitive! Always keep them secure and never commit them to version control.
