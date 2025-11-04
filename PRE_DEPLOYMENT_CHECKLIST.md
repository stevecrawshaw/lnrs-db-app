# Pre-Deployment Checklist

Use this checklist to ensure everything is ready before deploying to Streamlit Community Cloud.

**Date:** _____________
**Deployer:** _____________

---

## Phase 1: Repository Preparation

### Git Repository Status

- [ ] All code changes committed to git
- [ ] Working directory is clean (`git status` shows no uncommitted changes)
- [ ] Latest changes pushed to GitHub (`git push`)
- [ ] Repository is accessible (private or public)
- [ ] Correct branch selected for deployment (usually `main` or `master`)

### Security Check

- [ ] `.env` file is in `.gitignore`
- [ ] `.streamlit/secrets.toml` is in `.gitignore`
- [ ] `data/*.duckdb` files are in `.gitignore`
- [ ] No secrets committed in git history
- [ ] No MotherDuck tokens in code or comments
- [ ] Reviewed recent commits for sensitive data

**Verify with:**
```bash
git status
git log -5 --oneline
grep -r "motherduck_token" --exclude-dir=.git --exclude="*.md"
```

### Required Files Present

- [ ] `app.py` exists in repository root
- [ ] `requirements.txt` exists in repository root
- [ ] `config/database.py` exists
- [ ] All `models/*.py` files present
- [ ] All `ui/pages/*.py` files present
- [ ] `.gitignore` file present and correct

**Verify with:**
```bash
ls app.py requirements.txt config/database.py
ls models/*.py
ls ui/pages/*.py
```

---

## Phase 2: Dependencies Verification

### Python Dependencies

- [ ] `requirements.txt` contains all required packages
- [ ] Package versions are specified correctly
- [ ] No development-only dependencies included

**Contents of `requirements.txt`:**
```txt
duckdb>=1.4.1
streamlit>=1.50.0
polars>=1.34.0
pyarrow>=21.0.0
python-dotenv>=1.2.1
```

- [ ] Contents match expected list above

### Python Version

- [ ] Python version in `pyproject.toml` matches deployment target
- [ ] Python version is 3.13 or compatible

**Check with:**
```bash
grep "requires-python" pyproject.toml
python --version
```

---

## Phase 3: MotherDuck Database

### Database Status

- [ ] MotherDuck account is active
- [ ] Database `lnrs_weca` exists in MotherDuck
- [ ] Database contains all required tables
- [ ] Database contains data (not empty)

**Verify at:** https://app.motherduck.com/

### Database Validation

- [ ] Run schema validation: `DATABASE_MODE=motherduck uv run python validate_motherduck_schema.py`
- [ ] All 20 operational tables match local database
- [ ] Views exist and work (`source_table_recreated_vw`, `apmg_slim_vw`)
- [ ] Macros function correctly (`max_meas()`)
- [ ] Foreign key relationships intact

**Expected Results:**
```
[OK] All 20 operational tables match perfectly
[OK] Both views working correctly
[OK] Macros functional
[OK] All foreign key relationships intact
```

### MotherDuck Token

- [ ] MotherDuck API token is available
- [ ] Token is valid (test at https://app.motherduck.com/)
- [ ] Token has write permissions
- [ ] Token is stored securely (password manager)
- [ ] Token is ready to paste into Streamlit secrets

**Test token:**
```bash
# Try connecting with token
DATABASE_MODE=motherduck uv run python -c "from config.database import db; print(db.test_connection())"
```

**Expected:** `True` (connection successful)

---

## Phase 4: Local Testing

### Local Mode Testing

- [ ] Run `DATABASE_MODE=local uv run python test_local_mode.py`
- [ ] All 10 tests pass
- [ ] No errors or warnings
- [ ] Connection works
- [ ] CRUD operations work
- [ ] Macros functional
- [ ] Views return correct data

**Expected Output:**
```
============================================================
PHASE 5.1 LOCAL MODE TESTING: ALL TESTS PASSED
============================================================
```

### MotherDuck Mode Testing

- [ ] Run `DATABASE_MODE=motherduck uv run python test_motherduck_mode.py`
- [ ] All 10 tests pass
- [ ] Connection to cloud database works
- [ ] CRUD operations work
- [ ] Data persists in cloud
- [ ] Macros functional
- [ ] Views return correct data

**Expected Output:**
```
============================================================
PHASE 5.2 MOTHERDUCK MODE TESTING: ALL TESTS PASSED
============================================================
```

### Streamlit App Testing (Local)

- [ ] Start app: `uv run streamlit run app.py`
- [ ] App loads without errors
- [ ] Set `DATABASE_MODE="motherduck"` in `.env`
- [ ] Restart app, verify connects to MotherDuck
- [ ] Dashboard shows `MODE: MOTHERDUCK`
- [ ] Dashboard shows `Database: lnrs_weca`
- [ ] All pages load correctly
- [ ] Can navigate between pages
- [ ] Test CRUD operations work
- [ ] Changes persist after page refresh

---

## Phase 5: Streamlit Community Cloud Setup

### Account Setup

- [ ] Streamlit Community Cloud account created
- [ ] Signed in at https://share.streamlit.io/
- [ ] GitHub account connected
- [ ] Can access repository from Streamlit Cloud

### Configuration Prepared

- [ ] MotherDuck token copied to clipboard
- [ ] Database name confirmed: `lnrs_weca`
- [ ] Have `SECRETS_TEMPLATE.md` open for reference

**Secrets to configure:**
```toml
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"
motherduck_token = "YOUR_TOKEN_HERE"
```

---

## Phase 6: Documentation Review

### Documentation Complete

- [ ] `DEPLOYMENT.md` reviewed and understood
- [ ] `SECRETS_TEMPLATE.md` reviewed and understood
- [ ] `PRE_DEPLOYMENT_CHECKLIST.md` (this file) completed
- [ ] `README.md` updated with deployment info (if needed)

### Deployment Plan

- [ ] Reviewed `streamlit_deploy_motherduck_implementation_plan.md`
- [ ] Phases 1-5 marked as complete
- [ ] Phase 6 in progress
- [ ] Phase 7 steps understood

---

## Phase 7: Access Control Planning

### Authentication Strategy

- [ ] Decided to use Streamlit's built-in authentication
- [ ] Have email addresses of 2 authorized users
- [ ] Users aware they'll need GitHub/Google/Email account for access
- [ ] Users aware they'll receive invitation emails

**Authorized Users:**
1. Email: _____________________________
2. Email: _____________________________

### Access Control Configuration

- [ ] Plan to set app to "Private" after deployment
- [ ] Plan to invite users via Streamlit dashboard
- [ ] Users informed they'll need to accept invitation
- [ ] Understand how to revoke access if needed

---

## Phase 8: Monitoring Setup

### Monitoring Tools Ready

- [ ] Bookmark: Streamlit Cloud dashboard (https://share.streamlit.io/)
- [ ] Bookmark: MotherDuck dashboard (https://app.motherduck.com/)
- [ ] Bookmark: Deployed app URL (will be created during deployment)
- [ ] Calendar reminder: Daily checks (first week)
- [ ] Calendar reminder: Weekly checks (ongoing)
- [ ] Calendar reminder: Monthly maintenance

### Monitoring Plan

- [ ] Know how to access Streamlit logs (Settings → Logs)
- [ ] Know how to check MotherDuck usage (dashboard)
- [ ] Know how to reboot app if needed (Settings → Reboot)
- [ ] Know how to check user access list (Settings → Sharing)

---

## Phase 9: Rollback Plan

### Backup Strategy

- [ ] Local database backed up (`data/lnrs_3nf_o1.duckdb`)
- [ ] Local database is up-to-date with MotherDuck
- [ ] Know how to restore from local to MotherDuck if needed
- [ ] Understand git revert process if deployment fails

### Emergency Contacts

- [ ] Streamlit support: https://discuss.streamlit.io
- [ ] MotherDuck support: https://motherduck.com/support
- [ ] GitHub repository access confirmed

---

## Phase 10: Final Checks

### Pre-Deployment Verification

- [ ] No uncommitted changes (`git status` clean)
- [ ] Latest code pushed to GitHub
- [ ] All tests passing locally
- [ ] MotherDuck connection tested and working
- [ ] Secrets prepared and ready to paste
- [ ] Documentation reviewed
- [ ] Authorized users identified
- [ ] Monitoring tools bookmarked
- [ ] Backup created

### Deployment Readiness

- [ ] Ready to proceed with deployment
- [ ] Have 30-60 minutes for deployment process
- [ ] Have stable internet connection
- [ ] Have MotherDuck token ready
- [ ] Have authorized user emails ready
- [ ] Understand rollback procedure if needed

---

## Deployment Go/No-Go Decision

Review all checkboxes above. If ALL items are checked, you are ready to deploy.

**Final Status:**

- [ ] ALL checklist items complete
- [ ] No blocking issues
- [ ] Ready to proceed to Phase 7: Deployment & Monitoring

**Decision:**
- [ ] GO for deployment
- [ ] NO-GO (reason): _________________________________

**Sign-off:**

Deployer: _____________________ Date: __________

---

## Post-Checklist: Next Steps

Once this checklist is complete, proceed to:

1. **Deploy to Streamlit Cloud**
   - Follow steps in `DEPLOYMENT.md`
   - Configure secrets
   - Set up access control
   - Verify deployment

2. **Monitor Initial Deployment**
   - Check logs for errors
   - Verify MotherDuck connection
   - Test CRUD operations
   - Confirm data persistence

3. **Invite Users**
   - Configure access control (private app)
   - Invite authorized users
   - Verify user access

4. **Begin Monitoring**
   - Daily checks (first week)
   - Weekly checks (ongoing)
   - Monthly maintenance

---

**Checklist Version:** 1.0
**Last Updated:** 2025-11-04
**Next Review:** After first deployment
