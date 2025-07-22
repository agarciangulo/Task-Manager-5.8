"""
RAG-Enhanced AI Insights for Task Manager.

This module enhances the existing insights generator with RAG-powered guideline awareness.
It integrates knowledge from guideline documents to provide more authoritative and 
company-specific coaching insights.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import json
import os

from src.config.settings import (
    AI_PROVIDER,
    CHAT_MODEL,
    DEBUG_MODE,
    MIN_TASK_LENGTH
)

# Import security plugin for protecting sensitive data
from src.plugins import plugin_manager

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def get_guideline_context_for_coaching(person_name: str, tasks: List[Dict[str, Any]], recent_tasks: pd.DataFrame) -> str:
    """
    Get relevant guideline context for coaching insights.
    
    Args:
        person_name: Name of the person to analyze
        tasks: Current tasks
        recent_tasks: Recent task history
        
    Returns:
        str: Relevant guideline context for coaching
    """
    try:
        from src.core.knowledge.knowledge_base import KnowledgeBase
        
        # Analyze patterns to determine relevant guidelines
        guideline_queries = []
        
        # Check for email response patterns
        email_tasks = [task for task in tasks if any(keyword in task.get('task', '').lower() 
                                                   for keyword in ['email', 'response', 'reply', 'follow up'])]
        if email_tasks:
            # Check for overdue emails (more than 2 business days)
            current_date = datetime.now()
            overdue_emails = []
            for task in email_tasks:
                task_date = task.get('date')
                if task_date:
                    if isinstance(task_date, str):
                        try:
                            task_date = datetime.strptime(task_date, '%Y-%m-%d')
                        except:
                            continue
                    
                    # Calculate business days (simplified)
                    days_diff = (current_date - task_date).days
                    if days_diff > 2:  # More than 2 business days
                        overdue_emails.append(task)
            
            if overdue_emails:
                guideline_queries.append("email response time guidelines business days")
        
        # Check for project management patterns
        project_tasks = [task for task in tasks if any(keyword in task.get('task', '').lower() 
                                                     for keyword in ['project', 'deliverable', 'milestone', 'deadline'])]
        if project_tasks:
            guideline_queries.append("project management timeline guidelines")
        
        # Check for security-related tasks
        security_tasks = [task for task in tasks if any(keyword in task.get('task', '').lower() 
                                                      for keyword in ['security', 'vulnerability', 'patch', 'compliance'])]
        if security_tasks:
            guideline_queries.append("security incident response guidelines")
        
        # Check for code quality patterns
        code_tasks = [task for task in tasks if any(keyword in task.get('task', '').lower() 
                                                  for keyword in ['code', 'review', 'testing', 'deployment'])]
        if code_tasks:
            guideline_queries.append("code quality standards review guidelines")
        
        # Get guideline context for relevant queries
        kb = KnowledgeBase(name="guidelines")
        all_context = []
        
        for query in guideline_queries:
            chunks = kb.query_guidelines(query, top_k=2)
            if chunks:
                all_context.extend(chunks)
        
        if all_context:
            return "\n\n---\n\n".join(all_context)
        else:
            return "No specific guidelines found for current patterns."
            
    except Exception as e:
        debug_print(f"Error getting guideline context: {e}")
        return "Unable to retrieve guideline context."

def get_rag_enhanced_coaching_insight(person_name: str, tasks: List[Dict[str, Any]], recent_tasks: pd.DataFrame, peer_feedback: List[Dict[str, Any]]) -> str:
    """
    Generate RAG-enhanced coaching insights with guideline awareness.
    
    This enhanced version incorporates knowledge from guideline documents to provide
    more authoritative and company-specific coaching recommendations.
    
    Args:
        person_name: Name of the person to analyze.
        tasks: Current tasks.
        recent_tasks: Recent task history.
        peer_feedback: Peer feedback entries.
        
    Returns:
        str: RAG-enhanced coaching insights.
    """
    # Get the project protection plugin if available
    protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
    use_protection = protection_plugin and protection_plugin.enabled
    
    # Calculate basic statistics for the AI
    basic_stats = {}
    try:
        if not recent_tasks.empty:
            completed_tasks = recent_tasks[recent_tasks['status'] == 'Completed']
            basic_stats = {
                "total_tasks": len(recent_tasks),
                "completed_tasks": len(completed_tasks),
                "completion_rate": f"{len(completed_tasks) / len(recent_tasks):.1%}" if len(recent_tasks) > 0 else "0%",
                "category_counts": recent_tasks['category'].value_counts().to_dict(),
                "date_range": (recent_tasks['date'].max() - recent_tasks['date'].min()).days + 1 if not recent_tasks.empty else 0
            }
    except Exception as e:
        debug_print(f"Error calculating statistics: {e}")
        basic_stats = {"error": str(e)}
    
    # Protect sensitive information if needed
    protected_tasks = tasks
    protected_stats = basic_stats
    protected_feedback = peer_feedback
    
    if use_protection:
        try:
            # Protect tasks
            protected_tasks = protection_plugin.protect_task_list(tasks)
            
            # Protect category counts in stats
            if "category_counts" in protected_stats:
                protected_counts = {}
                for category, count in protected_stats["category_counts"].items():
                    protected_category = protection_plugin.security_manager.tokenize_project(category)
                    protected_counts[protected_category] = count
                protected_stats["category_counts"] = protected_counts
            
            # Feedback doesn't need protection as it doesn't contain project names
        except Exception as e:
            debug_print(f"Error protecting data: {e}")
            # Continue with unprotected data if protection fails

    # Get relevant guideline context
    guideline_context = get_guideline_context_for_coaching(person_name, tasks, recent_tasks)

    # Enhanced prompt with RAG context
    feedback_prompt = f"""
    You are CoachAI, a friendly and helpful workplace assistant who offers coaching insights in a conversational, supportive tone. You have access to our company's internal guidelines and best practices.

    ANALYZE THE FOLLOWING DATA FOR {person_name}:
    1. Current tasks: {protected_tasks}
    2. Task history (14 days): {recent_tasks[['task', 'status', 'employee', 'date', 'category']].to_dict(orient='records') if not recent_tasks.empty else []}
    3. Basic statistics: {protected_stats}
    4. Peer feedback: {protected_feedback}

    RELEVANT COMPANY GUIDELINES:
    {guideline_context}

    FIRST, ANALYZE THIS DATA TO IDENTIFY PATTERNS:
    - Task completion rates and patterns
    - Work distribution across different projects
    - Recent productivity trends
    - Task complexity and priority handling
    - Collaboration patterns
    - Compliance with company guidelines and best practices

    THEN, PROVIDE INSIGHTS ON THE ANALYSIS IN A CONVERSATIONAL TONE, INCLUDING:
    1. A specific strength or accomplishment to recognize
    2. Specific instances that require their immediate attention (especially if they violate guidelines)
    3. A friendly, practical, and tactical suggestion that could help them improve
    4. Reference to relevant company guidelines when applicable

    IMPORTANT STYLE GUIDANCE:
    - Write as a helpful colleague, not a formal report
    - Use personal language ("I notice...", "You're doing well at...")
    - Keep it brief and conversational (3-4 sentences per insight)
    - Avoid technical terms like "metadata analysis" or "velocity metrics"
    - Don't list categories like "STRENGTH:" or "OPPORTUNITY:" - just flow naturally
    - Sound encouraging and supportive throughout
    - When referencing guidelines, be helpful and educational, not punitive
    """

    try:
        from src.core.ai_client import call_ai_api
        
        # Use the unified AI client
        ai_response = call_ai_api(feedback_prompt)
        
        # Unprotect any project tokens in the insights if needed
        if use_protection:
            try:
                ai_response = protection_plugin.unprotect_text(ai_response)
            except Exception as e:
                debug_print(f"Error unprotecting insights: {e}")
            
        return ai_response
    except Exception as e:
        debug_print(f"Error generating RAG-enhanced coaching insights: {e}")
        return "Unable to generate coaching insights at this time."

def get_rag_enhanced_project_insight(selected_category: str, filtered_tasks: pd.DataFrame) -> str:
    """
    Generate RAG-enhanced project insights with guideline awareness.
    
    Args:
        selected_category: Category/project to analyze.
        filtered_tasks: Tasks filtered for this category.
        
    Returns:
        str: RAG-enhanced project insights.
    """
    # Get the project protection plugin if available
    protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
    use_protection = protection_plugin and protection_plugin.enabled
    
    # Calculate basic statistics for the AI
    basic_stats = {}
    try:
        if not filtered_tasks.empty:
            # Calculate date range
            if 'date' in filtered_tasks.columns and not filtered_tasks['date'].isna().all():
                date_range = (filtered_tasks['date'].max() - filtered_tasks['date'].min()).days + 1
            else:
                date_range = 0

            # Calculate team distribution
            team_counts = filtered_tasks['employee'].value_counts().to_dict()

            basic_stats = {
                "total_tasks": len(filtered_tasks),
                "status_counts": filtered_tasks['status'].value_counts().to_dict(),
                "team_distribution": team_counts,
                "date_range": date_range
            }
    except Exception as e:
        debug_print(f"Error calculating project stats: {e}")
        basic_stats = {"error": str(e)}
    
    # Protect sensitive information if needed
    protected_category = selected_category
    protected_tasks = filtered_tasks
    
    if use_protection:
        try:
            # Protect the category name
            protected_category = protection_plugin.security_manager.tokenize_project(selected_category)
            
            # Convert DataFrame to list of dicts for protection
            tasks_list = []
            for _, row in filtered_tasks.iterrows():
                task_dict = row.to_dict()
                # Ensure 'task' key exists for compatibility with protect_task_data
                if 'task' not in task_dict and 'Task' in task_dict:
                    task_dict['task'] = task_dict['Task']
                tasks_list.append(task_dict)
            
            # Protect each task
            protected_tasks_list = protection_plugin.protect_task_list(tasks_list)
            
            # Convert back to DataFrame if needed
            # For simplicity, we'll just use the list for the prompt
        except Exception as e:
            debug_print(f"Error protecting project data: {e}")
            # Continue with unprotected data if protection fails
            protected_tasks_list = tasks_list

    # Get relevant guideline context for project management
    try:
        from src.core.knowledge.knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(name="guidelines")
        project_guidelines = kb.query_guidelines("project management timeline guidelines", top_k=3)
        deployment_guidelines = kb.query_guidelines("deployment procedures guidelines", top_k=2)
        
        guideline_context = ""
        if project_guidelines:
            guideline_context += "\n\nPROJECT MANAGEMENT GUIDELINES:\n" + "\n\n---\n\n".join(project_guidelines)
        if deployment_guidelines:
            guideline_context += "\n\nDEPLOYMENT GUIDELINES:\n" + "\n\n---\n\n".join(deployment_guidelines)
            
    except Exception as e:
        debug_print(f"Error getting project guidelines: {e}")
        guideline_context = ""

    # Enhanced AI-generated insight with RAG context
    project_prompt = f"""
    You are ProjectAnalyst, a strategic advisor on project management and team productivity with access to company guidelines.

    ANALYZE PROJECT '{protected_category}' TASKS:
    {protected_tasks_list if use_protection else filtered_tasks[['task', 'status', 'employee', 'date']].to_dict(orient='records')}

    PROJECT METADATA:
    {basic_stats}

    RELEVANT COMPANY GUIDELINES:
    {guideline_context}

    FIRST, PERFORM A METADATA ANALYSIS ON THE PROJECT:
    - Calculate key project metrics: completion rate, velocity, team distribution
    - Identify how many tasks have been open for more than 7 days
    - Analyze distribution of task ages
    - Determine if certain team members have disproportionate workloads
    - Identify any bottlenecks or common blockers
    - Determine if task completion is on pace with creation
    - Check compliance with company guidelines and best practices

    THEN, PROVIDE A THREE-PART INSIGHT:
    1. HEALTH STATUS: One sentence on overall project health
    2. KEY RISK: The most critical item requiring attention
    3. STRATEGIC RECOMMENDATION: One specific action to improve project health (reference guidelines when applicable)

    Keep your response focused, data-driven, and immediately actionable.
    """

    try:
        from src.core.ai_client import call_ai_api
        
        # Use the unified AI client
        ai_response = call_ai_api(project_prompt)
        
        # Unprotect any project tokens in the insights if needed
        if use_protection:
            try:
                ai_response = protection_plugin.unprotect_text(ai_response)
            except Exception as e:
                debug_print(f"Error unprotecting project insights: {e}")
        
        return ai_response.strip()
    except Exception as e:
        debug_print(f"Error generating RAG-enhanced project insight: {e}")
        return f"⚠️ Unable to generate AI insight: {e}"

def get_guideline_violation_alerts(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify potential guideline violations in tasks.
    
    Args:
        tasks: List of tasks to analyze
        
    Returns:
        List of potential guideline violations
    """
    alerts = []
    
    try:
        from src.core.knowledge.knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(name="guidelines")
        
        # Check for email response time violations
        email_guidelines = kb.query_guidelines("email response time guidelines", top_k=2)
        if email_guidelines:
            current_date = datetime.now()
            for task in tasks:
                if any(keyword in task.get('task', '').lower() for keyword in ['email', 'response', 'reply']):
                    task_date = task.get('date')
                    if task_date:
                        if isinstance(task_date, str):
                            try:
                                task_date = datetime.strptime(task_date, '%Y-%m-%d')
                            except:
                                continue
                        
                        days_diff = (current_date - task_date).days
                        if days_diff > 2:  # More than 2 business days
                            alerts.append({
                                'type': 'email_response_time',
                                'task': task.get('task', ''),
                                'days_overdue': days_diff,
                                'guideline': 'Email responses should be handled within 2 business days',
                                'severity': 'medium'
                            })
        
        # Check for security-related delays
        security_guidelines = kb.query_guidelines("security incident response guidelines", top_k=2)
        if security_guidelines:
            for task in tasks:
                if any(keyword in task.get('task', '').lower() for keyword in ['security', 'vulnerability', 'patch']):
                    task_date = task.get('date')
                    if task_date:
                        if isinstance(task_date, str):
                            try:
                                task_date = datetime.strptime(task_date, '%Y-%m-%d')
                            except:
                                continue
                        
                        days_diff = (current_date - task_date).days
                        if days_diff > 1:  # Security issues should be addressed within 1 day
                            alerts.append({
                                'type': 'security_response_time',
                                'task': task.get('task', ''),
                                'days_overdue': days_diff,
                                'guideline': 'Security issues should be addressed within 1 business day',
                                'severity': 'high'
                            })
        
    except Exception as e:
        debug_print(f"Error checking guideline violations: {e}")
    
    return alerts 