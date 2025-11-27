# AI Team Support – Technology Stack

This document catalogs the technologies, libraries, and managed services that power the platform. Use it to understand runtime requirements, evaluate upgrade impacts, or brief stakeholders on dependencies.

---

## 1. Runtime & Language

| Component | Version / Notes | Purpose |
|-----------|-----------------|---------|
| Python | 3.11+ (3.9+ compatible) | Primary language for API, automation, and agents |
| Pip / Poetry | Pip with `requirements.txt` | Dependency management |
| Docker | Multi-stage builds | Packaging for Cloud Run deployments |
| Celery | Worker runtime | Asynchronous task processing and scheduling |

---

## 2. Core Frameworks & Libraries

| Category | Technology | Key Usage |
|----------|------------|-----------|
| Web Framework | Flask, Flask-CORS | REST API (`src/api/app_auth.py`), templating, CORS handling |
| Authentication | PyJWT, bcrypt | JWT issuance/validation, password hashing |
| Email | `imaplib`, `smtplib`, `email` stdlib | Gmail IMAP polling, SMTP confirmations |
| AI / LLM | Google Gemini client (`google-generativeai`), optional OpenAI SDK | Task extraction, correction interpretation, coaching insights |
| Data Processing | Pandas | Normalizing Notion data, reporting |
| Configuration | python-dotenv | Loading `.env` files across tools |
| Logging | Python `logging`, custom config (`src/core/logging_config.py`) | Unified log formatting |

> Additional utilities: `requests`, `uuid`, `datetime`, `json`, `re`, and other stdlib modules for parsing and orchestration.

---

## 3. Data Stores & Integrations

| System | Purpose | Access Layer |
|--------|---------|--------------|
| Notion API | Canonical task database, feedback DB, user registry | `NotionService`, `NotionAgent`, `UserTaskService` |
| PostgreSQL | Correction logs, optional email archive | `CorrectionService`, `EmailArchiveService` via SQLAlchemy |
| Redis / Memorystore | Celery broker, caching | `src/core/services/celery_config.py`, `CachedCorrectionService` |
| Google Gmail (IMAP/SMTP) | Inbound email ingestion, outbound confirmations | `gmail_processor_enhanced.py`, `check_gmail_enhanced.py` |
| Google Gemini (Generative AI) | LLM-backed processing | `src/core/gemini_client.py`, agent modules |

---

## 4. Asynchronous & Scheduling

| Technology | Role |
|------------|------|
| Celery | Executes background tasks (corrections, reminders, cleanups) |
| Celery Beat | Schedules periodic tasks when running worker nodes |
| Google Cloud Scheduler | Triggers the Gmail processor Cloud Run service every 5 minutes |
| Pending conversation JSON store | Persists context verification state between runs |

---

## 5. Deployment & DevOps Tooling

| Tool | Usage |
|------|-------|
| Google Cloud Run | Hosts the Gmail processor and (optionally) the API |
| Google Cloud Build | CI/CD for container images (`deployment/cloudbuild-*.yaml`) |
| Google Secret Manager / Env Vars | Securely stores API keys, tokens |
| Docker Compose | Local development (`docs/README.md`) for multi-service scenarios |
| Git / GitHub | Source control |
| pytest | Automated testing (`tests/`), coverage |
| make (optional) | Scripts for setup/testing (if defined in project root) |

---

## 6. Plugin & Extension System

| Component | Description |
|-----------|-------------|
| Plugin Manager (`src/plugins/plugin_manager_instance.py`) | Discovers and registers plugins at runtime |
| Guidelines Plugins | Enforce SDLC or security policies during processing |
| Feedback Plugins | Provide user feedback loops or data augmentation |
| Integration Plugins | Hook into external services without modifying core code |

> Plugins run inside both the Gmail processor and API contexts, so they must respect the layered architecture.

---

## 7. Observability & Resilience

| Technology | Purpose |
|------------|---------|
| Google Cloud Logging | Captures Cloud Run stdout/stderr |
| Custom Metrics (`correction_metrics.py`) | Tracks correction success rates, latencies |
| Retry Strategies | SQLAlchemy retries, Celery retries, exponential backoff in services |
| Pending Conversation Persistence | File-based fallback to survive restarts |

---

## 8. Documentation & Knowledge Base

| Asset | Description |
|-------|-------------|
| `README.md` | High-level project overview |
| `docs/DOCKER_ENVIRONMENT_SETUP.md` | Docker & environment setup guide |
| `docs/OPERATIONAL_FLOW.md` | End-to-end runtime flow |
| `docs/LAYERED_ARCHITECTURE.md` | Layered architecture map |
| `docs/GOOGLE_CLOUD_DEPLOYMENT.md` | Deployment playbooks |
| `docs/testing/TESTING_GUIDE.md` | Testing strategy |

---

## 9. Environment Variables (High-Level)

| Variable | Category | Notes |
|----------|----------|-------|
| `NOTION_TOKEN`, `NOTION_DATABASE_ID`, etc. | Notion | Identify workspace and databases |
| `GEMINI_API_KEY` | AI Providers | Default model `gemini-1.5-flash` |
| `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` | Gmail | IMAP/SMTP credentials |
| `DATABASE_URL` | PostgreSQL | Required for correction logging |
| `REDIS_URL` | Redis | Celery broker |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM` | Security | API authentication |
| `EMAIL_ARCHIVE_ENABLED` | Feature flags | Toggle archive service |

See `env.production.template` and `docs/README.md` for exhaustive lists and environment-specific notes.

---

## Technology Ownership & Considerations

- **Upgrades** – Track compatibility when upgrading Python, Flask, Gemini SDK, or SQLAlchemy. Ensure tests cover both API and automation flows.
- **Vendor lock-in** – Core data persists in Notion; corrections rely on PostgreSQL. Gemini is pluggable (OpenAI alternative) via environment configuration.
- **Security** – Ensure `.env` files and secrets remain out of source control. Rotate API keys periodically; bcrypt handles password hashing.
- **Scalability** – Gmail processor is stateless and horizontally scalable on Cloud Run; Celery workers can be scaled separately.
- **Testing** – Use pytest suites (unit, integration, e2e) to validate functionality when modifying any part of the stack.

---

Keep this document inline with `requirements.txt`, deployment configs, and architecture docs so the stack view stays accurate as the project evolves.

