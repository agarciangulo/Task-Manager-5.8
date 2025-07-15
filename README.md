## 📦 Running Scripts and Modules

**Best Practice:**
- Always run scripts in `src/` as modules from the project root using the `-m` flag.
- Example: `python -m src.utils.gmail_processor`
- Do not run scripts directly (e.g., `python src/utils/gmail_processor.py`), as this can break imports.

**Import Style:**
- Always use absolute imports from the `src` package root (e.g., `from core.adapters.plugin_manager import PluginManager`).
- Do not use relative imports (e.g., `from .plugin_manager_instance import ...`).

This ensures robust, error-free imports and a maintainable codebase. 