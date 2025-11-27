# AI Team Support – Layered Architecture Overview

This document maps the system into logical layers so you can reason about responsibilities, dependencies, and extension points. Each layer builds on the ones below it; arrows indicate primary direction of control flow. Use this guide when analyzing impact, onboarding new contributors, or explaining the architecture to other teams or tooling.

```
┌───────────────────────────────┐
│ Experience Interfaces         │   Slack, web UI (future)              │
└──────────────▲────────────────┘
               │ API / Automation
┌──────────────┴────────────────┐
│ Interaction Layer             │   Flask API, Gmail processor          │
└──────────────▲────────────────┘
               │ Service orchestration
┌──────────────┴────────────────┐
│ Application Services          │   Agents, routers, domain services    │
└──────────────▲────────────────┘
               │ Data & integration
┌──────────────┴────────────────┐
│ Integration & Data Access     │   Notion, Gemini, PostgreSQL wrappers │
└──────────────▲────────────────┘
               │ Platform support
┌──────────────┴────────────────┐
│ Infrastructure & Operations   │   Deployment, scheduling, observability │
└───────────────────────────────┘
```

---

## 1. Experience Interfaces (Future-Facing)

*Purpose:* Present information to users and downstream systems; today, most interaction happens through email confirmations and API responses.

- **Email summaries** (`send_confirmation_email_with_correction_support` in `src/utils/gmail_processor_enhanced.py`) – HTML/plain-text bundles with processed tasks, insights, and correction instructions.
- **API consumers** – Clients calling REST endpoints (Postman, internal tools). Currently the API serves operational dashboards, user management, and task queries.
- **Planned interfaces** – Slack bots, admin dashboards, or LLM-based copilots can plug in here by consuming the Interaction Layer APIs.

> This layer has no direct business logic; it merely renders data prepared by lower layers.

---

## 2. Interaction Layer

*Purpose:* Accept requests, authenticate users, translate protocols, and kick off domain workflows.

- **Flask application** (`src/api/app_auth.py`)
  - Registers routes for authentication (`/api/login`, `/api/register`), task dashboards, insights, feedback, and admin operations.
  - Applies JWT-based auth guards (`require_auth`, `require_role`) from `src/core/security/jwt_utils.py`.
  - Initialises plugins (`src/plugins/initialize_all_plugins`) to enforce policy at request boundaries.
- **Gmail processor** (`check_gmail_enhanced.py` and `src/utils/gmail_processor_enhanced.py`)
  - Periodically polls Gmail via IMAP, routes messages, and sends notifications through SMTP.
  - Persists conversation context and delegates to application services for extraction, corrections, and archiving.
- **Celery task endpoints** (`src/core/tasks/*.py`)
  - Provide asynchronous entry points triggered by Celery workers; e.g. `process_correction`, reminder jobs.

> Responsibility stops once a message is validated and handed to application services.

---

## 3. Application Services Layer

*Purpose:* Encapsulate business rules, orchestration, and domain logic. This layer is “where the work happens.”

- **Agents**
  - `TaskExtractionAgent` (`src/core/agents/task_extraction_agent.py`) – Coordinates Gemini prompts to convert email text into structured task payloads.
  - `TaskProcessingAgent` (`src/core/agents/task_processing_agent.py`) – Normalizes and persists tasks; enforces deduplication and enrichment rules.
  - `CorrectionAgent` (`src/core/agents/correction_agent.py`) – Interprets user correction replies and produces validated updates/deletes.
  - `NotionAgent`, `ProjectAnalyzer`, `TaskAnalyzer` – Provide higher-level operations on Notion data and AI insights.
- **Services**
  - `EmailRouter` – Classifies inbound emails (new tasks vs corrections vs noise).
  - `CorrectionService`, `SecureCorrectionService`, `CachedCorrectionService` – Manage correction lifecycle, retries, and resilience.
  - `UserTaskService` – Provides user-specific Notion CRUD and mapping logic.
  - `AuthService` – Handles user provisioning, password hashing, JWT issuance, and lookup.
  - `NotionService` – Raw Notion API wrapper with validation and caching behaviors.
- **Context verification plugins**
  - `src/core/chat/verification.py` and plugin hooks generate clarifying questions, queue reminders, and persist “pending conversation” state.

Dependencies within this layer should go “sideways” sparingly; most components are composed by dependency injection in the Interaction Layer.

---

## 4. Integration & Data Access Layer

*Purpose:* Provide clean abstractions for external systems, storage, and AI providers.

- **Notion access** – `src/core/notion_service.py`, `src/core/services/user_task_service.py` encapsulate Notion client usage, schema mapping, and caching.
- **Gmail access** – IMAP/SMTP wrappers inside `gmail_processor_enhanced.py`; these modules convert raw MIME messages into domain objects.
- **Gemini/OpenAI** – `src/core/gemini_client.py` (default) exposes a simple `generate_content` API; fallback to OpenAI lives behind the same interface.
- **PostgreSQL** – SQLAlchemy models in `src/core/models/*.py` (`TaskCorrectionLog`, `TaskCorrection`); service layer uses session factories and retry-safe operations.
- **Redis / Celery** – `src/core/services/celery_config.py` configures brokers, beat schedules, and task routing.
- **File persistence** – JSON snapshots (`pending_conversations.json`), local `email_storage/` and `logs/` folders for debugging or AirGap scenarios.

> Each integration module hides API specifics, so application services deal with Python objects, not raw HTTP/SQL primitives.

---

## 5. Infrastructure & Operations Layer

*Purpose:* Deliver, monitor, and secure the platform across environments.

- **Deployment assets**
  - Cloud Run Dockerfiles (`Dockerfile`, `deployment/Dockerfile.gmail-processor`).
  - Cloud Build configs (`deployment/cloudbuild-*.yaml`) and shell scripts.
- **Scheduling**
  - Cloud Scheduler job triggers the Gmail processor HTTPS endpoint.
  - Celery Beat orchestrates asynchronous jobs (reminders, cleanups).
- **Configuration management**
  - `.env` templates (`env.production.template`, `.env.*.example`), `docs/DOCKER_ENVIRONMENT_SETUP.md` instructions for local/staging/prod parity.
- **Observability & resilience**
  - Logging utilities (`src/core/logging_config.py`) unify logging format across services.
  - Metrics services (`src/core/services/correction_metrics.py`) capture success rates and durations.
  - `docs/GOOGLE_CLOUD_DEPLOYMENT.md`, `DEPLOYMENT_READY_SUMMARY.md` describe runtime expectations, secrets management, and verification steps.
- **Security posture**
  - JWT configuration, password hashing (`bcrypt`), plugin-based policy checks, and sender validation for corrections.

> This layer should not depend on application logic; it provides the operational scaffolding and guardrails.

---

## Layer Interaction Summary

- **Interaction Layer → Application Services** – `Flask routes`, `Celery tasks`, and `Gmail processor` call agents/services to execute business workflows.
- **Application Services → Integration Layer** – Agents/services rely on Notion clients, Gemini client, PostgreSQL sessions, Redis connections.
- **Integration Layer → Infrastructure** – Connection strings, environment variables, and deployment configs originate from infrastructure assets.
- **Experience Interfaces ← Interaction Layer** – APIs and notification emails expose results to end users and external systems.

Cross-layer calls in the opposite direction should be avoided. If you see infrastructure code reaching into application services, it’s a code smell.

---

## Common Extension Points

- **New communication channel** – Add handler in Interaction Layer (e.g., Slack bot), reuse agents/services, extend plugins if needed.
- **Additional AI provider** – Implement an adapter in the Integration Layer (matching `generate_content` signature), switch in configuration.
- **Alternative task sink** – Create a new service in Application Services that writes to Asana/Jira; use plugin or router to branch emails.
- **Compliance requirements** – Extend Infrastructure Layer with additional logging, secrets rotation, or policy plugins.

---

## Complementary References

- `docs/OPERATIONAL_FLOW.md` – Detailed runtime flow.
- `PROJECT_STRUCTURE.md` – File/folder catalogue.
- `DEPLOYMENT_READY_SUMMARY.md` – Production hardening summary.
- `docs/testing/TESTING_GUIDE.md` – Testing strategy per layer.

Use this layered map alongside the operational flow to keep dependencies clean, plan refactors, and onboard collaborators efficiently.

