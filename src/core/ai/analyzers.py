"""
AI-powered analyzers for Task Manager.
Provides insights and analysis of tasks and related data.
"""
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime
import os
from src.config.settings import (
    AI_PROVIDER,
    CHAT_MODEL,
    DEBUG_MODE,
    MIN_TASK_LENGTH
)

class AnalyzerBase:
    """Base class for analyzers."""
    def __init__(self, model_name=None):
        self.model_name = model_name or AI_PROVIDER
        self.provider = AI_PROVIDER
        self.client = None
        self._initialize_gemini()

    def _initialize_gemini(self):
        """Initialize Gemini client."""
        try:
            from src.core.gemini_client import client as gemini_client
            self.client = gemini_client
        except ImportError:
            print("Gemini client not available")
            self.client = None

    def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini."""
        if not self.client:
            return "Gemini client not available"
        
        try:
            # Use Gemini's native API
            response_text = self.client.generate_content(
                prompt,
                temperature=0.7
            )
            return response_text
        except Exception as e:
            print(f"Error generating text with Gemini: {e}")
            return f"Error: {str(e)}"

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

    def analyze_task_similarity(self, 
                               new_task: Dict[str, Any], 
                               existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze similarity between a new task and existing tasks using AI.
        
        Args:
            new_task: The new task to check
            existing_tasks: List of existing tasks to compare against
            
        Returns:
            Dict with similarity results
        """
        if not new_task or not existing_tasks:
            return {
                "is_match": False,
                "confidence": 0.0,
                "explanation": "No tasks to compare"
            }
        
        try:
            # Create prompt for similarity analysis
            prompt = self._create_similarity_prompt(new_task, existing_tasks)
            
            # Generate analysis using AI
            response = self.generate_text(prompt)
            
            # Parse the response
            return self._parse_similarity_response(response, existing_tasks)
            
        except Exception as e:
            import traceback
            print(f"Error in task similarity analysis: {e}")
            print(traceback.format_exc())
            return {
                "is_match": False,
                "confidence": 0.0,
                "explanation": f"Error in AI analysis: {str(e)}"
            }
    
    def _create_similarity_prompt(self, new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> str:
        """Create a prompt for task similarity analysis."""
        
        new_task_text = new_task.get("task", "")
        
        # Format existing tasks
        existing_tasks_text = ""
        for i, task in enumerate(existing_tasks, 1):
            task_text = task.get("task", "")
            description = task.get("description", "")
            status = task.get("status", "")
            category = task.get("category", "")
            
            existing_tasks_text += f"{i}. Task: {task_text}\n"
            if description:
                existing_tasks_text += f"   Description: {description}\n"
            existing_tasks_text += f"   Status: {status}, Category: {category}\n\n"
        
        prompt = f"""You are an expert at identifying duplicate or similar tasks in a project management system.

NEW TASK TO CHECK:
"{new_task_text}"

EXISTING TASKS:
{existing_tasks_text}

Please analyze if the new task is similar to any existing tasks. Consider:
- Semantic similarity (same meaning, different words)
- Functional similarity (same purpose/goal)
- Domain similarity (same area of work)
- Implementation similarity (same technical approach)

Respond in the following JSON format:
{{
    "is_match": true/false,
    "confidence": 0.0-1.0,
    "matched_task_index": null or the index number (1-based),
    "explanation": "Detailed explanation of why tasks are similar or different"
}}

If there's a match, provide the index number of the most similar existing task. If no match, set matched_task_index to null.

Response:"""
        
        return prompt
    
    def _parse_similarity_response(self, response: str, existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse the AI response for task similarity."""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Validate required fields
                if "is_match" not in result or "confidence" not in result:
                    raise ValueError("Missing required fields in AI response")
                
                # Get the matched task if there's a match
                matched_task = None
                if result.get("is_match") and result.get("matched_task_index"):
                    try:
                        index = int(result["matched_task_index"]) - 1  # Convert to 0-based
                        if 0 <= index < len(existing_tasks):
                            matched_task = existing_tasks[index]
                    except (ValueError, IndexError):
                        pass
                
                return {
                    "is_match": result["is_match"],
                    "confidence": float(result["confidence"]),
                    "matched_task": matched_task,
                    "explanation": result.get("explanation", "No explanation provided")
                }
            else:
                # Fallback: try to infer from text response
                is_match = "true" in response.lower() and "match" in response.lower()
                confidence = 0.8 if is_match else 0.0
                
                return {
                    "is_match": is_match,
                    "confidence": confidence,
                    "matched_task": None,
                    "explanation": f"Could not parse AI response: {response[:200]}..."
                }
                
        except Exception as e:
            return {
                "is_match": False,
                "confidence": 0.0,
                "matched_task": None,
                "explanation": f"Error parsing AI response: {str(e)}"
            }

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
    """Get response from Gemini API."""
    try:
        from src.core.gemini_client import client
        
        if not client:
            raise Exception("Gemini client not available")
        
        # Use Gemini's native API
        response_text = client.generate_content(
            prompt,
            temperature=0.3
        )
        
        return response_text
        
    except Exception as e:
        print(f"Error getting AI response from Gemini: {e}")
        return f"Error: {str(e)}"