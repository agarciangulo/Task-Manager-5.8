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
| **Check Completeness** | Verify tasks have required info (due date, priority, etc.) |
| **Request Context** | Send email back to user if information is missing |
| **Trigger Behavior Analysis** | Pass interaction data to Behavior Analyzer for pattern detection |

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
| **Compare & Decide** | Determine which tasks are NEW (add) vs existing (update) |
| **Apply Corrections** | Process correction requests from user |
| **Update Database** | Write final state to Task DB |

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
| **AI/LLM** | Google Gemini (Vertex AI) | Task extraction, insight generation, query understanding |
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

#### Process 1 Nodes
| Node | Input | Output | LLM Call? |
|------|-------|--------|-----------|
| `EmailIntakeNode` | Raw email | Normalized email object | No |
| `IntentClassifierNode` | Normalized email | Intent (activity/correction/context) | Yes |
| `TaskExtractorNode` | Email + Intent | Extracted tasks | Yes |
| `ContextCheckerNode` | Extracted tasks | Tasks or clarification questions | Yes |
| `BehaviorAnalyzerNode` | User interaction history | Meta-behavior observations | **Yes** |
| `BehaviorPersistNode` | Observations | Stored to User Behaviour DB | No |
| `TaskComparisonNode` | New tasks + DB tasks | Diff (add/update list) | No |
| `TaskPersistNode` | Diff | Updated Task DB | No |
| `PresenterNode` | Task DB state | Email response | Yes |

#### Process 2 Nodes
| Node | Input | Output | LLM Call? |
|------|-------|--------|-----------|
| `TaskFetchNode` | User ID | Current tasks | No |
| `PrioritizerNode` | Tasks | Prioritized list | Yes |
| `BestPracticesFetchNode` | Category | Relevant practices | No |
| `InsightGeneratorNode` | Tasks + Practices | Insights | Yes |
| `InsightPersistNode` | Insights | Stored to Insights DB | No |
| `EmailComposerNode` | Priorities + Insights | Combined email | No |

#### Process 3 Nodes
| Node | Input | Output | LLM Call? |
|------|-------|--------|-----------|
| `QueryIntakeNode` | Natural language query | Parsed query | Yes |
| `BreakdownNode` | Parsed query | Sub-queries | Yes |
| `AccessControlNode` | User + Query | Allowed data scopes | No |
| `CoordinatorNode` | Sub-queries + Scopes | Routed queries | No |
| `DataFetchNode` | Routed queries | Raw results | No |
| `SummarizerNode` | Raw results + Privacy rules | Summarized if needed | Yes |
| `SynthesizerNode` | All results | Combined response | Yes |

---

## 8. Integration Points & Future Extensions

| Integration | Description | Priority |
|-------------|-------------|----------|
| **Gmail Intake** | Process incoming emails automatically | MVP |
| **Email Output** | Send summaries, priorities, insights | MVP |
| **Notion Sync** | Bidirectional sync with Notion databases | Post-MVP |
| **Slack Integration** | Query via Slack, receive alerts | Future |
| **Calendar Integration** | Consider calendar when prioritizing | Future |
| **Team Dashboard** | Manager UI for team oversight | Future |

---

## 9. Observability & Resilience

### 9.1 Logging Strategy
- Every LangGraph node logs entry/exit with run ID
- LLM calls log prompt hash, latency, token count
- Email operations log message IDs for traceability

### 9.2 Error Handling
- Failed extractions trigger context requests (not silent failures)
- Database errors trigger retries with exponential backoff
- Unrecoverable errors logged with full state for replay

### 9.3 Metrics
- Task extraction accuracy (manual review sampling)
- End-to-end latency per process
- User engagement with insights (future)

---

## 10. Deployment Architecture

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

## 11. Next Implementation Steps

1. **Set up repository** with process-based folder structure
2. **Implement Process 1** (Task Intake) as MVP core
3. **Create database schemas** for all four databases
4. **Implement Process 2** (Prioritization & Insights)
5. **Implement Process 3** (Query System) - foundation only
6. **Add email integration** (Gmail IMAP/SMTP)
7. **Deploy to Cloud Run** with basic monitoring
8. **Document learnings** and comparison with current system

---

## 12. Summary

This architecture defines three interconnected processes:

| Process | Purpose | Key Innovation |
|---------|---------|----------------|
| **1. Task Intake** | Get tasks from email, process, store | User behavior tracking, intelligent comparison |
| **2. Prioritization & Insights** | Daily priorities + improvement advice | Best practices comparison, combined output |
| **3. Query System** | Natural language data access | Role-based access, privacy-aware summarization |

Together, these processes create an intelligent task management agent that not only tracks tasks but actively helps users improve their productivity through personalized insights and easy data access.
