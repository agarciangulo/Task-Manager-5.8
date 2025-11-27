# Diagnostic Tests

This folder contains diagnostic and debugging test scripts that are used for troubleshooting specific issues rather than regular automated testing.

## Contents

These scripts help diagnose:
- **Authentication issues** - `test_auth_service_fix.py`
- **Email processing** - `test_email_flow_simulation.py`, `test_email_processing_diagnostic.py`
- **Notion connectivity** - `test_notion_*.py` files

## Usage

Run individual diagnostic scripts when troubleshooting:

```bash
python -m tests.diagnostic.test_notion_connection
```

## Note

These are not part of the regular test suite (`pytest tests/`). They are standalone diagnostic utilities.

