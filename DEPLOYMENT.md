# Deployment Guide - LNRS Database Application

This guide walks you through deploying the LNRS (Local Nature Recovery Strategy) database application to Streamlit Community Cloud with MotherDuck cloud database backend.

## Prerequisites

Before deploying, ensure you have:

1. **MotherDuck Account**
   - Active account at https://app.motherduck.com/
   - Database `lnrs_weca` created with data loaded
   - Valid MotherDuck API token (from Settings → Access Tokens)

2. **GitHub Repository**
   - Repository with application code
   - All files committed (except `.env` and `.streamlit/secrets.toml`)
   - Repository can be private or public

3. **Streamlit Community Cloud Account**
   - Free account at https://share.streamlit.io/
   - Sign in with GitHub (recommended for easy deployment)

---

## Deployment Steps

### Step 1: Prepare GitHub Repository

Ensure these files are committed to your repository:

**Required Files:**
- `app.py` - Main application entry point
- `requirements.txt` - Python dependencies
- `config/database.py` - Database connection handler
- `models/` - All model files
- `ui/pages/` - All UI page files
- `.gitignore` - Ensures secrets are not committed

**Files to EXCLUDE (should be in .gitignore):**
- `.env` - Local environment variables
- `.streamlit/secrets.toml` - Local secrets
- `data/*.duckdb` - Local database files

**Verify with:**
```bash
git status
# Ensure no sensitive files are staged
```

---

### Step 2: Deploy to Streamlit Community Cloud

1. **Navigate to Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app" button

2. **Connect Your Repository**
   - Select your GitHub account
   - Choose the repository containing your app
   - Select the branch (usually `main` or `master`)

3. **Configure App Settings**
   - **Main file path**: `app.py`
   - **Python version**: 3.13 (or your version from `pyproject.toml`)
   - **App URL**: Choose a custom URL or use auto-generated

4. **Advanced Settings (IMPORTANT)**
   - Click "Advanced settings..." before deploying
   - Go to "Secrets" section (see Step 3 below)

---

### Step 3: Configure Secrets

In the Streamlit Cloud app settings, click "Advanced settings" → "Secrets" and add:

```toml
# Database Mode - Use MotherDuck for production
DATABASE_MODE = "motherduck"

# MotherDuck Database Name
database_name = "lnrs_weca"

# MotherDuck Authentication Token
# Get your token from: https://app.motherduck.com/ → Settings → Access Tokens
motherduck_token = "YOUR_MOTHERDUCK_TOKEN_HERE"
```

**How to get your MotherDuck token:**
1. Go to https://app.motherduck.com/
2. Click your profile icon → Settings
3. Navigate to "Access Tokens"
4. Copy your existing token OR create a new one
5. Paste it in the `motherduck_token` field above

**IMPORTANT SECURITY NOTES:**
- Never commit secrets to git
- Never share your MotherDuck token publicly
- Store tokens only in Streamlit Cloud secrets interface

---

### Step 4: Configure Access Control (Authentication)

Streamlit Community Cloud includes **built-in authentication** to restrict access to your app.

**Setup Steps:**

1. **After deploying**, go to your app dashboard at https://share.streamlit.io/

2. **Click the menu (⋮)** next to your app → "Settings"

3. **Navigate to "Sharing"** in the left sidebar

4. **Configure Access Control:**
   - **Option A: Private App with Email Invites**
     - Toggle "Make app private"
     - Click "Invite viewers"
     - Add the email addresses of your 2 authorized users
     - They will receive email invitations

   - **Option B: Restricted by GitHub/Google Accounts**
     - Keep app private
     - Users sign in with their GitHub or Google accounts
     - You control who has access via email invitations

5. **User Experience:**
   - When users visit your app URL, they'll see a login screen
   - They can sign in with:
     - GitHub account (recommended)
     - Google account
     - Email verification
   - After authentication, they'll have full access to the app

**Benefits:**
- Zero code required - fully managed by Streamlit
- No passwords to manage or reset
- Users authenticate with trusted providers (GitHub/Google)
- You control access via email invitations
- Can revoke access anytime from the dashboard

---

### Step 5: Deploy and Verify

1. **Click "Deploy!"**
   - Streamlit will build and deploy your app
   - This typically takes 2-5 minutes
   - Watch the logs for any errors

2. **Monitor Deployment Logs**
   - Look for successful database connection messages
   - Check for any import errors or missing dependencies
   - Verify MotherDuck connection is established

3. **Initial Verification Checklist:**
   - [ ] App loads without errors
   - [ ] Login/authentication screen appears (if configured)
   - [ ] After login, dashboard displays correctly
   - [ ] MODE indicator shows "MOTHERDUCK" (not "LOCAL")
   - [ ] Database name shows "lnrs_weca"
   - [ ] Record counts are correct (measure≈168, area≈68, etc.)
   - [ ] All navigation pages load correctly
   - [ ] Can view measures, areas, priorities, species, grants

4. **Test CRUD Operations:**
   - [ ] Navigate to a page (e.g., Measures)
   - [ ] Create a new test record
   - [ ] Update the test record
   - [ ] Delete the test record
   - [ ] Verify changes persist after page refresh

5. **Test Data Persistence:**
   - [ ] Make a change in the app
   - [ ] Go to Settings → Reboot app
   - [ ] Verify the change still exists after reboot
   - [ ] Confirms data is in MotherDuck (not local storage)

---

## Post-Deployment Configuration

### Invite Users (Access Control)

1. Go to your app settings at https://share.streamlit.io/
2. Click menu (⋮) → Settings → Sharing
3. Enter email addresses of authorized users
4. Click "Invite"
5. Users will receive email invitations with app access link

**For your 2 authorized users:**
- They must create/sign in to Streamlit account
- Can use GitHub, Google, or email authentication
- After first sign-in, they'll have permanent access (until revoked)

### Monitor Usage

**Streamlit Cloud Dashboard:**
- View app logs: Settings → Logs
- Monitor resource usage: Settings → Analytics
- Check app status: Dashboard shows uptime

**MotherDuck Dashboard:**
- URL: https://app.motherduck.com/
- Monitor compute usage (10 CU hours/month on free tier)
- Track storage usage (should be ~23 MB)
- Review query performance

---

## Troubleshooting

### Issue: App won't start

**Symptoms:** Build fails, app shows error screen

**Solutions:**
1. Check Streamlit Cloud logs (Settings → Logs)
2. Verify all secrets are correctly set
3. Ensure `requirements.txt` is in repository root
4. Check Python version matches your local version
5. Review error messages for missing dependencies

### Issue: Can't connect to MotherDuck

**Symptoms:** "Connection failed" errors in logs

**Solutions:**
1. Verify `motherduck_token` in secrets is correct
2. Check database name is exactly `lnrs_weca`
3. Ensure `DATABASE_MODE = "motherduck"` in secrets
4. Test token at https://app.motherduck.com/ (should work)
5. Check MotherDuck service status

### Issue: "Local mode" shows instead of "MotherDuck mode"

**Symptoms:** Dashboard shows "MODE: LOCAL"

**Solutions:**
1. Check secrets configuration has `DATABASE_MODE = "motherduck"`
2. Verify secrets are saved (click "Save" in secrets editor)
3. Reboot the app (Settings → Reboot app)
4. Check logs for configuration loading errors

### Issue: Data not persisting after app restart

**Symptoms:** Changes disappear after reboot

**Solutions:**
1. Verify MODE shows "MOTHERDUCK" (not "LOCAL")
2. Check MotherDuck web UI - data should appear there
3. Review logs for write operation errors
4. Ensure database permissions allow writes

### Issue: Users can't access the app

**Symptoms:** Authentication errors, access denied

**Solutions:**
1. Verify app is set to "Private" in Sharing settings
2. Check user emails are correctly invited
3. Ensure users have accepted the invitation
4. Verify users are signing in with correct account (GitHub/Google)
5. Check invite list in Settings → Sharing

### Issue: Slow performance

**Symptoms:** Pages take >5 seconds to load

**Solutions:**
1. Check MotherDuck connection quality
2. Review query logs for slow queries
3. Verify caching is working (Phase A implementation)
4. Consider upgrading MotherDuck tier if free tier limits reached
5. Check Streamlit Cloud resource usage

---

## Monitoring and Maintenance

### Daily Checks (First Week)
- [ ] App is accessible and loads correctly
- [ ] No errors in Streamlit Cloud logs
- [ ] MotherDuck compute usage is within limits
- [ ] Users can successfully log in and use the app

### Weekly Checks (Ongoing)
- [ ] Review MotherDuck compute usage trends
- [ ] Check for any error patterns in logs
- [ ] Verify data integrity (record counts)
- [ ] Test CRUD operations still work
- [ ] Review user feedback

### Monthly Checks
- [ ] MotherDuck token still valid (tokens can expire)
- [ ] Review storage usage (should remain ~23 MB)
- [ ] Update dependencies if security patches available
- [ ] Review access control (add/remove users as needed)

---

## Updating the Application

### Making Code Changes

1. **Develop Locally:**
   - Make changes in your local repository
   - Test with `DATABASE_MODE="local"` in `.env`
   - Test with `DATABASE_MODE="motherduck"` before deploying

2. **Commit and Push:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

3. **Automatic Deployment:**
   - Streamlit Cloud automatically detects changes
   - App will rebuild and redeploy (takes 2-3 minutes)
   - Monitor logs during redeployment

4. **Test After Deployment:**
   - Verify changes appear in production
   - Test affected functionality
   - Check logs for any new errors

### Updating Dependencies

1. **Update `requirements.txt`:**
   ```bash
   # Update versions as needed
   duckdb>=1.5.0
   streamlit>=1.51.0
   ...
   ```

2. **Commit and push changes**
3. **Streamlit Cloud will rebuild** with new dependencies

### Rolling Back Changes

If a deployment causes issues:

1. **Via Git:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Via Streamlit Cloud:**
   - Settings → Advanced → Deploy from branch
   - Select previous working commit

---

## Backup and Recovery

### MotherDuck Data Backup

MotherDuck provides automatic backups, but you can also:

1. **Export Data Locally:**
   ```bash
   DATABASE_MODE=local uv run python test_local_mode.py
   # This creates a local snapshot
   ```

2. **Regular Exports:**
   - Use the Data Export page in the app
   - Download CSV exports of critical tables
   - Store in a secure location

### Disaster Recovery

If MotherDuck data is lost or corrupted:

1. **Restore from Local Database:**
   ```bash
   duckdb
   ATTACH 'data/lnrs_3nf_o1.duckdb' AS lnrs;
   ATTACH 'md:lnrs_weca?motherduck_token=YOUR_TOKEN' AS motherduck;
   .read lnrs_to_motherduck.sql
   ```

2. **Verify Restoration:**
   ```bash
   DATABASE_MODE=motherduck uv run python test_motherduck_mode.py
   ```

---

## Cost Management

### Streamlit Community Cloud (Free Tier)

**Limits:**
- 1 private app (unlimited public apps)
- Shared resources
- Automatic sleep after inactivity
- Auto-wake on access

**Best Practices:**
- App will sleep after 7 days of inactivity
- First access after sleep takes 10-20 seconds
- No action needed - automatic wake-up

### MotherDuck (Free Tier)

**Limits:**
- 10 GB storage (you're using <0.3%)
- 10 CU hours/month compute
- 5 users

**Monitoring:**
- Check usage at https://app.motherduck.com/
- Dashboard shows compute and storage usage
- Alerts when approaching limits

**Optimization:**
- Phase A caching reduces query load
- Dashboard caching: 5 minutes
- Reference data caching: 1 hour
- Reduces compute usage by ~70%

**If Free Tier Exceeded:**
- MotherDuck will send email notification
- Consider upgrading to paid tier
- Or optimize queries further
- Or limit concurrent users

---

## Security Best Practices

### Access Control
- ✅ Use Streamlit's built-in authentication
- ✅ Keep app private (don't make public)
- ✅ Only invite authorized users (2 people in your case)
- ✅ Review access list monthly

### Token Management
- ✅ Never commit tokens to git
- ✅ Store only in Streamlit Cloud secrets
- ✅ Rotate tokens every 6-12 months
- ✅ Revoke unused tokens immediately

### Code Security
- ✅ Keep dependencies updated
- ✅ Review security advisories
- ✅ Use `.gitignore` for sensitive files
- ✅ Never log sensitive data

---

## Support and Resources

### Streamlit Resources
- Documentation: https://docs.streamlit.io
- Community Forum: https://discuss.streamlit.io
- Status Page: https://status.streamlit.io

### MotherDuck Resources
- Documentation: https://motherduck.com/docs
- Support: https://motherduck.com/support
- Status Page: https://status.motherduck.com

### Project Resources
- Test Scripts: `test_local_mode.py`, `test_motherduck_mode.py`
- Implementation Plan: `streamlit_deploy_motherduck_implementation_plan.md`
- Caching Strategy: `motherduck_caching_strategy.md`

---

## Quick Reference: Environment Variables

### Local Development (.env file)
```bash
# For local testing
DATABASE_MODE="local"

# For MotherDuck testing
DATABASE_MODE="motherduck"
motherduck_token="your_token_here"
database_name="lnrs_weca"
```

### Production (Streamlit Cloud Secrets)
```toml
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"
motherduck_token = "your_token_here"
```

---

## Deployment Checklist

Use this checklist before deploying:

**Pre-Deployment:**
- [ ] All code committed to GitHub
- [ ] `.env` and `secrets.toml` in `.gitignore`
- [ ] `requirements.txt` exists and is correct
- [ ] MotherDuck database `lnrs_weca` exists with data
- [ ] MotherDuck token is valid and has write permissions
- [ ] Local testing passed (`test_local_mode.py`)
- [ ] MotherDuck testing passed (`test_motherduck_mode.py`)

**Deployment:**
- [ ] Created app on Streamlit Community Cloud
- [ ] Configured secrets correctly
- [ ] Set DATABASE_MODE to "motherduck"
- [ ] App builds successfully
- [ ] No errors in deployment logs

**Post-Deployment:**
- [ ] App loads correctly
- [ ] Dashboard shows MOTHERDUCK mode
- [ ] Record counts are correct
- [ ] CRUD operations work
- [ ] Data persists after reboot
- [ ] Configured access control (private app)
- [ ] Invited authorized users (2 people)
- [ ] Users can successfully log in

**Monitoring Setup:**
- [ ] Bookmarked app URL
- [ ] Bookmarked Streamlit Cloud dashboard
- [ ] Bookmarked MotherDuck dashboard
- [ ] Set up weekly check reminders

---

**Deployment Complete!**

Your LNRS database application is now live and accessible to your authorized users via Streamlit's built-in authentication.

For questions or issues, refer to the Troubleshooting section or consult the support resources listed above.
