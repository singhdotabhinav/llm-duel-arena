# Workflow Consolidation

## Problem

When pushing to `develop` or `main`, **multiple workflows were triggering simultaneously**, causing:
- ❌ Duplicate test runs (wasteful)
- ❌ Multiple parallel jobs consuming CI minutes
- ❌ Confusing workflow run history
- ❌ Slower feedback (multiple workflows to check)

## What Was Happening

### Before Consolidation

**On push to `develop`:**

1. **`test.yml` workflow** triggered:
   - `test` job with matrix (Python 3.9, 3.10, 3.11) = **3 parallel jobs**
   - `lint` job = **1 parallel job**
   - `security` job = **1 parallel job**
   - **Total: 5 jobs**

2. **`ci-cd.yml` workflow** triggered:
   - `test` job (Python 3.13)
   - `build` job
   - `deploy-infrastructure` job
   - `deploy-lambda` job
   - `deploy-static` job
   - `integration-test` job
   - `notify` job
   - **Total: 7 jobs**

3. **`deploy.yml` workflow** triggered (only on `main`):
   - `deploy` job (SAM-based deployment)

**Result:** Up to **12+ jobs** running across **3 workflows** for a single push! 🚨

## Solution

### After Consolidation

**Single workflow: `ci-cd.yml`**

- ✅ All testing (linting, formatting, type checking, unit tests)
- ✅ Build verification
- ✅ Infrastructure deployment
- ✅ Lambda deployment
- ✅ Static asset deployment
- ✅ Integration testing
- ✅ Notifications

**Other workflows disabled:**
- `test.yml` - Disabled automatic triggers (can still run manually)
- `deploy.yml` - Disabled automatic triggers (can still run manually)

## Current Workflow Structure

```
Push to develop/main:
  └─ ci-cd.yml workflow
      ├─ test (sequential steps)
      ├─ build
      ├─ deploy-infrastructure
      ├─ deploy-lambda ──┐
      ├─ deploy-static ──┼─→ integration-test → notify
      └──────────────────┘
```

**Parallel execution:**
- `deploy-lambda` and `deploy-static` run in parallel (both depend on `deploy-infrastructure`)
- This is intentional and efficient - they don't depend on each other

## Benefits

1. ✅ **Faster CI/CD** - No duplicate work
2. ✅ **Lower costs** - Fewer CI minutes consumed
3. ✅ **Clearer history** - One workflow per push
4. ✅ **Better organization** - All steps in logical order
5. ✅ **Easier debugging** - Single workflow to check

## If You Need the Old Workflows

The old workflows (`test.yml` and `deploy.yml`) are still available but disabled:
- They can be manually triggered via `workflow_dispatch`
- To re-enable, uncomment the `on:` triggers in those files

## Future Enhancements

Consider adding to `ci-cd.yml`:
- [ ] Matrix testing with multiple Python versions (currently only 3.13)
- [ ] Security scanning (safety, bandit)
- [ ] Import sorting checks (isort)

These features were in `test.yml` but can be integrated into `ci-cd.yml` if needed.

