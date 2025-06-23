# Gemini Prompts Audit

This document provides a comprehensive audit of all places in the codebase where prompts are being sent to Gemini AI.

## Summary

**Total Gemini API Calls Found: 8 locations**
- **Active/Used**: 6 locations
- **Test/Unused**: 2 locations

## 1. Task Extraction (ACTIVE)

**File**: `core/task_extractor.py`
**Function**: `extract_tasks_from_update()`
**Line**: 179
**Purpose**: Extract structured tasks from freeform text with vague task detection

**Prompt Length**: ~95 lines (comprehensive)
**Key Features**:
- Vague task detection with suggested questions
- Status determination (Completed/In Progress/Pending/Blocked)
- Date extraction and standardization
- Category assignment
- Employee identification

**Temperature**: 0.3

---

## 2. Coaching Insights (ACTIVE)

**File**: `core/ai/insights.py`
**Function**: `get_coaching_insight()`
**Line**: 119
**Purpose**: Generate personalized coaching insights for individual users

**Prompt Length**: ~25 lines
**Key Features**:
- Analyzes task completion patterns
- Identifies strengths and areas for improvement
- Provides tactical suggestions
- Conversational, supportive tone

**Temperature**: 0.4

---

## 3. Project Insights (ACTIVE)

**File**: `core/ai/insights.py`
**Function**: `get_project_insight()`
**Line**: 235
**Purpose**: Generate strategic project analysis and recommendations

**Prompt Length**: ~30 lines
**Key Features**:
- Project health assessment
- Risk identification
- Strategic recommendations
- Data-driven analysis

**Temperature**: 0.5

---

## 4. Task Analysis (ACTIVE)

**File**: `core/ai/analyzers.py`
**Function**: `TaskAnalyzer._create_insights_prompt()`
**Line**: 174
**Purpose**: Generate productivity insights and recommendations

**Prompt Length**: ~25 lines
**Key Features**:
- Workload summary
- Productivity insights
- Actionable recommendations
- Task prioritization analysis

**Temperature**: 0.7 (via `generate_text()`)

---

## 5. Project Analysis (ACTIVE)

**File**: `core/ai/analyzers.py`
**Function**: `ProjectAnalyzer._create_project_prompt()`
**Line**: 340
**Purpose**: Generate project health analysis and strategic insights

**Prompt Length**: ~35 lines
**Key Features**:
- Project metrics calculation
- Bottleneck identification
- Health status assessment
- Strategic recommendations

**Temperature**: 0.7 (via `generate_text()`)

---

## 6. Task Verification (ACTIVE)

**File**: `core/chat/verification.py`
**Function**: `extract_task_info_from_response()`
**Line**: 82
**Purpose**: Extract detailed task information from user responses

**Prompt Length**: ~15 lines
**Key Features**:
- Parses user responses about vague tasks
- Extracts task description, category, and status
- JSON format output
- Uses original task as fallback

**Temperature**: 0.3

---

## 7. Combined Coaching Insights (ACTIVE)

**File**: `core/chat/verification.py`
**Function**: `generate_combined_coaching_insights()`
**Line**: 270
**Purpose**: Generate both coaching insights and task verification in one call

**Prompt Length**: ~40 lines
**Key Features**:
- Dual analysis (coaching + verification)
- JSON structured output
- Personal language requirements
- Conversational tone

**Temperature**: 0.4

---

## 8. Generic AI Response (ACTIVE)

**File**: `core/ai/analyzers.py`
**Function**: `get_ai_response()`
**Line**: 421
**Purpose**: Generic AI response function for custom prompts

**Prompt Length**: Variable (user-provided)
**Key Features**:
- Generic wrapper function
- Error handling
- Temperature: 0.3

---

## Test Files (NOT ACTIVE)

### Test Integration
**File**: `test_gemini_integration.py`
**Purpose**: Testing Gemini connectivity
**Prompt**: Simple "Hello" test

### Test Task Extraction
**File**: `tests/task_extraction/test_task_extraction.py`
**Purpose**: Unit testing task extraction
**Prompt**: Test task extraction functionality

---

## Prompt Complexity Analysis

### Most Complex Prompts:
1. **Task Extraction** (95+ lines) - Most comprehensive
2. **Combined Coaching Insights** (40 lines) - Dual purpose
3. **Project Analysis** (35 lines) - Strategic focus

### Simplest Prompts:
1. **Generic AI Response** - Variable length
2. **Task Verification** (15 lines) - Focused extraction
3. **Coaching Insights** (25 lines) - Conversational

## Temperature Settings

- **0.3**: Task extraction, verification, generic responses (most conservative)
- **0.4**: Coaching insights, combined insights (balanced)
- **0.5**: Project insights (slightly creative)
- **0.7**: Task analysis, project analysis (most creative)

## Recommendations

1. **Consistency**: Consider standardizing temperature settings across similar functions
2. **Prompt Optimization**: The task extraction prompt could potentially be optimized for better performance
3. **Error Handling**: All prompts have good error handling with fallbacks
4. **Security**: Project protection is implemented in coaching and project insights

## Usage Patterns

- **Most Frequent**: Task extraction (primary user interaction)
- **Strategic**: Project analysis and coaching insights
- **Supportive**: Task verification and combined insights
- **Generic**: Flexible AI response function

All prompts are actively used in the application and contribute to the core AI functionality of the task management system. 