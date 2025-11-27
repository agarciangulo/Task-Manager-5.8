# Contributing to AI Team Support

Thank you for your interest in contributing! This guide will help you get started.

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the project's coding standards

## 🔀 Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/Task-Manager-5.8.git
cd "Task-Manager-5.8"
git remote add upstream https://github.com/agarciangulo/Task-Manager-5.8.git
```

### 2. Create a Branch

**Naming convention:** `feature/`, `fix/`, `docs/`, or `refactor/`

```bash
# Create and checkout a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/issue-description
```

**Branch naming examples:**
- `feature/add-email-templates`
- `fix/gmail-connection-timeout`
- `docs/update-onboarding-guide`
- `refactor/task-extraction-service`

### 3. Make Your Changes

- **Write clean, readable code**
- **Follow existing code style** (PEP 8)
- **Add comments** for complex logic
- **Update tests** as needed

**Code style guidelines:**
```python
# ✅ Good: Clear, descriptive names
def extract_tasks_from_email(email_content: str) -> List[Task]:
    """Extract tasks from email content using AI."""
    ...

# ❌ Bad: Unclear abbreviations
def ext_tasks(e: str) -> List:
    ...
```

### 4. Run Tests

**Always run tests before committing:**

```bash
# Run all tests
pytest tests/ -v

# Run relevant tests for your changes
pytest tests/unit/test_your_feature.py -v

# Check test coverage
pytest tests/ --cov=src --cov-report=term-missing
```

**Tests must pass before submitting a PR!**

### 5. Commit Your Changes

**Commit message format:**
```
<type>: <short summary>

<optional detailed description>

<optional issue reference>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/updates
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add email template customization

- Add template configuration in settings
- Support custom HTML templates
- Update email service to use templates

Closes #123"
```

```bash
git commit -m "fix: handle None values in task extraction

Prevents crashes when email content is empty"
```

### 6. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Then create a PR on GitHub
```

## 📝 Pull Request Guidelines

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All existing tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated (if needed)
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Related issues referenced (if any)
```

### PR Requirements

Before your PR can be merged:

- ✅ **All tests pass** - CI must be green
- ✅ **Code coverage maintained** - Don't decrease coverage
- ✅ **No merge conflicts** - Keep branch up to date
- ✅ **Reviewed by maintainer** - At least one approval
- ✅ **Documentation updated** - If adding features

### Keeping Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase your branch on main
git checkout main
git pull upstream main
git checkout feature/your-feature-name
git rebase main

# Resolve conflicts if any, then:
git push origin feature/your-feature-name --force-with-lease
```

## 🧪 Testing Requirements

### Writing Tests

**Every new feature needs tests:**

```python
# Example: tests/unit/test_your_feature.py
import pytest
from src.core.services.your_service import YourService

def test_your_feature_basic():
    """Test basic functionality."""
    service = YourService()
    result = service.do_something()
    assert result is not None

def test_your_feature_error_handling():
    """Test error cases."""
    service = YourService()
    with pytest.raises(ValueError):
        service.do_something(invalid_input=None)
```

### Test Structure

- **Unit tests** - Test individual functions/classes
- **Integration tests** - Test component interactions
- **E2E tests** - Test complete workflows

**When to use each:**
- Unit: Testing a single function or method
- Integration: Testing service → database interactions
- E2E: Testing email → task extraction → Notion sync

### Test Best Practices

```python
# ✅ Good: Clear test names
def test_extract_tasks_from_simple_email():
    """Test task extraction from simple email format."""
    ...

# ✅ Good: Test edge cases
def test_extract_tasks_handles_empty_email():
    """Test that empty emails return empty task list."""
    ...

# ✅ Good: Use fixtures for setup
@pytest.fixture
def sample_email():
    return "Subject: Daily Update\n\n- Task 1\n- Task 2"

def test_extract_tasks(sample_email):
    ...
```

## 📚 Documentation

### Code Documentation

**Add docstrings to new functions/classes:**

```python
def extract_tasks(email_content: str, user_id: str) -> List[Task]:
    """
    Extract tasks from email content using AI.
    
    Args:
        email_content: The raw email text content
        user_id: ID of the user who sent the email
        
    Returns:
        List of Task objects extracted from the email
        
    Raises:
        ValueError: If email_content is empty
        AIAPIError: If AI service call fails
    """
    ...
```

### Update Documentation Files

If your changes affect:
- **Setup process** → Update `ONBOARDING.md`
- **API endpoints** → Update API documentation
- **Deployment** → Update `docs/GOOGLE_CLOUD_DEPLOYMENT.md`
- **Features** → Update `README.md`

## 🐛 Bug Reports

### Before Reporting

1. **Check existing issues** - Don't duplicate
2. **Reproduce the bug** - Can you consistently reproduce it?
3. **Check recent changes** - Might be a recent regression

### Bug Report Template

```markdown
## Description
Clear description of the bug.

## Steps to Reproduce
1. Step 1
2. Step 2
3. See error

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- Python version: 3.11
- OS: macOS 14.0
- Branch/commit: main@abc123

## Error Messages/Logs
```
Paste error logs here
```

## Additional Context
Any other relevant information.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature.

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've thought about.

## Additional Context
Mockups, examples, etc.
```

## 🏗️ Architecture Guidelines

### Adding New Features

1. **Service Layer** - Business logic goes in `src/core/services/`
2. **API Layer** - Routes go in `src/api/routes/`
3. **Models** - Data models go in `src/api/models/`
4. **Tests** - Tests go in appropriate `tests/` subdirectory

### Import Guidelines

**Always use absolute imports:**

```python
# ✅ Correct
from src.core.services.task_service import TaskService
from src.core.agents.task_extraction_agent import TaskExtractionAgent

# ❌ Wrong
from ..services.task_service import TaskService
from .task_extraction_agent import TaskExtractionAgent
```

### Running Scripts

**Always run as modules:**

```bash
# ✅ Correct
python -m src.utils.gmail_processor

# ❌ Wrong
python src/utils/gmail_processor.py
```

## 🔍 Code Review Process

### What Reviewers Look For

- ✅ **Functionality** - Does it work as intended?
- ✅ **Code quality** - Is it readable and maintainable?
- ✅ **Tests** - Are there adequate tests?
- ✅ **Documentation** - Is it documented?
- ✅ **Performance** - Any performance concerns?
- ✅ **Security** - Any security issues?

### Responding to Review Feedback

- **Be open to feedback** - Reviews are collaborative
- **Ask questions** - If feedback is unclear, ask
- **Make requested changes** - Update your PR
- **Explain your reasoning** - If you disagree, discuss it

## 📋 Checklist Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console.log or debug statements
- [ ] No sensitive data committed
- [ ] Commit messages follow format
- [ ] Branch is up to date with main
- [ ] PR description is complete

## 🎯 Good First Issues

Looking for something to start with? Good first issues:

- 🐛 Fix small bugs
- 📝 Improve documentation
- 🧪 Add test coverage
- 🔧 Refactor small functions
- 📊 Improve error messages

## 🙏 Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!

## 📞 Questions?

- Check existing documentation in `docs/`
- Review `ONBOARDING.md` for setup help
- Open an issue for questions or discussions

---

**Remember:** Every contribution, no matter how small, is valuable! 🎉





