# Tests Directory

This directory contains all test files for the AI Team Support project, organized by test type.

## Directory Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for component interactions
├── e2e/              # End-to-end workflow tests
├── performance/      # Performance and load tests
├── task_extraction/  # Task extraction specific tests
├── task_similarity/  # Task similarity specific tests
├── task_context_verification/  # Context verification tests
├── tokenization/     # Tokenization tests
├── fixtures/         # Test fixtures and sample data
└── archive/          # Archived/duplicate test files
```

## Test Organization

### Unit Tests (`tests/unit/`)
Tests for individual functions, classes, and modules. These tests should be fast and not require external dependencies.

**Examples:**
- `test_auth.py` - Authentication unit tests
- `test_celery_config.py` - Celery configuration tests
- `test_embeddings.py` - Embedding generation tests
- `test_gemini_integration.py` - Gemini API integration tests

### Integration Tests (`tests/integration/`)
Tests for interactions between multiple components or services.

**Examples:**
- `test_api_endpoints.py` - API endpoint integration tests
- `test_core_workflow.py` - Core workflow integration
- `test_integration.py` - General integration tests
- `test_notion_integration.py` - Notion API integration

### End-to-End Tests (`tests/e2e/`)
Tests that verify complete workflows from start to finish.

**Examples:**
- `test_end_to_end_workflow.py` - Full workflow tests
- `test_correction_workflow.py` - Correction handling workflow
- `test_complete_correction_workflow.py` - Complete correction process

### Performance Tests (`tests/performance/`)
Tests that measure and validate performance characteristics.

**Examples:**
- `performance_test.py` - General performance tests
- `test_correction_performance.py` - Correction handler performance

### Specialized Test Directories

#### `task_extraction/`
Tests specific to task extraction functionality, including sample inputs and results.

#### `task_similarity/`
Tests for task similarity matching algorithms.

#### `task_context_verification/`
Tests for context verification in task processing.

#### `tokenization/`
Tests for text tokenization functionality.

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test type:
```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/           # End-to-end tests only
```

### Run specific test file:
```bash
pytest tests/unit/test_auth.py
```

## Test Files Organization History

**November 2024:** Reorganized test files from root directory and `src/utils/` into proper test directory structure. Duplicate files archived in `tests/archive/`.


