# Test Files Archive

This directory contains archived test files that were duplicates or have been superseded.

## Structure

### `utils/`
Contains test files that were originally in `src/utils/` but are duplicates of files already properly organized in `tests/unit/`. These files have been moved here to avoid confusion.

**Note:** If you need to reference these files, use the versions in `tests/unit/` instead.

## Files Archived

### From `src/utils/` (archived: November 2024)
- All `test_*.py` files that duplicated existing files in `tests/unit/`

**Reason:** Test files should be organized in the `tests/` directory structure, not alongside source code. These duplicates were causing confusion and maintenance issues.

### From root directory (archived: November 2024)
- `test_correction_workflow.py` - Older script-style version (292 lines). A more complete pytest-based version exists in `tests/e2e/test_correction_workflow.py` (421 lines).

**Reason:** The e2e version uses proper pytest structure and is more comprehensive. The root version was an older implementation.

