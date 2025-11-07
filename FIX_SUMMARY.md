# Notion Query Fix Summary

## The Problem
- Error: `'DatabasesEndpoint' object has no attribute 'query'`
- In `notion-client==1.0.0`, the `databases.query()` method doesn't exist
- The code was trying to use `self.notion_client.databases.query()` which fails

## The Solution
Replaced all calls to `databases.query()` with direct `request()` method calls:

**Before (broken):**
```python
response = self.notion_client.databases.query(
    database_id=self.users_database_id,
    filter={...}
)
```

**After (fixed):**
```python
response = self.notion_client.request(
    path=f"databases/{self.users_database_id}/query",
    method="POST",
    body={
        "filter": {...}
    }
)
```

## Files Changed
- `src/core/services/auth_service.py` - Fixed 5 locations where `databases.query()` was called

## Testing
- ✅ Verified `request()` method exists and has correct signature
- ✅ Verified parameter order (path, method, body)
- ✅ Code changes applied to all 5 locations

## Next Steps
The fix has been deployed. The code should now work correctly with `notion-client==1.0.0`.


