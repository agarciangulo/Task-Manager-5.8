# Spike Architecture – AI Task Management Agent (Parallel Prototype)

This document outlines the proposed architecture for the spike described in `docs/SPIKE_SCOPE.md`. It highlights layers, components, data flows, and extension points so the implementation can follow a clear blueprint.

---

## 1. Layered View

```
┌────────────────────────────────────────────────────┐
│ Interaction Layer                                   │
│  - API Gateway (Next.js API Routes or FastAPI)      │
│  - Optional Operator UI (Vercel v0 dashboard)       │
│  - Admin CLI / Postman Collection                   │
└──────────────▲─────────────────────────────────────┘
               │ HTTP requests (task intake, corrections)
┌──────────────┴─────────────────────────────────────┐
│ Orchestration Layer                                │
│  - LangGraph Flow (Vertex AI execution environment)│
│     • IntakeNode                                   │
│     • ExtractionNode (Gemini)                      │
│     • ContextCheckNode (optional)                  │
│     • PersistNode                                  │
│     • InsightNode                                  │
│     • ResponseNode                                 │
│  - Workflow Monitoring Hooks                       │
└──────────────▲─────────────────────────────────────┘
               │ Commands/events, structured payloads
┌──────────────┴─────────────────────────────────────┐
│ Application Services Layer                         │
│  - Task Repository (CRUD abstractions)             │
│  - Correction Service (diff/apply, audit logging)  │
│  - Insight Service (lightweight analytics)         │
│  - Notification Service (stub for email/slack)     │
└──────────────▲─────────────────────────────────────┘
               │ Data access requests
┌──────────────┴─────────────────────────────────────┐
│ Data & Integration Layer                           │
│  - PostgreSQL / Cloud SQL (tasks, corrections, runs)│
│  - Vertex AI (Gemini 1.5 Flash)                     │
│  - Optional: Vector Store (Vertex Matching Engine)  │
└──────────────▲─────────────────────────────────────┘
               │ Configuration, deployment, monitoring
┌──────────────┴─────────────────────────────────────┐
│ Infrastructure & Ops                               │
│  - Cloud Run / Vercel deploy targets                │
│  - Cloud Build CI/CD                                │
│  - Cloud Logging & Monitoring                       │
│  - Secret Manager (API keys, DB creds)              │
└────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

| Component | Responsibilities | Notes |
|-----------|------------------|-------|
| **API Gateway** | Expose `/tasks/intake` and `/tasks/corrections` endpoints, validate payloads, emit run IDs | Choose Next.js (Vercel) for fast iteration or FastAPI (Cloud Run) for Python parity |
| **IntakeNode** | Normalize payload, enrich metadata, hand off to extraction node | Logging and request ID assignment |
| **ExtractionNode** | Prompt Gemini to generate structured tasks; enforce JSON schema | Use Vertex Function calling or manual validation |
| **ContextCheckNode** | Optional follow-up: detect missing info, generate clarifying questions | Stores pending context state if needed |
| **PersistNode** | Call Task Repository to write tasks and run metadata | Handles transactions |
| **InsightNode** | Compute quick insight using stored data or AI summarization | Light logic only |
| **ResponseNode** | Assemble final response object for API; optionally enqueue notification | |
| **Task Repository** | Abstract DB operations (create/read/update tasks); expose models | Keeps LangGraph nodes free of SQL |
| **Correction Service** | Fetch tasks, apply updates/deletes, log before/after, emit events | Should be idempotent |
| **Insight Service** | Provide derived metrics (count due soon, etc.) | Reused by both new-task flow and correction flow |
| **Notification Service (stub)** | Future integration point for email/Slack | Include interface but keep implementation minimal |
| **Observability Hooks** | Decorators/middleware capturing latency, success/failure counts | Feed into Cloud Logging/Monitoring |

---

## 3. Data Flow (New Task Intake)

```
Client → API Gateway → LangGraph Flow
  1. IntakeNode: validate payload, log run
  2. ExtractionNode: Gemini prompt → structured tasks
  3. PersistNode: Task Repository writes to Postgres
  4. InsightNode: compute summary insight
  5. ResponseNode: return JSON {tasks, insight, run_id}
  6. (Optional) Notification Service sends confirmation
```

## 4. Data Flow (Correction Request)

```
Client → API Gateway → LangGraph Correction Flow
  1. IntakeNode: verify original run/task IDs
  2. CorrectionNode: Gemini prompt → update actions
  3. ApplyNode: Correction Service applies diff, logs audit records
  4. InsightNode: recalc summary insight
  5. ResponseNode: return updated tasks + correction log ID
```

---

## 5. Data Model (Minimum Viable)

| Table | Key Fields | Purpose |
|-------|------------|---------|
| `runs` | `id`, `type` (intake/correction), `status`, `created_at`, `latency_ms`, `raw_input`, `raw_output` | Track orchestrated executions |
| `tasks` | `id`, `run_id`, `title`, `status`, `priority`, `due_date`, `metadata` | Canonical tasks produced by extraction |
| `corrections` | `id`, `run_id`, `task_id`, `action` (update/delete), `before`, `after`, `success`, `error` | Audit trail for corrections |
| `insights` | `id`, `run_id`, `summary`, `details`, `created_at` | Store response/insight per run |

Optional future tables: `pending_context`, `notifications`.

---

## 6. Node Connectivity & Data Contracts

Detailed view of the LangGraph nodes, inputs, outputs, and transitions.

### 6.1 New Task Flow Nodes

| Node | Upstream | Downstream | Input Payload | Output Payload |
|------|----------|------------|---------------|----------------|
| `IntakeNode` | API Gateway | `ExtractionNode` | `{ run_id, request: { subject, body, sender, metadata } }` | `{ run_id, normalized_email: { text, sender, thread_id }, context: {...}}` |
| `ExtractionNode` | `IntakeNode` | `ContextCheckNode` (optional) or `PersistNode` | `{ run_id, normalized_email, context }` | `{ run_id, tasks_raw: <Gemini response>, tasks_validated: [ {title, status, ...} ], context }` |
| `ContextCheckNode` | `ExtractionNode` (only when confidence low) | `PersistNode` or API callback | `{ run_id, tasks_validated, gaps: [...], normalized_email }` | Either `{ run_id, clarification_needed: true, questions: [...] }` or pass-through `{ run_id, tasks_validated }` |
| `PersistNode` | `ExtractionNode` or `ContextCheckNode` | `InsightNode` | `{ run_id, tasks_validated, context }` | `{ run_id, tasks_db: [task_records], context }` |
| `InsightNode` | `PersistNode` | `ResponseNode` | `{ run_id, tasks_db }` | `{ run_id, insight: { summary, metrics }, tasks_db }` |
| `ResponseNode` | `InsightNode` | API Gateway | `{ run_id, insight, tasks_db }` | `{ status: "success", run_id, tasks: [...], insight }` (and optionally event for Notification Service) |

### 6.2 Correction Flow Nodes

| Node | Upstream | Downstream | Input Payload | Output Payload |
|------|----------|------------|---------------|----------------|
| `CorrectionIntakeNode` | API Gateway | `CorrectionAgentNode` | `{ correction_run_id, original_run_id, corrections_request: { text, task_ids } }` | `{ correction_run_id, original_tasks, correction_text }` |
| `CorrectionAgentNode` | `CorrectionIntakeNode` | `ApplyCorrectionNode` | `{ correction_run_id, original_tasks, correction_text }` | `{ correction_run_id, actions: [ {task_id, type, updates} ] }` |
| `ApplyCorrectionNode` | `CorrectionAgentNode` | `CorrectionInsightNode` | `{ correction_run_id, actions }` | `{ correction_run_id, updated_tasks, audit_log }` |
| `CorrectionInsightNode` | `ApplyCorrectionNode` | `CorrectionResponseNode` | `{ correction_run_id, updated_tasks, audit_log }` | `{ correction_run_id, insight, updated_tasks, audit_log }` |
| `CorrectionResponseNode` | `CorrectionInsightNode` | API Gateway | `{ correction_run_id, insight, updated_tasks, audit_log }` | `{ status: "success", correction_run_id, updated_tasks, insight, audit_reference }` |

### 6.3 Error & Fallback Paths

- Any node can emit `{ status: "error", run_id, reason, payload }` which routes to an error handler node logging to `runs` table and returning an HTTP 500/4xx.
- `ContextCheckNode` returning `clarification_needed` should short-circuit the main flow and send a response indicating pending state.

---

## 7. State Management Strategy

LangGraph relies on an explicit state object that flows through nodes. The spike will implement the following state constructs:

### 7.1 Shared State Schema

```json
{
  "run_id": "uuid",
  "flow_type": "intake | correction",
  "request": { "...raw request payload..." },
  "normalized_email": { "...processed content..." },
  "tasks_validated": [ { "...task fields..." } ],
  "pending_questions": [ { "question": "...", "reason": "missing_due_date" } ],
  "actions": [ { "task_id": "...", "type": "update", "updates": {...} } ],
  "insight": { "summary": "...", "metrics": {...} },
  "audit_log": [ { "task_id": "...", "before": {...}, "after": {...} } ],
  "status": "in_progress | awaiting_context | success | error",
  "error": { "message": "...", "context": {...} }
}
```

- **Mutation rules:** Each node receives the state object, mutates only its owned keys, and returns a shallow copy. Immutable snapshots are persisted in the `runs` table for replay.
- **Concurrency:** LangGraph’s built-in state store (in-memory for the spike) will later be backed by Redis/Vertex memory for resilience.

### 7.2 Node-Specific State Responsibilities

| Node | Reads | Writes | Persistence Hooks |
|------|-------|--------|-------------------|
| `IntakeNode` | `request` | `normalized_email`, `status` | Insert `runs` row (`status='in_progress'`) |
| `ExtractionNode` | `normalized_email` | `tasks_validated`, `pending_questions`, `status` | Append to `runs.raw_output` (LLM response) |
| `ContextCheckNode` | `tasks_validated`, `pending_questions` | `status` (set to `awaiting_context`) | If awaiting, update run status and emit pending question record |
| `PersistNode` | `tasks_validated` | `tasks_db`, `status` | Create task rows; update run with `tasks_db` IDs |
| `InsightNode` | `tasks_db` | `insight` | Write insight row linked to `run_id` |
| `ResponseNode` | `insight`, `tasks_db`, `status` | Finalize `status='success'`, add response payload | Update `runs` status and response |
| `CorrectionAgentNode` | `original_tasks`, `correction_text` | `actions`, `status` | Store raw LLM correction response |
| `ApplyCorrectionNode` | `actions` | `audit_log`, `updated_tasks`, `status` | Persist correction rows, update tasks |
| `CorrectionResponseNode` | `updated_tasks`, `insight` | Final `status` | Update `runs` + return payload |

### 7.3 Context & Memory Handling

- **Short-term memory:** State object carries context within a single run.
- **Long-term memory:** `runs`, `tasks`, and `corrections` tables act as durable memory; future LangGraph sessions can hydrate state by querying these tables.
- **Pending clarifications:** When `ContextCheckNode` flags missing data, a `pending_context` record is written with the current state. Upon receiving user clarification, the state is rehydrated from the record and the graph resumes at the appropriate node.
- **Idempotency:** `run_id` and `correction_run_id` enforce single-write operations. Replays reuse the same IDs to prevent duplicate persistence.

### 7.4 Error State Transitions

- On exception, nodes set `state.status = "error"` and attach `state.error`.
- Error handler node logs the state snapshot and writes `runs.status='failed'`.
- Replay is supported by reloading the snapshot and restarting the graph from a designated node (to be implemented in future iterations).

---

## 8. Integration Points & Future Extensions

- **Gmail Intake** – Replace HTTP payload with a Gmail webhook or Cloud Function pushing messages into the API.
- **Notion Sync** – Add a downstream service that consumes `tasks` table changes and writes to Notion.
- **Multi-Channel Output** – Notification service connects to email, Slack, Teams.
- **Analytics** – Export `runs` and `corrections` to BigQuery for evaluation dashboards.
- **Security** – Layer on OAuth/JWT once UI/API is exposed to real users.

---

## 9. Observability & Resilience Plan

- Per-node logging with run IDs.
- Latency and failure metrics aggregated into Cloud Monitoring dashboards.
- Retry policies:
  - LangGraph nodes retry once on transient Vertex/DB errors.
  - Correction application guarded by transactions.
- Dead-letter strategy: failed runs written to `runs` table with `status='failed'` and error payload for replay.

---

## 10. Deployment Sketch

| Component | Deployment Target |
|-----------|------------------|
| API Gateway | Vercel (if Next.js) or Cloud Run (if FastAPI) |
| LangGraph Service | Vertex AI custom container / Cloud Run job |
| Database | Cloud SQL (Postgres) |
| Secret Store | Google Secret Manager |
| CI/CD | Cloud Build or GitHub Actions building container + deploy |

---

## 11. Next Implementation Steps

1. Create repository structure reflecting layers (apps/, services/, infra/, docs/).
2. Scaffold API Gateway with stub endpoints returning mock data.
3. Implement LangGraph flow skeleton (nodes logging and passing through data).
4. Hook up Postgres via SQLAlchemy/Prisma (depending on language choice).
5. Integrate Gemini prompts and validation.
6. Add logging/metrics wrappers and finalize spike demo script.

This architecture positions the spike to deliver the scoped flow while highlighting clear seams for expansion into a full production platform.

