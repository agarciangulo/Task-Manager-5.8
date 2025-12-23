# Spike Architecture – AI Task Management Agent (Parallel Prototype)

This document outlines the proposed architecture for the spike described in `docs/SPIKE_SCOPE.md`. It defines three core processes, their components, data flows, and the databases that support them.

---

## 1. System Overview

The AI Task Management Agent consists of **three core processes** that work together to help users manage tasks, receive insights, and query their data:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI TASK MANAGEMENT AGENT                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   PROCESS 1     │  │   PROCESS 2     │  │   PROCESS 3     │             │
│  │   Task Intake   │  │  Prioritization │  │  Query System   │             │
│  │   & Processing  │  │   & Insights    │  │  & Analytics    │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           ▼                    ▼                    ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DATA LAYER                                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐        │   │
│  │  │ Task DB  │ │ User     │ │ Insights │ │ Best Practices   │        │   │
│  │  │          │ │ Behaviour│ │    DB    │ │       DB         │        │   │
│  │  │          │ │    DB    │ │          │ │                  │        │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.5 Email Router (Pre-Process)

Before routing to Process 1 or Process 3, incoming emails pass through the Email Router:

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   EMAIL     │      │  Email Router   │      │  Process 1 or 3 │
│   INBOX     │ ──▶  │                 │ ──▶  │                 │
│             │      │ 1. Validate     │      │                 │
└─────────────┘      │ 2. Deduplicate  │      └─────────────────┘
                     │ 3. Classify     │
                     └─────────────────┘
```

### Router Responsibilities

| Step | Action | Details |
|------|--------|---------|
| **1. Validate Sender** | Check `users` table | Reject unknown senders with "please register" reply |
| **2. Deduplicate** | Check Gmail Message-ID | Skip if already processed |
| **3. Classify Intent** | AI classification | Task/Activity → Process 1, Query → Process 3 |
| **4. Truncate** | Limit email size | Truncate >10K characters with warning |

### Intent Classification Examples

| Email Content | Classification | Route To |
|---------------|----------------|----------|
| "I completed the report today" | Task/Activity | Process 1 |
| "Actually the due date is Thursday" | Correction | Process 1 |
| "What tasks do I have due tomorrow?" | Query | Process 3 |
| "The report is done, what's next?" | Task + Query | Process 1 (primary), note query for follow-up |

---

## 2. Process 1: Task Intake & Processing Pipeline

### 2.1 Overview

This process handles all incoming emails from users, extracts tasks, compares with existing data, and updates the database accordingly.

### 2.2 Flow Diagram

```
┌─────────────┐      ┌─────────────────┐      ┌───────────────────┐         ┌──────────┐
│   EMAIL     │      │  Task Extractor │      │  Task Processor   │  ──▶    │  Task    │
│             │      │                 │      │                   │ writes  │    DB    │
│ Contains:   │ ──▶  │ - Classifies    │ ──▶  │ - Compares new    │         │          │
│ • Activities│      │   intent        │      │   vs existing     │  ◀──    │          │
│ • Corrections      │ - Checks context│      │ - Decides: ADD or │ reads   │          │
│ • Context   │ ◀──  │ - Asks for more │      │   UPDATE          │         │          │
│   replies   │      │   if needed     │      │ - Updates DB      │         │          │
└─────────────┘      └────────┬────────┘      └───────────────────┘         └────┬─────┘
       ▲                      │                                                  │
       │                      │ analyzes patterns (AI)                           │
       │                      ▼                                                  │
       │             ┌─────────────────┐                              ┌──────────▼──────┐
       │             │ Behavior        │                              │ Task Presenter  │
       │             │ Analyzer (AI)   │                              │                 │
       │             │                 │                              │ Outputs:        │
       │             │ - Detects meta  │                              │ • Daily summary │
       │             │   patterns      │                              │ • High priority │
       │             │ - Generates     │                              │ • Corrections   │
       │             │   observations  │                              │   confirmed     │
       │             └────────┬────────┘                              └─────────────────┘
       │                      │ stores                                        │
       │                      ▼                                               │
       │             ┌─────────────────┐                                      │
       │             │ User Behaviour  │                                      │
       │             │      DB         │                                      │
       │             └─────────────────┘                                      │
       │                                                                      │
       └──────────────────────────────────────────────────────────────────────┘
                              (email response)
```

### 2.3 Email Input Types

| Content Type | Example | Purpose |
|--------------|---------|---------|
| **New Activities** | "Today I completed X, Y, Z" | Log completed tasks |
| **Corrections** | "Task was due Wednesday not Thursday" | Update existing tasks |
| **Context Replies** | Response to system's clarification request | Fill in missing information |

### 2.4 Component Details

#### Task Extractor
| Responsibility | Description |
|----------------|-------------|
| **Classify Intent** | Determine if email contains new activities, corrections, or context replies |
| **Extract Tasks** | Identify individual tasks from free-form text or lists |
| **Transform to JSON** | Use AI to convert extracted tasks into uniform JSON schema (see below) |
| **Check Completeness** | Verify tasks have required info (due date, priority, etc.) |
| **Request Context** | Send email back to user if information is missing |
| **Trigger Behavior Analysis** | Pass interaction data to Behavior Analyzer for pattern detection |

**Task JSON Schema:**
```json
{
  "task_id": "uuid",
  "title": "string (required)",
  "description": "string (optional)",
  "due_date": "ISO 8601 date (optional)",
  "priority": "high | medium | low (default: medium)",
  "status": "pending | in_progress | completed",
  "category": "string (optional)",
  "estimated_hours": "number (optional)",
  "source_email_id": "string",
  "extracted_at": "ISO 8601 timestamp",
  "raw_text": "original text from email"
}
```

**Example Transformation:**

*User writes:*
> "Tomorrow I need to finish the quarterly report (urgent!) and also send follow-up emails to the 3 clients from last week's meeting"

*AI transforms to:*
```json
[
  {
    "title": "Finish quarterly report",
    "due_date": "2025-12-24",
    "priority": "high",
    "status": "pending",
    "raw_text": "finish the quarterly report (urgent!)"
  },
  {
    "title": "Send follow-up emails to clients",
    "description": "3 clients from last week's meeting",
    "due_date": "2025-12-24",
    "priority": "medium",
    "status": "pending",
    "raw_text": "send follow-up emails to the 3 clients from last week's meeting"
  }
]
```

#### Behavior Analyzer (AI-Powered)
| Responsibility | Description |
|----------------|-------------|
| **Analyze Patterns** | Use AI to detect meta-patterns in user behavior over time |
| **Generate Observations** | Create human-readable observations (e.g., "User tends to submit tasks without due dates") |
| **Track Frequency** | Monitor how often patterns occur |
| **Store to DB** | Persist observations to User Behaviour DB |

**Example Meta-Behavior Observations:**
- "User frequently submits tasks without context - consider prompting for details"
- "User tends to forget to log completed tasks - send reminders"
- "User often corrects due dates within 24 hours - verify dates at intake"
- "User is highly responsive to context requests - can ask follow-ups"

#### Task Processor
| Responsibility | Description |
|----------------|-------------|
| **Read Existing Tasks** | Fetch current tasks from Task DB for comparison |
| **Hybrid Comparison** | Use embeddings + AI to find similar tasks (existing implementation) |
| **Classify Match Type** | Distinguish between: correction, recurring occurrence, or new task |
| **Apply Corrections** | Process correction requests from user |
| **Log Recurring** | Create new occurrence linked to recurring pattern |
| **Update Database** | Write final state to Task DB |

**Hybrid Comparison Logic (Existing):**
The spike will leverage the existing `src/core/task_similarity.py` which implements:
1. Chroma embeddings for fast top-k candidate retrieval
2. AI (Gemini) for semantic analysis of candidates
3. Returns confidence score and matched task

**Expanding ChromaDB Usage:**
The existing `SimpleChromaEmbeddingManager` can be extended for:
- **Intent classification cache** - Store email→intent mappings, reuse for similar emails
- **Query pattern cache** - Cache common queries for Process 3
- **Recurring pattern detection** - Cluster similar tasks to detect patterns
- **User behavior clustering** - Group similar user behaviors

**Match Classification:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    MATCH CLASSIFICATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Similar task found?                                            │
│         │                                                        │
│    ┌────┴────┐                                                  │
│    │         │                                                  │
│   NO        YES                                                 │
│    │         │                                                  │
│    ▼         ▼                                                  │
│  CREATE    Is it a recurring pattern?                           │
│   NEW      (logged 3+ times before)                             │
│  TASK            │                                              │
│           ┌──────┴──────┐                                       │
│           │             │                                       │
│          NO            YES                                      │
│           │             │                                       │
│           ▼             ▼                                       │
│      Same day?    LOG NEW OCCURRENCE                            │
│           │       (link to pattern,                             │
│      ┌────┴────┐   update streak)                               │
│      │         │                                                │
│     YES       NO                                                │
│      │         │                                                │
│      ▼         ▼                                                │
│  CORRECTION  CREATE NEW                                         │
│  (update)    (different day)                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Recurring Patterns: Assume → Announce → Correct

Since this is email communication (not a UI), we minimize back-and-forth by:
1. **Assuming** patterns automatically based on detection
2. **Announcing** assumptions in Task Presenter emails
3. **Correcting** only if user replies with disagreement

**Detection Flow:**
```
┌─────────────────────────────────────────────────────────────────┐
│  AUTOMATIC DETECTION (no user interaction required)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ 1. Language     │  │ 2. Pattern      │  │ 3. User         │ │
│  │    Signals      │  │    Analysis     │  │    Explicit     │ │
│  │                 │  │                 │  │                 │ │
│  │ "daily",        │  │ 3+ similar      │  │ User says       │ │
│  │ "weekly",       │  │ tasks on        │  │ "I do this      │ │
│  │ "standup",      │  │ different days  │  │ every day"      │ │
│  │ "sync"          │  │                 │  │                 │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┘           │
│                                │                                │
│                                ▼                                │
│                   AUTO-CREATE PATTERN                           │
│                   (status: "assumed")                           │
│                                │                                │
│                                ▼                                │
│              ANNOUNCE IN TASK PRESENTER EMAIL                   │
└─────────────────────────────────────────────────────────────────┘
```

**Detection Priority:**
| Priority | Method | Example | Confidence |
|----------|--------|---------|------------|
| 1 | User explicit | "I do this every day" | Highest |
| 2 | Language signals | "Weekly report", "daily standup" | High |
| 3 | Pattern analysis | 3+ similar on different days | Medium |

**New Table: `recurring_patterns`**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Owner |
| `title` | String | Activity name (e.g., "Daily standup with Acme") |
| `expected_frequency` | String | "daily", "weekly:mon,wed,fri", "monthly" |
| `detection_method` | String | "language", "pattern_analysis", "user_explicit" |
| `status` | String | "assumed", "confirmed", "rejected" |
| `announced_at` | DateTime | When user was notified |
| `last_logged_at` | DateTime | Most recent occurrence |
| `streak_count` | Integer | Consecutive occurrences logged |
| `created_at` | DateTime | When pattern was detected |

**Status Values:**
- `assumed` - System detected and announced, user hasn't responded
- `confirmed` - User explicitly confirmed or corrected frequency
- `rejected` - User said "not recurring", won't track anymore

**Announcement in Task Presenter:**
```
🔄 NEW RECURRING PATTERNS DETECTED:
• "Daily standup with Acme" → marked as DAILY
  (logged 4 times this week on different days)
• "Weekly report to leadership" → marked as WEEKLY
  (detected from language)

↩️ Reply to correct: "Daily standup is not recurring"
   or "Weekly report is actually monthly"
```

**Correction Handling (via Process 1):**
| User Says | Action |
|-----------|--------|
| "X is not recurring" | Set status='rejected', delete pattern |
| "X is weekly, not daily" | Update frequency, set status='confirmed' |
| "Stop tracking X" | Set status='rejected' |

**Missing Activity Check (for Process 2):**
```
⚠️ RECURRING ACTIVITIES NOT LOGGED TODAY:
• "Daily standup with Acme" - usually logged by now
  Reply "Done" if completed, or "Skip today" to note the miss

🔥 STREAK UPDATE:
• "Weekly report" - 8 week streak! Keep it up!
```

#### Task Presenter
| Responsibility | Description |
|----------------|-------------|
| **Generate Summary** | Create summary of tasks completed that day |
| **Highlight Priorities** | List high-priority activities needing immediate attention |
| **Confirm Changes** | Acknowledge corrections that were applied |
| **Send Response** | Email the combined output back to user |

### 2.5 Email Response Strategy

| Scenario | Email Type | Reason |
|----------|-----------|--------|
| Daily summary / Tasks completed | New email | Read-only, no response needed |
| Confirmation of corrections | Reply to original | Context matters, closes the loop |
| Asking for more context | Reply to original | User needs to see what was unclear |
| High priority alerts | New email | Stands out, urgent |

---

## 3. Process 2: Prioritization & Insights Generation

### 3.1 Overview

This process generates daily task priorities and personalized insights by analyzing the user's task database against organizational best practices.

### 3.2 Trigger

**Scheduled Daily Job** (e.g., Cloud Scheduler at 6:00 PM)
- Runs automatically for all active users
- Generates priorities for the next day
- Sends combined email with priorities + insights

### 3.3 Flow Diagram

```
┌──────────────┐         ┌───────────────────┐
│   Task DB    │────────▶│  Task Prioritizer │──────────────┐
│              │ reads   │                   │              │
│              │         │ Creates prioritized              │ prioritized
│              │         │ list for next day │              │ task list
│              │         └───────────────────┘              │
│              │                                            │
│              │         ┌───────────────────┐              ▼
│              │────────▶│ Insight Generator │      ┌───────────────┐
└──────────────┘ reads   │                   │      │   Combined    │      ┌──────────┐
                         │ - Analyzes backlog│      │   Email to    │ ──▶  │   USER   │
┌──────────────┐         │ - Creates advice  │      │     User      │      └──────────┘
│Best Practices│────────▶│ - What to improve │      │               │
│      DB      │ reads   │ - What to fix     │      │ Contains:     │
│              │         │                   │      │ • Task list   │
│              │         └─────────┬─────────┘      │ • Insights    │
└──────────────┘                   │                │   (separate)  │
                                   │ stores         └───────▲───────┘
                                   ▼                        │
                         ┌───────────────────┐              │ insights
                         │ Insights Database │──────────────┘
                         │                   │
                         │ (all generated    │
                         │  insights logged) │
                         └───────────────────┘
```

### 3.4 Component Details

#### Task Prioritizer
| Responsibility | Description |
|----------------|-------------|
| **Read Task Backlog** | Fetch all open/pending tasks from Task DB |
| **Apply Prioritization Logic** | Consider due dates, priority flags, dependencies |
| **Generate Priority List** | Create ordered list of tasks for next day |

#### Insight Generator
| Responsibility | Description |
|----------------|-------------|
| **Analyze User Backlog** | Read current state from Task DB |
| **Compare to Best Practices** | Check patterns against Best Practices DB |
| **Generate Advice** | Create actionable recommendations |
| **Store Insights** | Log all generated insights to Insights Database |

### 3.5 Example Insights

- "You have 5 overdue tasks - consider addressing these first"
- "You've been logging tasks without due dates - try adding deadlines"
- "Your high-priority queue is growing - consider delegating"
- "Great job completing 12 tasks this week - above your average!"

### 3.6 Combined Email Output

The Task Prioritizer and Insight Generator outputs are combined (but kept as separate sections) in a single email:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 YOUR PRIORITIES FOR TOMORROW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Complete quarterly report (High Priority, Due: Tomorrow)
2. Send client follow-up emails (Medium Priority)
3. Review team submissions (Medium Priority)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 INSIGHTS & RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• You have 3 tasks overdue by more than a week - consider re-prioritizing
• Great job completing 12 tasks this week - above your average!
• Suggestion: Your "Admin" category is growing - block time for admin work
...
```

---

## 4. Process 3: Query/Analytics System

### 4.1 Overview

This process enables users and managers to query data across all databases with appropriate access controls and privacy safeguards.

### 4.2 Interface

| Phase | Interface | Description |
|-------|-----------|-------------|
| **MVP** | Email | Users send queries via email (e.g., "What tasks do I have due this week?") |
| **Future** | Web UI | Dedicated query interface with chat-like experience |
| **Future** | Slack/Teams | Query via messaging platforms |

### 4.3 Flow Diagram

```
                                                      ┌─────────────────────────────────┐
                                                      │        DATA ACCESS LAYER        │
                                                      ├─────────────────┬───────────────┤
                                                      │   User's Own    │   Firm Total  │
                                                      │   (Full Access) │  (Summarized) │
                                                      ├─────────────────┼───────────────┤
┌──────────┐                                          │                 │               │
│   USER   │──┐                                   ┌──▶│ UB-DB (personal)│ UB-DB (total) │
└──────────┘  │                                   │   │                 │  [summarized] │
              │      ┌───────────────────────┐    │   ├─────────────────┼───────────────┤
              ├─────▶│     Query Router      │────┼──▶│Task DB (personal│Task DB (total)│
              │      │                       │    │   │                 │  [summarized] │
              │      │ • Breakdown           │    │   ├─────────────────┼───────────────┤
              │      │   (decomposes query)  │    │   │Ins DB (personal)│Ins DB (total) │
┌──────────┐  │      │                       │    │   │                 │  [summarized] │
│ MANAGER  │──┘      │ • Coordinator         │    │   ├─────────────────┼───────────────┤
│          │         │   (routes to sources) │    └──▶│  Best Practices │Best Practices │
│ Can also │         │                       │        │                 │               │
│ access:  │         │ • Synthesizer         │        └─────────────────┴───────────────┘
│ • Team   │         │   (combines results)  │
│   members│         └───────────────────────┘
│ • Team   │
│   totals │
└──────────┘
```

### 4.4 Access Control Matrix

| Requester | Own Data | Team Members | Team Total | Firm Total |
|-----------|----------|--------------|------------|------------|
| **User** | ✅ Full | ❌ No | ⚠️ Summarized | ⚠️ Summarized |
| **Manager** | ✅ Full | ✅ Full | ✅ Full | ⚠️ Summarized |

### 4.5 Query Router Components

| Component | Responsibility |
|-----------|----------------|
| **Breakdown** | Decomposes complex queries into sub-queries |
| **Coordinator** | Routes sub-queries to appropriate data sources |
| **Synthesizer** | Combines results from multiple sources into coherent response |

### 4.6 Query Examples

| Who | Query | Data Source | Response Type |
|-----|-------|-------------|---------------|
| User | "What tasks did I complete this week?" | Task DB (personal) | Full detail |
| User | "How does my productivity compare to the firm?" | Task DB (total) | Summarized ("top 25%") |
| User | "How is my team doing?" | Task DB (team total) | Summarized |
| Manager | "Show me Alex's overdue tasks" | Task DB (Alex's personal) | Full detail |
| Manager | "What's my team's completion rate?" | Task DB (team total) | Full aggregated |
| Manager | "How does my team compare to the firm?" | Task DB (firm total) | Summarized |

### 4.7 Sensitivity Handling

When accessing **team or firm-wide data**, the Query Router:
- Aggregates/anonymizes individual data
- Returns summaries, percentages, trends (not raw data)
- Examples:
  - ✅ "Average task completion: 85%"
  - ✅ "You completed 20% more tasks than average"
  - ❌ NOT "John completed 5 tasks, Sarah completed 12..."

### 4.8 MVP Scope Note

This process is intentionally **scoped as a foundation** for the spike. Future enhancements may include:
- More granular role-based access control
- Department-level views
- Audit logging of sensitive queries
- Permission management UI

---

## 5. Data Model

### 5.1 Databases Overview

| Database | Purpose | Key Data |
|----------|---------|----------|
| **Task DB** | Canonical store for all tasks | Tasks, status, priority, due dates, metadata |
| **User Behaviour DB** | Patterns and habits about user interactions | Behavioral observations, trends, flags |
| **Best Practices DB** | Organizational standards and guidelines | Rules, templates, benchmarks |
| **Insights DB** | Historical record of generated insights | All insights with timestamps, context |

### 5.2 Task DB Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Owner of the task |
| `title` | String | Task description |
| `status` | Enum | pending, in_progress, completed, cancelled |
| `priority` | Enum | low, medium, high, urgent |
| `due_date` | DateTime | When task is due |
| `category` | String | Task category/project |
| `created_at` | DateTime | When task was created |
| `updated_at` | DateTime | Last modification |
| `source_email_id` | String | Reference to originating email |
| `metadata` | JSON | Additional flexible data |

### 5.3 User Behaviour DB Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | User being tracked |
| `pattern_type` | String | Type of behavior (e.g., "missing_context", "late_logging") |
| `observation` | String | Description of the pattern |
| `frequency` | Integer | How often observed |
| `first_seen` | DateTime | When first noticed |
| `last_seen` | DateTime | Most recent occurrence |
| `is_active` | Boolean | Whether pattern is still relevant |

### 5.4 Best Practices DB Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `category` | String | Category (productivity, prioritization, etc.) |
| `rule` | String | The best practice rule |
| `description` | String | Detailed explanation |
| `benchmark` | JSON | Quantitative benchmarks if applicable |
| `is_active` | Boolean | Whether currently enforced |

### 5.5 Insights DB Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | User who received the insight |
| `insight_type` | String | Category of insight |
| `content` | String | The insight text |
| `context` | JSON | Data that drove the insight |
| `created_at` | DateTime | When generated |
| `was_actioned` | Boolean | Whether user acted on it (future) |

---

## 6. Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **AI/LLM** | Google Gemini 3.0 (Vertex AI) | Task extraction, insight generation, query understanding |
| **Orchestration** | LangGraph | Agent workflow management |
| **API** | FastAPI or Next.js API Routes | HTTP endpoints |
| **Database** | PostgreSQL (Cloud SQL) | All four databases |
| **Email** | Gmail API / IMAP+SMTP | Input and output channel |
| **Deployment** | Google Cloud Run | Containerized services |
| **Secrets** | Google Secret Manager | API keys, credentials |
| **Monitoring** | Cloud Logging & Monitoring | Observability |

---

## 7. Agent Architecture

### 7.1 LangGraph Node Structure

Each process is implemented as a LangGraph workflow with specialized nodes:

#### Process 1 Nodes (Optimized)

**Consolidated LLM Calls:** To minimize latency and cost, we combine multiple extraction steps into single LLM calls.

| Node | Input | Output | LLM Call? |
|------|-------|--------|-----------|
| `EmailIntakeNode` | Raw email | Normalized email object | No |
| `UnifiedExtractionNode` | Normalized email | Intent + JSON tasks + context flags + entities | **Yes (1 call)** |
| `BehaviorAnalyzerNode` | User interaction history | Meta-behavior observations | **Yes** |
| `BehaviorPersistNode` | Observations | Stored to User Behaviour DB | No |
| `TaskComparisonNode` | JSON tasks + DB tasks | Diff (add/update list) | No |
| `TaskPersistNode` | Diff | Updated Task DB | No |
| `PresenterNode` | Task DB state | Email response | Yes |

**UnifiedExtractionNode** combines what was previously 3-4 separate calls:
- Intent classification (activity/correction/context/query)
- Task extraction from free-form text
- JSON transformation to uniform schema
- Missing context detection
- Entity extraction (dates, people, projects)
- Recurring signal detection

**Single Prompt Output:**
```json
{
  "intent": "activity",
  "tasks": [{"title": "...", "due_date": "...", "priority": "..."}],
  "missing_context": [],
  "is_recurring_signal": false,
  "detected_entities": {"dates": [], "people": [], "projects": []}
}
```

**Performance Comparison:**
| Metric | Before (4 calls) | After (1 call) | Improvement |
|--------|------------------|----------------|-------------|
| LLM calls | 4 | 1 | 75% fewer |
| Latency | ~8s | ~2-3s | 60% faster |
| Token cost | 4x | 1x | 75% cheaper |

#### Process 2 Nodes
| Node | Input | Output | LLM Call? |
|------|-------|--------|-----------|
| `TaskFetchNode` | User ID | Current tasks | No |
| `PrioritizerNode` | Tasks | Prioritized list | Yes |
| `BestPracticesFetchNode` | Category | Relevant practices | No |
| `InsightGeneratorNode` | Tasks + Practices | Insights | Yes |
| `InsightPersistNode` | Insights | Stored to Insights DB | No |
| `EmailComposerNode` | Priorities + Insights | Combined email | No |

#### Process 3 Nodes (Optimized)

| Node | Input | Output | LLM Call? |
|------|-------|--------|-----------|
| `QueryParserNode` | Natural language query | Parsed query + sub-queries | **Yes (1 call)** |
| `AccessControlNode` | User + Query | Allowed data scopes | No |
| `CoordinatorNode` | Sub-queries + Scopes | Routed queries | No |
| `DataFetchNode` | Routed queries | Raw results | No |
| `ResponseGeneratorNode` | Raw results + Privacy rules | Summarized + synthesized response | **Yes (1 call)** |

**Consolidation:** Reduced from 4 LLM calls to 2:
- `QueryIntakeNode` + `BreakdownNode` → `QueryParserNode`
- `SummarizerNode` + `SynthesizerNode` → `ResponseGeneratorNode`

---

## 8. Prompt Specifications

This section defines the prompt structure for each LLM-calling node. These are the "contracts" that the Gemini model must fulfill.

### 8.1 UnifiedExtractionNode (Process 1)

**Purpose:** Single call to classify intent, extract tasks, transform to JSON, detect missing context, and identify entities.

**Temperature:** 0.3 (conservative for structured output)

**Input:**
```
Email from: {sender_email}
Subject: {subject}
Body:
{email_body}
```

**Prompt Structure:**
```
You are an AI task management assistant. Analyze this email and extract all relevant information.

EMAIL:
From: {sender_email}
Subject: {subject}
Body: {email_body}

INSTRUCTIONS:
1. Classify the PRIMARY intent of this email
2. Extract all tasks mentioned (activities, completions, todos)
3. Convert each task to structured JSON
4. Identify any missing information that needs clarification
5. Detect entities (dates, people, projects)
6. Check for recurring activity signals ("daily", "weekly", "standup", etc.)

RETURN THIS EXACT JSON STRUCTURE:
{
  "intent": "activity" | "correction" | "context_reply" | "query",
  "tasks": [
    {
      "title": "string (required)",
      "description": "string or null",
      "due_date": "YYYY-MM-DD or null",
      "priority": "high" | "medium" | "low",
      "status": "pending" | "in_progress" | "completed",
      "category": "string or null",
      "raw_text": "original text from email"
    }
  ],
  "corrections": [
    {
      "original_task_hint": "what task to correct",
      "field_to_update": "due_date" | "priority" | "status" | "title",
      "new_value": "the corrected value"
    }
  ],
  "missing_context": [
    "Question to ask user if info is missing"
  ],
  "detected_entities": {
    "dates": ["list of dates mentioned"],
    "people": ["list of people mentioned"],
    "projects": ["list of projects mentioned"]
  },
  "is_recurring_signal": true | false,
  "recurring_frequency_hint": "daily" | "weekly" | "monthly" | null
}

RULES:
- If intent is "query", tasks array should be empty
- Always preserve the raw_text for each task
- Infer priority from language: "urgent", "ASAP", "!!!" = high
- Infer dates: "tomorrow" = next day, "next week" = 7 days, etc.
- If unsure about a field, use null
```

**Example Input:**
```
From: john@company.com
Subject: Today's update
Body: Today I finished the quarterly report (finally!) and had my daily standup 
with the Acme team. Tomorrow I need to send 5 follow-up emails to clients - 
this is urgent! Also, I said the budget review was due Wednesday but it's 
actually Thursday.
```

**Example Output:**
```json
{
  "intent": "activity",
  "tasks": [
    {
      "title": "Finished quarterly report",
      "description": null,
      "due_date": null,
      "priority": "medium",
      "status": "completed",
      "category": null,
      "raw_text": "finished the quarterly report (finally!)"
    },
    {
      "title": "Daily standup with Acme team",
      "description": null,
      "due_date": "2025-12-23",
      "priority": "medium",
      "status": "completed",
      "category": "Acme",
      "raw_text": "had my daily standup with the Acme team"
    },
    {
      "title": "Send follow-up emails to clients",
      "description": "5 clients",
      "due_date": "2025-12-24",
      "priority": "high",
      "status": "pending",
      "category": null,
      "raw_text": "send 5 follow-up emails to clients - this is urgent!"
    }
  ],
  "corrections": [
    {
      "original_task_hint": "budget review",
      "field_to_update": "due_date",
      "new_value": "Thursday"
    }
  ],
  "missing_context": [],
  "detected_entities": {
    "dates": ["today", "tomorrow", "Wednesday", "Thursday"],
    "people": [],
    "projects": ["Acme"]
  },
  "is_recurring_signal": true,
  "recurring_frequency_hint": "daily"
}
```

---

### 8.2 BehaviorAnalyzerNode (Process 1)

**Purpose:** Analyze user interaction patterns and generate meta-observations.

**Temperature:** 0.5 (moderate creativity for insights)

**Input:**
```
User: {user_email}
Recent interactions: {last_N_interactions}
Current extraction: {current_extraction_result}
Existing patterns: {existing_patterns_from_db}
```

**Prompt Structure:**
```
You are analyzing user behavior patterns for a task management system.

USER: {user_email}
RECENT INTERACTIONS (last 20):
{interactions_summary}

CURRENT EXTRACTION:
{current_extraction}

EXISTING PATTERNS WE'VE DETECTED:
{existing_patterns}

ANALYZE and identify NEW or REINFORCED patterns. Consider:
- Do they frequently omit due dates?
- Do they often need context clarification?
- Do they correct tasks shortly after submitting?
- Are they consistent with recurring activities?
- Do they use vague language often?

RETURN JSON:
{
  "new_patterns": [
    {
      "pattern_type": "missing_due_dates" | "needs_context" | "frequent_corrections" | etc,
      "observation": "Human-readable observation",
      "confidence": 0.0-1.0,
      "evidence": "What led to this conclusion"
    }
  ],
  "reinforced_patterns": [
    {
      "pattern_id": "existing pattern ID",
      "additional_evidence": "new supporting evidence"
    }
  ]
}
```

---

### 8.3 PrioritizerNode (Process 2)

**Purpose:** Generate prioritized task list for the next day.

**Temperature:** 0.3 (structured output)

**Prompt Structure:**
```
You are a productivity coach helping prioritize tasks for tomorrow.

USER'S OPEN TASKS:
{tasks_json}

TODAY'S DATE: {today}
USER'S PATTERNS: {relevant_behavior_patterns}

Generate a prioritized list for tomorrow. Consider:
1. Due dates (overdue first, then tomorrow, then this week)
2. Priority flags (high > medium > low)
3. User's patterns (if they often miss deadlines, emphasize those)
4. Realistic daily capacity (5-7 focus tasks)

RETURN JSON:
{
  "priority_tasks": [
    {
      "task_id": "uuid",
      "title": "task title",
      "reason": "Why this is prioritized",
      "suggested_time": "morning" | "afternoon" | "anytime"
    }
  ],
  "deferred_tasks": [
    {
      "task_id": "uuid",
      "reason": "Why this can wait"
    }
  ],
  "warnings": [
    "Any urgent warnings (overdue, capacity exceeded, etc.)"
  ]
}
```

---

### 8.4 InsightGeneratorNode (Process 2)

**Purpose:** Generate personalized productivity insights.

**Temperature:** 0.6 (creative but grounded)

**Prompt Structure:**
```
You are a supportive productivity coach generating insights.

USER'S TASK DATA:
{task_summary}

BEST PRACTICES TO COMPARE AGAINST:
{best_practices}

USER'S BEHAVIOR PATTERNS:
{behavior_patterns}

MISSED RECURRING ACTIVITIES:
{missed_recurring}

Generate 2-4 actionable insights. Be:
- Supportive, not critical
- Specific, not generic
- Actionable, not just observational

RETURN JSON:
{
  "insights": [
    {
      "type": "celebration" | "improvement" | "reminder" | "warning",
      "message": "The insight message",
      "action": "Specific action they can take",
      "related_practice_id": "uuid or null"
    }
  ]
}
```

---

### 8.5 QueryParserNode (Process 3)

**Purpose:** Parse natural language query and decompose into sub-queries.

**Temperature:** 0.3 (structured)

**Prompt Structure:**
```
You are parsing a user's query about their task data.

USER: {user_email}
USER ROLE: {role: user | manager}
QUERY: "{query_text}"

Parse this query and decompose if needed.

RETURN JSON:
{
  "query_type": "personal" | "team" | "comparison" | "aggregate",
  "time_range": {
    "start": "YYYY-MM-DD or null",
    "end": "YYYY-MM-DD or null",
    "relative": "today" | "this_week" | "this_month" | null
  },
  "sub_queries": [
    {
      "target_db": "tasks" | "insights" | "behaviors" | "best_practices",
      "filter": "description of what to fetch",
      "aggregation": "count" | "list" | "average" | null
    }
  ],
  "requires_summarization": true | false,
  "original_intent": "What the user wants to know"
}
```

---

### 8.6 ResponseGeneratorNode (Process 3)

**Purpose:** Synthesize data into natural language response with privacy rules.

**Temperature:** 0.5 (conversational)

**Prompt Structure:**
```
Generate a response to the user's query.

ORIGINAL QUERY: "{query}"
USER ROLE: {role}
DATA RESULTS:
{raw_results}

PRIVACY RULES:
- If data is about OTHER users and role is "user", summarize only
- Never expose individual names when summarizing team/firm data
- Use percentages and aggregates for protected data

Generate a helpful, conversational response.

RETURN JSON:
{
  "response": "The natural language response",
  "data_displayed": "personal" | "summarized" | "aggregate",
  "follow_up_suggestion": "Optional follow-up question" 
}
```

---

### 8.7 Temperature Guidelines

| Temperature | Use Case | Nodes |
|-------------|----------|-------|
| **0.3** | Structured extraction, parsing | UnifiedExtraction, QueryParser |
| **0.5** | Balanced creativity/structure | BehaviorAnalyzer, ResponseGenerator |
| **0.6** | Creative insights | InsightGenerator |

---

### 8.8 Prompt Engineering Best Practices

1. **Always request JSON** - Structured output is easier to parse
2. **Provide examples** - Few-shot prompts improve accuracy
3. **Set boundaries** - Clear rules prevent hallucination
4. **Include context** - User patterns, date, role
5. **Handle edge cases** - What to return if no tasks, no matches, etc.

---

## 9. Integration Points & Future Extensions

| Integration | Description | Priority |
|-------------|-------------|----------|
| **Gmail Intake** | Process incoming emails automatically | MVP |
| **Email Output** | Send summaries, priorities, insights | MVP |
| **Notion Sync** | Bidirectional sync with Notion databases | Post-MVP |
| **Slack Integration** | Query via Slack, receive alerts | Future |
| **Calendar Integration** | Consider calendar when prioritizing | Future |
| **Team Dashboard** | Manager UI for team oversight | Future |

---

## 10. Observability & Resilience

### 10.1 Logging Strategy
- Every LangGraph node logs entry/exit with run ID
- LLM calls log prompt hash, latency, token count
- Email operations log message IDs for traceability

### 10.2 Error Handling
- Failed extractions trigger context requests (not silent failures)
- Database errors trigger retries with exponential backoff
- Unrecoverable errors logged with full state for replay

### 10.3 Metrics
- Task extraction accuracy (manual review sampling)
- End-to-end latency per process
- User engagement with insights (future)

---

## 11. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Google Cloud Platform                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Cloud Run    │    │ Cloud Run    │    │ Cloud Run    │       │
│  │ Process 1    │    │ Process 2    │    │ Process 3    │       │
│  │ (Intake)     │    │ (Priority)   │    │ (Query)      │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │   Cloud SQL     │                          │
│                    │   (PostgreSQL)  │                          │
│                    │                 │                          │
│                    │ • Task DB       │                          │
│                    │ • User Behav DB │                          │
│                    │ • Insights DB   │                          │
│                    │ • Best Prac DB  │                          │
│                    └─────────────────┘                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Cloud        │    │ Secret       │    │ Cloud        │       │
│  │ Scheduler    │    │ Manager      │    │ Logging      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Next Implementation Steps

1. **Set up repository** with process-based folder structure
2. **Implement Process 1** (Task Intake) as MVP core
3. **Create database schemas** for all four databases
4. **Implement Process 2** (Prioritization & Insights)
5. **Implement Process 3** (Query System) - foundation only
6. **Add email integration** (Gmail IMAP/SMTP)
7. **Deploy to Cloud Run** with basic monitoring
8. **Document learnings** and comparison with current system

---

## 13. MVP Operational Considerations

### 13.1 User Authentication (Simple)

For MVP, use a simple `users` table lookup:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',  -- 'user' or 'manager'
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Authentication Flow:**
1. Email arrives → extract sender address
2. Lookup in `users` table
3. If found → proceed with user_id
4. If not found → reply with "Please register" or auto-create (configurable)

> **Note:** Full JWT/OAuth authentication is deferred to Phase 1 (see SPIKE_ROADMAP.md)

### 13.2 Error Handling

| Failure | Handling | User Impact |
|---------|----------|-------------|
| **Gemini API down** | Retry 3x with exponential backoff, then queue for later | Delayed response |
| **Gemini returns malformed JSON** | Fallback prompt or flag for manual review | Generic acknowledgment |
| **Task DB unavailable** | Queue email, alert operator, retry on recovery | Delayed processing |
| **Email send fails** | Retry 3x, log failure, alert operator | User doesn't receive response |
| **Unknown error** | Log full state, send generic "processing delayed" response | Graceful degradation |

### 13.3 Cost Controls

| Control | Implementation |
|---------|----------------|
| **Daily budget alert** | Alert if LLM costs exceed $X/day |
| **Rate limiting** | 50 emails/user/day for MVP |
| **Email truncation** | Truncate emails >10K characters |
| **Token monitoring** | Log token usage per process for analysis |

### 13.4 Assumptions & Constraints

| Assumption | Notes |
|------------|-------|
| **Single timezone** | All times in UTC or configured timezone; per-user timezones deferred to Phase 1 |
| **English-only** | Gemini handles other languages, but not formally tested |
| **Email attachments** | Ignored for MVP; logged for future processing |
| **Process 3 read-only** | Queries are read-only; mutations (corrections, updates) go through Process 1 |
| **Empty state handling** | P2 with 0 tasks sends "No tasks to prioritize - time to add some!" |

---

## 14. Summary

This architecture defines three interconnected processes:

| Process | Purpose | Key Innovation |
|---------|---------|----------------|
| **1. Task Intake** | Get tasks from email, process, store | User behavior tracking, intelligent comparison |
| **2. Prioritization & Insights** | Daily priorities + improvement advice | Best practices comparison, combined output |
| **3. Query System** | Natural language data access | Role-based access, privacy-aware summarization |

Together, these processes create an intelligent task management agent that not only tracks tasks but actively helps users improve their productivity through personalized insights and easy data access.
