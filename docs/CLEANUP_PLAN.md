# Project Cleanup Plan

## 📁 Documentation Organization

### Keep in Root (Essential)
- `README.md` - Main project documentation
- `ENVIRONMENTS.md` - Environment setup guide
- `DEPLOYMENT_CHECKLIST.md` - Deployment reference

### Move to `docs/` (Reference)
- `AUTHENTICATION.md` - Auth documentation
- `AWS_DEPLOYMENT_STATUS.md` - Deployment status
- `MIGRATION_GUIDE.md` - Migration documentation
- `SECURITY_DEPLOYMENT.md` - Security guide

### Archive to `docs/archive/` (Old/Troubleshooting)
- All `COGNITO_*.md` troubleshooting guides
- All `FIX_*.md` guides
- All `TROUBLESHOOT_*.md` guides
- `SESSION_COOKIE_DEBUG.md`
- `TOKEN_TRACKING.md`
- `OAUTH_TROUBLESHOOTING.md`
- Old status files (`PROJECT_STATUS.md`, `PHASE1_STATUS.md`, etc.)
- Setup guides that are outdated

## 🗑️ Code Cleanup

### Remove Google OAuth Code
- `app/routers/auth.py` - Entire file (replaced by Cognito)
- Google OAuth config from `app/core/config.py`
- Google OAuth references from templates

### Archive Unused Scripts
- Move all `*.py` scripts from root to `scripts/archive/`

## 📝 Result

After cleanup:
- **Root directory:** Clean, only essential files
- **docs/:** Organized documentation
- **docs/archive/:** Old troubleshooting guides
- **scripts/archive/:** Unused helper scripts
- **Code:** Only Cognito auth, no Google OAuth





