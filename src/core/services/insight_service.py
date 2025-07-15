"""
Insight Service for AI Team Support.
Implements the IInsightService interface for AI-powered insights and analysis.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from src.core.interfaces.task_service import IInsightService
from src.core.exceptions.service_exceptions import (
    InsightServiceError, AIProcessingError, UserNotFoundError
)
from src.core.logging.service_logger import LoggingMixin, log_operation
from src.core.ai.insights import get_coaching_insight
from src.core.ai.analyzers import TaskAnalyzer, ProjectAnalyzer
from src.core.services.auth_service import AuthService
from src.core.agents.notion_agent import NotionAgent


class InsightService(IInsightService, LoggingMixin):
    """Service for generating AI-powered insights and analysis."""
    
    def __init__(self, notion_token: str, auth_service: AuthService):
        super().__init__()
        self.notion_token = notion_token
        self.auth_service = auth_service
        self.notion_agent = NotionAgent()
        self.task_analyzer = TaskAnalyzer()
        self.project_analyzer = ProjectAnalyzer()
    
    @log_operation("generate_coaching_insights")
    def generate_coaching_insights(self, user_id: str, tasks: List[Dict[str, Any]]) -> str:
        """Generate coaching insights for a user."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise InsightServiceError("User does not have a task database configured")
            
            self.log_info("generate_insights_start", 
                         user_id=user_id,
                         tasks_count=len(tasks))
            
            # Get existing tasks for context
            existing_tasks = self.notion_agent.fetch_tasks(user.task_database_id)
            
            if not tasks:
                return "No tasks provided for analysis."
            
            if existing_tasks.empty:
                return "No existing tasks found for comparison."
            
            # Generate insights using AI
            insights = get_coaching_insight(
                user.full_name or "User",
                tasks,
                existing_tasks,
                []  # Empty peer feedback for now
            )
            
            self.log_info("generate_insights_success", 
                         user_id=user_id,
                         insights_length=len(insights))
            
            return insights
            
        except Exception as e:
            self.log_error("generate_insights_error", e, user_id=user_id)
            if isinstance(e, (UserNotFoundError, InsightServiceError)):
                raise
            raise AIProcessingError(f"Failed to generate coaching insights: {str(e)}")
    
    @log_operation("analyze_task_patterns")
    def analyze_task_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze task patterns for a user."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise InsightServiceError("User does not have a task database configured")
            
            self.log_info("analyze_patterns_start", user_id=user_id)
            
            # Get user's tasks
            tasks_df = self.notion_agent.fetch_tasks(user.task_database_id)
            
            if tasks_df.empty:
                return {
                    "message": "No tasks found for analysis",
                    "patterns": {},
                    "recommendations": []
                }
            
            # Analyze patterns using the task analyzer
            summary_stats = self.task_analyzer.get_summary_statistics(tasks_df)
            tasks_by_status = self.task_analyzer.get_tasks_by_status(tasks_df)
            tasks_by_category = self.task_analyzer.get_tasks_by_category(tasks_df)
            upcoming_deadlines = self.task_analyzer.get_upcoming_deadlines(tasks_df)
            
            # Generate recommendations based on patterns
            recommendations = self._generate_recommendations(
                summary_stats, tasks_by_status, tasks_by_category
            )
            
            patterns = {
                "summary_stats": summary_stats,
                "tasks_by_status": tasks_by_status,
                "tasks_by_category": tasks_by_category,
                "upcoming_deadlines": upcoming_deadlines
            }
            
            self.log_info("analyze_patterns_success", 
                         user_id=user_id,
                         patterns_count=len(patterns),
                         recommendations_count=len(recommendations))
            
            return {
                "patterns": patterns,
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.log_error("analyze_patterns_error", e, user_id=user_id)
            if isinstance(e, (UserNotFoundError, InsightServiceError)):
                raise
            raise AIProcessingError(f"Failed to analyze task patterns: {str(e)}")
    
    @log_operation("get_project_insights")
    def get_project_insights(self, user_id: str, project_name: str) -> Dict[str, Any]:
        """Get insights for a specific project."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise InsightServiceError("User does not have a task database configured")
            
            self.log_info("get_project_insights_start", 
                         user_id=user_id,
                         project_name=project_name)
            
            # Get user's tasks
            tasks_df = self.notion_agent.fetch_tasks(user.task_database_id)
            
            if tasks_df.empty:
                return {
                    "message": "No tasks found for project analysis",
                    "project_insights": {},
                    "recommendations": []
                }
            
            # Filter tasks for the specific project
            project_tasks = tasks_df[tasks_df['category'] == project_name]
            
            if project_tasks.empty:
                return {
                    "message": f"No tasks found for project '{project_name}'",
                    "project_insights": {},
                    "recommendations": []
                }
            
            # Analyze project-specific patterns
            project_stats = self.task_analyzer.get_summary_statistics(project_tasks)
            project_status_distribution = self.task_analyzer.get_tasks_by_status(project_tasks)
            project_deadlines = self.task_analyzer.get_upcoming_deadlines(project_tasks)
            
            # Generate project-specific insights
            project_insights = self._generate_project_insights(
                project_name, project_stats, project_status_distribution, project_deadlines
            )
            
            # Generate project-specific recommendations
            recommendations = self._generate_project_recommendations(
                project_name, project_stats, project_status_distribution
            )
            
            result = {
                "project_name": project_name,
                "project_insights": project_insights,
                "recommendations": recommendations,
                "task_count": len(project_tasks),
                "completion_rate": project_stats.get("completion_rate", 0)
            }
            
            self.log_info("get_project_insights_success", 
                         user_id=user_id,
                         project_name=project_name,
                         task_count=len(project_tasks))
            
            return result
            
        except Exception as e:
            self.log_error("get_project_insights_error", e, 
                          user_id=user_id, project_name=project_name)
            if isinstance(e, (UserNotFoundError, InsightServiceError)):
                raise
            raise AIProcessingError(f"Failed to get project insights: {str(e)}")
    
    def _generate_recommendations(self, summary_stats: Dict, 
                                 tasks_by_status: Dict, 
                                 tasks_by_category: Dict) -> List[str]:
        """Generate recommendations based on task patterns."""
        recommendations = []
        
        # Check completion rate
        completion_rate = summary_stats.get("completion_rate", 0)
        if completion_rate < 0.5:
            recommendations.append("Consider focusing on completing more tasks to improve your completion rate.")
        elif completion_rate > 0.8:
            recommendations.append("Great job! You're maintaining a high completion rate.")
        
        # Check for overdue tasks
        overdue_count = summary_stats.get("overdue_count", 0)
        if overdue_count > 0:
            recommendations.append(f"You have {overdue_count} overdue tasks. Consider reviewing and updating their priorities.")
        
        # Check task distribution
        if tasks_by_status:
            not_started = tasks_by_status.get("Not Started", 0)
            in_progress = tasks_by_status.get("In Progress", 0)
            
            if not_started > in_progress * 2:
                recommendations.append("You have many tasks that haven't been started. Consider beginning work on some key tasks.")
            elif in_progress > 5:
                recommendations.append("You have many tasks in progress. Consider focusing on completing a few before starting new ones.")
        
        # Check category distribution
        if tasks_by_category:
            category_count = len(tasks_by_category)
            if category_count > 10:
                recommendations.append("You're working across many categories. Consider consolidating related tasks.")
            elif category_count < 3:
                recommendations.append("You're focused on few categories. Consider diversifying your work if appropriate.")
        
        return recommendations
    
    def _generate_project_insights(self, project_name: str, 
                                  project_stats: Dict, 
                                  status_distribution: Dict, 
                                  deadlines: List) -> Dict[str, Any]:
        """Generate insights specific to a project."""
        insights = {
            "project_name": project_name,
            "total_tasks": project_stats.get("total_tasks", 0),
            "completion_rate": project_stats.get("completion_rate", 0),
            "status_distribution": status_distribution,
            "upcoming_deadlines": deadlines,
            "average_completion_time": project_stats.get("average_completion_time", 0),
            "priority_distribution": project_stats.get("priority_distribution", {})
        }
        
        # Add qualitative insights
        completion_rate = project_stats.get("completion_rate", 0)
        if completion_rate > 0.8:
            insights["performance_rating"] = "Excellent"
            insights["performance_note"] = "This project is progressing very well with high completion rates."
        elif completion_rate > 0.6:
            insights["performance_rating"] = "Good"
            insights["performance_note"] = "This project is progressing well with solid completion rates."
        elif completion_rate > 0.4:
            insights["performance_rating"] = "Fair"
            insights["performance_note"] = "This project could benefit from increased focus on task completion."
        else:
            insights["performance_rating"] = "Needs Attention"
            insights["performance_note"] = "This project may need additional resources or reprioritization."
        
        return insights
    
    def _generate_project_recommendations(self, project_name: str, 
                                        project_stats: Dict, 
                                        status_distribution: Dict) -> List[str]:
        """Generate recommendations specific to a project."""
        recommendations = []
        
        completion_rate = project_stats.get("completion_rate", 0)
        total_tasks = project_stats.get("total_tasks", 0)
        
        if completion_rate < 0.5 and total_tasks > 5:
            recommendations.append(f"Project '{project_name}' has a low completion rate. Consider reviewing task priorities and breaking down larger tasks.")
        
        if status_distribution:
            not_started = status_distribution.get("Not Started", 0)
            in_progress = status_distribution.get("In Progress", 0)
            
            if not_started > in_progress:
                recommendations.append(f"Project '{project_name}' has many unstarted tasks. Consider beginning work on key deliverables.")
            
            if in_progress > 3:
                recommendations.append(f"Project '{project_name}' has many tasks in progress. Consider focusing on completing a few before starting new ones.")
        
        return recommendations 