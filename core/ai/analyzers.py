"""
AI-powered analyzers for Task Manager.
Provides insights and analysis of tasks and related data.
"""
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime
import os
from config import (
    DEBUG_MODE,
    AI_MODEL,
    AI_PROVIDER,
    OPENAI_API_KEY,
    CHAT_MODEL,
    HUGGINGFACE_TOKEN
)

class AnalyzerBase:
    """Base class for analyzers."""
    def __init__(self, model_name=None):
        self.model_name = model_name or AI_MODEL
        self.provider = AI_PROVIDER
        self.client = None
        self._initialize_openai()

    def _initialize_openai(self):
        """Initialize OpenAI client."""
        import httpx
        from openai import OpenAI
        from core.openai_client import client as openai_client
        
        # Use the shared client if available
        self.client = openai_client
        if self.client is None:
            http_client = httpx.Client(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            self.client = OpenAI(
                api_key=OPENAI_API_KEY,
                http_client=http_client
            )

    def generate_text(self, prompt: str) -> str:
        """Generate text using OpenAI."""
        response = self.client.chat_completions_create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content

    def analyze(self, content, **kwargs):
        """
        Analyze content.
        
        Args:
            content: Content to analyze.
            **kwargs: Additional arguments.
            
        Returns:
            dict: Analysis results.
        """
        # This should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement analyze()")

class TaskAnalyzer(AnalyzerBase):
    """Analyzer for tasks."""
    
    def __init__(self):
        """Initialize the task analyzer."""
        super().__init__()
    
    def analyze(self, 
                tasks: Union[List[Dict[str, Any]], pd.DataFrame], 
                analysis_type: str = "basic",
                **kwargs) -> Dict[str, Any]:
        """
        Analyze tasks.
        
        Args:
            tasks: Tasks to analyze (list of dictionaries or DataFrame).
            analysis_type: Type of analysis to perform.
            **kwargs: Additional arguments.
            
        Returns:
            dict: Analysis results.
        """
        # Convert list to DataFrame if necessary
        if isinstance(tasks, list):
            tasks_df = pd.DataFrame(tasks)
        else:
            tasks_df = tasks.copy()
            
        # Basic statistics
        if analysis_type == "basic":
            # Handle empty dataframe
            if tasks_df.empty:
                return {
                    "count": 0,
                    "message": "No tasks available for analysis"
                }
                
            # Calculate basic statistics
            result = {
                "count": len(tasks_df),
                "status_distribution": {}
            }
            
            # Status distribution
            if "status" in tasks_df.columns:
                status_counts = tasks_df["status"].value_counts().to_dict()
                result["status_distribution"] = status_counts
                
                # Calculate completion rate
                completed = status_counts.get("Completed", 0)
                result["completion_rate"] = completed / len(tasks_df) if len(tasks_df) > 0 else 0
            
            # Category distribution
            if "category" in tasks_df.columns:
                result["category_distribution"] = tasks_df["category"].value_counts().to_dict()
            
            # Employee distribution
            if "employee" in tasks_df.columns:
                result["employee_distribution"] = tasks_df["employee"].value_counts().to_dict()
            
            # Date statistics
            if "date" in tasks_df.columns:
                # Ensure date is datetime
                if tasks_df["date"].dtype == 'object':
                    tasks_df["date"] = pd.to_datetime(tasks_df["date"], errors='coerce')
                
                valid_dates = tasks_df["date"].dropna()
                if not valid_dates.empty:
                    result["date_range"] = {
                        "min": valid_dates.min().strftime("%Y-%m-%d"),
                        "max": valid_dates.max().strftime("%Y-%m-%d")
                    }
                    
                    # Calculate days since for each task
                    today = pd.Timestamp(datetime.now().date())
                    tasks_df["days_since"] = (today - tasks_df["date"]).dt.days
                    
                    result["age_statistics"] = {
                        "average_age": tasks_df["days_since"].mean(),
                        "max_age": tasks_df["days_since"].max(),
                        "tasks_older_than_7_days": int(sum(tasks_df["days_since"] > 7))
                    }
            
            return result
            
        # AI insights analysis
        elif analysis_type == "ai_insights":
            # Create prompt for the model
            prompt = self._create_insights_prompt(tasks_df, **kwargs)
            
            # Generate insights using the appropriate model
            try:
                insight = self.generate_text(prompt)
                
                return {
                    "insight": insight,
                    "raw_tasks": tasks_df.to_dict('records')
                }
            except Exception as e:
                import traceback
                print(f"Error analyzing tasks: {e}")
                print(traceback.format_exc())
                raise ValueError(f"Task analysis failed: {str(e)}\n{traceback.format_exc()}")
            
        # Default case
        return {
            "message": f"Unsupported analysis type: {analysis_type}"
        }
    
    def _create_insights_prompt(self, tasks_df: pd.DataFrame, **kwargs) -> str:
        """Create a prompt for AI insights."""
        person_name = kwargs.get('person_name', 'Unknown')
        recent_tasks = kwargs.get('recent_tasks', pd.DataFrame())
        peer_feedback = kwargs.get('peer_feedback', [])
        
        # Format tasks
        tasks_text = "\n".join([
            f"- {row['task']} (Status: {row['status']}, Category: {row.get('category', 'Uncategorized')})"
            for _, row in tasks_df.iterrows()
        ])
        
        # Format recent tasks
        recent_text = ""
        if not recent_tasks.empty:
            recent_text = "\nRecent tasks (last 14 days):\n" + "\n".join([
                f"- {row['task']} (Status: {row['status']}, Category: {row.get('category', 'Uncategorized')})"
                for _, row in recent_tasks.iterrows()
            ])
        
        # Format peer feedback
        feedback_text = ""
        if peer_feedback:
            feedback_text = "\nPeer feedback:\n" + "\n".join([
                f"- {entry['feedback']} (Date: {entry['date']})"
                for entry in peer_feedback
            ])
        
        # Create the prompt
        prompt = f"""You are a productivity coach analyzing {person_name}'s work patterns and progress.

CURRENT TASKS:
{tasks_text}
{recent_text}
{feedback_text}

Please provide a comprehensive analysis with the following sections:

1. WORKLOAD SUMMARY:
- Current task distribution across projects/categories
- Task completion patterns
- Any potential bottlenecks or blockers

2. PRODUCTIVITY INSIGHTS:
- Notable achievements or progress
- Areas where efficiency could be improved
- Task prioritization effectiveness

3. RECOMMENDATIONS:
- 2-3 specific, actionable suggestions for improvement
- Tips for better task management
- Ways to optimize workflow

Keep your tone supportive and constructive. Focus on actionable insights that can help {person_name} improve their productivity and work quality.

Analysis:"""
        
        return prompt

class ProjectAnalyzer(AnalyzerBase):
    """Analyzer for projects."""
    
    def analyze(self, 
                tasks: Union[List[Dict[str, Any]], pd.DataFrame],
                project: str,
                analysis_type: str = "health_check",
                **kwargs) -> Dict[str, Any]:
        """
        Analyze project health.
        
        Args:
            tasks: Tasks related to the project.
            project: Name of the project.
            analysis_type: Type of analysis to perform.
            **kwargs: Additional arguments.
            
        Returns:
            dict: Analysis results.
        """
        # Convert list to DataFrame if necessary
        if isinstance(tasks, list):
            tasks_df = pd.DataFrame(tasks)
        else:
            tasks_df = tasks.copy()
            
        # Filter for the project if category is available
        if "category" in tasks_df.columns:
            project_tasks = tasks_df[tasks_df["category"] == project]
        else:
            project_tasks = tasks_df
            
        # Basic project health check
        if analysis_type == "health_check":
            # Calculate health metrics
            if project_tasks.empty:
                return {
                    "project": project,
                    "health_score": 0,
                    "message": "No tasks found for this project"
                }
                
            # Calculate basic metrics
            total_tasks = len(project_tasks)
            
            if "status" in project_tasks.columns:
                status_counts = project_tasks["status"].value_counts().to_dict()
                completed = status_counts.get("Completed", 0)
                blocked = status_counts.get("Blocked", 0)
                
                # Calculate health score (simple version)
                health_score = (completed / total_tasks * 100) - (blocked / total_tasks * 50)
                health_score = max(0, min(100, health_score))
                
                # Determine health status
                if health_score >= 75:
                    health_status = "Healthy"
                elif health_score >= 50:
                    health_status = "Needs Attention"
                else:
                    health_status = "At Risk"
                    
                return {
                    "project": project,
                    "health_score": health_score,
                    "health_status": health_status,
                    "task_count": total_tasks,
                    "status_distribution": status_counts
                }
            
            # Fallback if status column missing
            return {
                "project": project,
                "health_score": 50,  # Neutral score
                "health_status": "Unknown",
                "task_count": total_tasks,
                "message": "Limited data available for health assessment"
            }
            
        # AI-powered project insights
        elif analysis_type == "ai_insights":
            prompt = self._create_project_prompt(project_tasks, project, **kwargs)
            
            try:
                response = self.generate_text(prompt)
                
                return {
                    "project": project,
                    "insights": response,
                    "task_count": len(project_tasks),
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            except Exception as e:
                print(f"Error generating project insights: {e}")
                return {
                    "project": project,
                    "error": str(e),
                    "message": "Unable to generate project insights"
                }
                
        # Unknown analysis type
        return {
            "project": project,
            "error": f"Unknown analysis type: {analysis_type}",
            "supported_types": ["health_check", "ai_insights"]
        }
    
    def _create_project_prompt(self, tasks_df: pd.DataFrame, project: str, **kwargs) -> str:
        """
        Create a prompt for AI project insights.
        
        Args:
            tasks_df: DataFrame of project tasks.
            project: Name of the project.
            **kwargs: Additional arguments.
            
        Returns:
            str: The prompt.
        """
        # Convert DataFrame to a more readable format
        tasks_str = ""
        for _, row in tasks_df.iterrows():
            task_str = f"- {row.get('task', 'Unknown task')}"
            
            if 'status' in row:
                task_str += f" (Status: {row['status']})"
                
            if 'employee' in row:
                task_str += f" (Employee: {row['employee']})"
                
            if 'date' in row:
                date_str = row['date']
                if not isinstance(date_str, str):
                    date_str = date_str.strftime("%Y-%m-%d") if hasattr(date_str, 'strftime') else str(date_str)
                task_str += f" (Date: {date_str})"
                
            tasks_str += task_str + "\n"
            
        # Basic statistics for the prompt
        task_count = len(tasks_df)
        
        # Status distribution
        status_dist = {}
        if 'status' in tasks_df.columns:
            status_dist = tasks_df["status"].value_counts().to_dict()
            
        # Employee distribution
        employee_dist = {}
        if 'employee' in tasks_df.columns:
            employee_dist = tasks_df["employee"].value_counts().to_dict()
        
        prompt = f"""
        You are ProjectAnalyst, a strategic advisor on project management and team productivity.

        ANALYZE PROJECT '{project}' TASKS:
        {tasks_str}

        PROJECT METADATA:
        - Total Tasks: {task_count}
        - Status Distribution: {status_dist}
        - Team Distribution: {employee_dist}

        FIRST, PERFORM A METADATA ANALYSIS ON THE PROJECT:
        - Calculate key project metrics: completion rate, velocity, team distribution
        - Identify how many tasks have been open for more than 7 days
        - Analyze distribution of task ages
        - Determine if certain team members have disproportionate workloads
        - Identify any bottlenecks or common blockers
        - Determine if task completion is on pace with creation

        THEN, PROVIDE A THREE-PART INSIGHT:
        1. HEALTH STATUS: One sentence on overall project health
        2. KEY RISK: The most critical item requiring attention
        3. STRATEGIC RECOMMENDATION: One specific action to improve project health

        Keep your response focused, data-driven, and immediately actionable.
        """
        
        return prompt

def get_ai_response(prompt: str) -> str:
    """Get response from the configured AI provider."""
    from core.openai_client import client
    response = client.chat_completions_create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content