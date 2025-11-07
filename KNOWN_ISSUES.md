# Known Issues & Technical Debt

This document tracks known issues, bugs, workarounds, and technical debt.

**Last Updated:** November 2024

## 🐛 Active Bugs

### High Priority

**None currently documented. Add bugs here as they're discovered.**

### Medium Priority

#### Issue: User Not Found - Silent Failure
**Description:** When an email is received from an unregistered user, processing fails silently. The email is not marked as read, but the user receives no notification and tasks are never processed.

**Location:** `src/utils/gmail_processor_enhanced.py:1154-1156`

**Impact:** Emails from unregistered users are ignored with no feedback

**Status:** Identified - needs better error handling (send notification email)

**Workaround:** Register all users who will send emails in the Notion users database before they send emails

#### Issue: Format Mismatch Between Gemini Extraction and Notion Schema
**Description:** There was a documented format mismatch (see `debug_format_mismatch.py` from June 2025) between what Gemini extracts and what Notion expects. 

**Status:** ✅ **ALREADY FIXED** - The code now handles this properly.

**Current Implementation:**
- `src/core/task_extractor.py` (lines 340-372) automatically adds all missing fields with defaults:
  - `priority` → defaults to "Medium" 
  - `due_date` → defaults to None
  - `notes` → defaults to ""
  - `is_recurring` → defaults to False
  - `reminder_sent` → defaults to False
- `src/core/notion_service.py` `_format_task_properties()` properly formats all fields for Notion

**Action Needed:** 
- Remove or update the outdated `src/utils/debug_format_mismatch.py` script
- If tasks are still failing to insert, the issue is likely elsewhere (check Notion API errors, authentication, etc.)

**Related Files:**
- `src/utils/debug_format_mismatch.py` - ⚠️ Outdated debug script (can be removed)
- `src/core/task_extractor.py:340-372` - ✅ Fix implemented here
- `src/core/notion_service.py:322-431` - ✅ Formatting handled here

### Low Priority

**None currently documented.**

## ⚠️ Workarounds

**No active workarounds documented. Add workarounds here as issues are discovered.**

## 🔧 Technical Debt

### Code Quality

#### 1. Legacy App Files Need Cleanup
**Issue:** Multiple legacy Flask app files exist that may not be in use:
- `src/api/app_flask.py` - Legacy Flask app
- `src/api/app.py` - Legacy app
- `src/api/app_new.py` - Legacy app

**Current State:** Main app is `src/api/app_auth.py`

**Action Needed:** 
- Verify nothing references the legacy files
- Remove if confirmed unused
- Update any documentation that references them

**Files to Check:**
- `src/core/services/start_async_system.py` - References `app_flask.py`
- `src/utils/start_async_system.py` - References `app_flask.py`
- Documentation files mentioning `app_flask.py`

**Priority:** Medium

#### 2. Duplicate Configuration Files
**Issue:** Configuration files exist in multiple locations:
- `src/config/config.py` - Main config
- `src/utils/config.py` - Duplicate?

**Action Needed:** Consolidate or verify which is actually used

**Priority:** Medium

#### 3. Duplicate Code Files
**Issue:** Several files appear to be duplicated:
- `src/utils/migrate.py` and `src/core/migrate.py` - Migration utilities
- `src/core/logging_config.py` and `src/core/logging/logging_config.py` - Logging setup
- `src/core/exceptions.py` and `src/core/exceptions/exceptions.py` - Exception definitions

**Action Needed:** 
- Identify which versions are actually imported/used
- Consolidate or remove duplicates
- Update imports if needed

**Priority:** Medium

#### 4. Debug Print Statements in Production Code
**Issue:** Numerous `print()` statements with `[DEBUG]` prefixes exist throughout the codebase:
- `src/utils/gmail_processor.py` - Multiple debug prints
- `src/utils/gmail_processor_enhanced.py` - Debug prints
- `src/core/ai/extractors.py` - Debug prints
- `src/core/chat/verification.py` - Debug prints

**Impact:** Clutters logs, potential security concerns if sensitive data is printed

**Action Needed:** 
- Replace with proper logging (use `logger.debug()`)
- Remove or guard with `DEBUG_MODE` flag
- Review for sensitive data exposure

**Priority:** Low (functionality works, but code quality)

**Example Locations:**
```python
# In src/utils/gmail_processor_enhanced.py
print(f"[DEBUG] Loading persistent state from: {PERSISTENCE_FILE}")
print(f"[DEBUG] Raw loaded state: {state}")
```

#### 5. Hardcoded "Dummy" JWT Secret Key
**Issue:** Some code uses a hardcoded "dummy" JWT secret key:

**Locations:**
- `src/utils/gmail_processor.py:1575` - `JWTManager(secret_key="dummy", algorithm="HS256")`
- `src/utils/gmail_processor_enhanced.py:587` - Similar pattern
- `src/utils/gmail_processor_enhanced.py:1150` - Similar pattern

**Impact:** Security concern if this is used for actual authentication

**Action Needed:** Verify this is only for non-auth operations (user lookup). If used for auth, fix immediately.

**Priority:** High (security concern)

#### 6. Inconsistent Error Handling
**Issue:** Error handling patterns vary across the codebase:
- Some functions use try/except with broad Exception catching
- Some return error dicts, others raise exceptions
- Inconsistent use of custom exception classes

**Action Needed:** Standardize error handling patterns

**Priority:** Low (works but could be better)

#### 7. Environment Variable Debug Output in Production
**Issue:** `src/api/app_auth.py` prints environment variables on startup (first 8 chars):

```python
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:8]}...")
```

**Impact:** Clutters logs, but only shows partial values

**Action Needed:** Remove or guard with DEBUG_MODE

**Priority:** Low

### Architecture

#### 1. Service Container Complexity
**Issue:** Dependency injection container could potentially be simplified

**Action Needed:** Review if container adds value or adds complexity

**Priority:** Low

#### 2. Error Handling Standardization
**Issue:** Error handling patterns vary across services and agents

**Action Needed:** 
- Standardize on exception types from `src/core/exceptions/`
- Use consistent error response formats
- Document error handling patterns

**Priority:** Medium

### Documentation

#### 1. API Documentation
**Issue:** Need to verify all API endpoints are fully documented

**Action Needed:** Audit API documentation completeness

**Priority:** Medium

#### 2. Architecture Diagrams
**Issue:** No visual architecture diagrams exist

**Action Needed:** Consider adding diagrams showing:
- Component interactions
- Data flow
- Deployment architecture

**Priority:** Low (nice to have)

### Performance

#### 1. Database Query Optimization
**Issue:** No documented N+1 query issues, but no optimization review conducted

**Action Needed:** Review database queries for optimization opportunities

**Priority:** Low (monitor and optimize as needed)

#### 2. Caching Strategy
**Issue:** Some caching exists but strategy could be more comprehensive

**Action Needed:** Review caching opportunities for frequently accessed data

**Priority:** Low

### Configuration

#### 1. Multiple Environment File References
**Issue:** Documentation mentions `.env.development`, `.env.staging`, `.env.production` but only `env.production.template` exists

**Action Needed:** Create missing templates or update documentation

**Priority:** Low

## 📝 Notes for New Developers

### Areas That Need Attention

- **Gmail processor** - Runs every 5 minutes; monitor for errors in Cloud Logs. Has extensive debug logging that should be cleaned up.
- **Notion rate limits** - Be aware of Notion API rate limits when adding features. Consider implementing rate limit handling.
- **Environment variables** - Many env vars needed; document any new ones added. Current debug output shows first 8 chars - review if this is appropriate.
- **Legacy files** - Several legacy app files exist. Verify before modifying to ensure you're working with the active codebase.

### Common Pitfalls

- **Import errors** - Always use absolute imports and run scripts as modules. Some duplicate files exist that could cause confusion.
- **Test database** - Tests may need database setup; check test fixtures.
- **Cloud deployment** - Budget alerts are set up; watch for cost overruns. Gmail processor runs every 5 minutes.
- **Debug code** - Many debug print statements exist. Use proper logging instead when adding new code.

### Security Concerns

- **Hardcoded JWT secrets** - Verify "dummy" JWT keys are not used for actual authentication
- **Environment variable logging** - Review if partial env var printing is appropriate for production
- **Debug statements** - Review debug prints for sensitive data exposure

## 🔄 Planned Improvements

### Short Term

- [ ] Audit and remove legacy app files (`app_flask.py`, `app.py`, `app_new.py`)
- [ ] Consolidate duplicate files (migrate.py, config.py, exceptions.py, logging_config.py)
- [ ] Replace debug print statements with proper logging
- [ ] Fix format mismatch between Gemini extraction and Notion schema
- [ ] Review and fix hardcoded "dummy" JWT secrets

### Long Term

- [ ] Add monitoring/observability
- [ ] Improve error logging and alerting
- [ ] Performance optimization pass
- [ ] Architecture diagrams
- [ ] Comprehensive API documentation review

## 📊 Issue Tracking

If you discover a new issue:

1. **Check if it's already documented here**
2. **Create a GitHub issue** (if using GitHub)
3. **Add to this document** with:
   - Description
   - Steps to reproduce (for bugs)
   - Workaround (if any)
   - Priority

## 🔗 Related Documentation

- [README.md](README.md) - Project overview
- [ONBOARDING.md](ONBOARDING.md) - Setup guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [HANDOFF_READINESS.md](HANDOFF_READINESS.md) - Handoff assessment

---

**Note:** This document should be updated regularly as issues are discovered and resolved. Priority levels:
- **High:** Security issues, data loss risks, breaking bugs
- **Medium:** Functional issues, code quality problems, technical debt affecting maintainability
- **Low:** Code quality improvements, documentation gaps, nice-to-have features
