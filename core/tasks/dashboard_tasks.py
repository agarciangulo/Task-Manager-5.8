"""
Asynchronous dashboard tasks for Task Manager.
Handles dashboard data aggregation and analytics without blocking the main application.
"""
import traceback
from typing import Dict, List, Any, Optional
from celery import current_task
from celery_config import celery_app
from core.logging_config import get_logger
import pandas as pd
from datetime import datetime, timedelta

logger = get_logger(__name__)

@celery_app.task(bind=True, name='core.tasks.dashboard_tasks.generate_dashboard_data_async')
def generate_dashboard_data_async(self, database_id: str, employee_filter: str = 'all', 
                                project_filter: str = 'all') -> Dict[str, Any]:
    """
    Asynchronously generate dashboard data with filtering support.
    
    Args:
        database_id: The Notion database ID
        employee_filter: Employee filter ('all' or specific employee)
        project_filter: Project filter ('all' or specific project)
        
    Returns:
        Dict with dashboard metrics and data
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Fetching tasks...'}
        )
        
        # Import here to avoid circular imports
        from core.tasks.notion_tasks import fetch_tasks_async
        
        # Fetch tasks asynchronously
        fetch_result = fetch_tasks_async.delay(database_id, 30)
        fetch_result.wait()  # Wait for completion
        
        if not fetch_result.result['success']:
            return {
                'success': False,
                'error': fetch_result.result['error']
            }
        
        tasks_data = fetch_result.result['data']
        df = pd.DataFrame(tasks_data)
        
        if df.empty:
            return {
                'success': True,
                'metrics': {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'in_progress_tasks': 0,
                    'pending_tasks': 0,
                    'blocked_tasks': 0,
                    'completion_rate': 0
                },
                'category_counts': {},
                'trend_data': {},
                'project_health': {}
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Applying filters...'}
        )
        
        # Apply filters
        filtered_df = df.copy()
        
        if employee_filter != 'all':
            filtered_df = filtered_df[filtered_df['employee'] == employee_filter]
            
        if project_filter != 'all':
            filtered_df = filtered_df[filtered_df['category'] == project_filter]
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Calculating metrics...'}
        )
        
        # Calculate overall metrics
        total_tasks = len(filtered_df)
        completed_tasks = len(filtered_df[filtered_df['status'] == 'Completed'])
        in_progress_tasks = len(filtered_df[filtered_df['status'] == 'In Progress'])
        pending_tasks = len(filtered_df[filtered_df['status'] == 'Pending'])
        blocked_tasks = len(filtered_df[filtered_df['status'] == 'Blocked'])
        
        completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        
        # Calculate tasks by category
        category_counts = filtered_df['category'].value_counts().to_dict()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Analyzing trends...'}
        )
        
        # Calculate task trend (completed tasks over time)
        try:
            filtered_df['date'] = pd.to_datetime(filtered_df['date'])
            df_completed = filtered_df[filtered_df['status'] == 'Completed']
            
            # Group by date and count
            if not df_completed.empty:
                trend_data = df_completed.groupby(df_completed['date'].dt.strftime('%Y-%m-%d')).size().to_dict()
                # Sort by date
                trend_data = {k: trend_data[k] for k in sorted(trend_data.keys())}
            else:
                trend_data = {}
        except Exception as e:
            logger.warning(f"Error calculating trend data: {str(e)}")
            trend_data = {}
        
        # Calculate project health scores
        project_health = {}
        try:
            for category in filtered_df['category'].unique():
                category_df = filtered_df[filtered_df['category'] == category]
                category_total = len(category_df)
                category_completed = len(category_df[category_df['status'] == 'Completed'])
                category_blocked = len(category_df[category_df['status'] == 'Blocked'])
                
                # Simple health score: (completed - blocked) / total
                health_score = ((category_completed - category_blocked) / category_total * 100) if category_total > 0 else 0
                project_health[category] = round(max(0, health_score), 1)
        except Exception as e:
            logger.warning(f"Error calculating project health: {str(e)}")
        
        logger.info(f"Successfully generated dashboard data for database {database_id}")
        
        return {
            'success': True,
            'metrics': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'pending_tasks': pending_tasks,
                'blocked_tasks': blocked_tasks,
                'completion_rate': completion_rate
            },
            'category_counts': category_counts,
            'trend_data': trend_data,
            'project_health': project_health,
            'filters': {
                'employee': employee_filter,
                'project': project_filter
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard data for {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id
        }

@celery_app.task(bind=True, name='core.tasks.dashboard_tasks.identify_stale_tasks_async')
def identify_stale_tasks_async(self, database_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Asynchronously identify stale tasks for dashboard.
    
    Args:
        database_id: The Notion database ID
        days: Number of days to consider for stale tasks
        
    Returns:
        Dict with stale tasks data
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing tasks...'}
        )
        
        # Import here to avoid circular imports
        from core.tasks.notion_tasks import identify_stale_tasks_async as notion_stale_tasks
        
        # Get stale tasks asynchronously
        stale_result = notion_stale_tasks.delay(database_id, days)
        stale_result.wait()  # Wait for completion
        
        if not stale_result.result['success']:
            return {
                'success': False,
                'error': stale_result.result['error']
            }
        
        stale_tasks = stale_result.result['stale_tasks']
        
        logger.info(f"Successfully identified {len(stale_tasks)} stale tasks in database {database_id}")
        
        return {
            'success': True,
            'stale_tasks': stale_tasks,
            'count': len(stale_tasks),
            'database_id': database_id,
            'days_threshold': days
        }
        
    except Exception as e:
        logger.error(f"Error identifying stale tasks in {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id,
            'days_threshold': days
        }

@celery_app.task(bind=True, name='core.tasks.dashboard_tasks.generate_analytics_report_async')
def generate_analytics_report_async(self, database_id: str, report_type: str = 'weekly') -> Dict[str, Any]:
    """
    Asynchronously generate comprehensive analytics report.
    
    Args:
        database_id: The Notion database ID
        report_type: Type of report ('daily', 'weekly', 'monthly')
        
    Returns:
        Dict with analytics report data
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Fetching data...'}
        )
        
        # Import here to avoid circular imports
        from core.tasks.notion_tasks import fetch_tasks_async
        
        # Determine days back based on report type
        days_back = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30
        }.get(report_type, 7)
        
        # Fetch tasks asynchronously
        fetch_result = fetch_tasks_async.delay(database_id, days_back)
        fetch_result.wait()  # Wait for completion
        
        if not fetch_result.result['success']:
            return {
                'success': False,
                'error': fetch_result.result['error']
            }
        
        tasks_data = fetch_result.result['data']
        df = pd.DataFrame(tasks_data)
        
        if df.empty:
            return {
                'success': True,
                'report_type': report_type,
                'period_days': days_back,
                'summary': 'No tasks found for the specified period',
                'metrics': {},
                'trends': {},
                'insights': []
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Calculating metrics...'}
        )
        
        # Calculate comprehensive metrics
        metrics = {
            'total_tasks': len(df),
            'completed_tasks': len(df[df['status'] == 'Completed']),
            'in_progress_tasks': len(df[df['status'] == 'In Progress']),
            'pending_tasks': len(df[df['status'] == 'Pending']),
            'blocked_tasks': len(df[df['status'] == 'Blocked']),
            'completion_rate': round((len(df[df['status'] == 'Completed']) / len(df) * 100), 1) if len(df) > 0 else 0
        }
        
        # Calculate trends
        try:
            df['date'] = pd.to_datetime(df['date'])
            trends = {
                'daily_completions': df[df['status'] == 'Completed'].groupby(df['date'].dt.strftime('%Y-%m-%d')).size().to_dict(),
                'status_distribution': df['status'].value_counts().to_dict(),
                'category_distribution': df['category'].value_counts().to_dict(),
                'employee_distribution': df['employee'].value_counts().to_dict()
            }
        except Exception as e:
            logger.warning(f"Error calculating trends: {str(e)}")
            trends = {}
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Generating insights...'}
        )
        
        # Generate insights
        insights = []
        
        # Completion rate insight
        if metrics['completion_rate'] > 80:
            insights.append("Excellent completion rate! Team is performing well.")
        elif metrics['completion_rate'] > 60:
            insights.append("Good completion rate. Consider reviewing blocked tasks.")
        else:
            insights.append("Low completion rate. Review task priorities and blockers.")
        
        # Blocked tasks insight
        if metrics['blocked_tasks'] > metrics['total_tasks'] * 0.2:
            insights.append("High number of blocked tasks. Consider addressing blockers.")
        
        # Employee workload insight
        if 'employee_distribution' in trends:
            employee_counts = trends['employee_distribution']
            if employee_counts:
                max_tasks = max(employee_counts.values())
                min_tasks = min(employee_counts.values())
                if max_tasks > min_tasks * 2:
                    insights.append("Uneven workload distribution detected. Consider rebalancing tasks.")
        
        logger.info(f"Successfully generated {report_type} analytics report for database {database_id}")
        
        return {
            'success': True,
            'report_type': report_type,
            'period_days': days_back,
            'generated_at': datetime.now().isoformat(),
            'metrics': metrics,
            'trends': trends,
            'insights': insights,
            'database_id': database_id
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics report for {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id,
            'report_type': report_type
        }

@celery_app.task(bind=True, name='core.tasks.dashboard_tasks.generate_performance_metrics_async')
def generate_performance_metrics_async(self, database_id: str, employee_name: str = None) -> Dict[str, Any]:
    """
    Asynchronously generate performance metrics for individuals or teams.
    
    Args:
        database_id: The Notion database ID
        employee_name: Specific employee name (None for team metrics)
        
    Returns:
        Dict with performance metrics
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Fetching performance data...'}
        )
        
        # Import here to avoid circular imports
        from core.tasks.notion_tasks import fetch_tasks_async
        
        # Fetch tasks asynchronously
        fetch_result = fetch_tasks_async.delay(database_id, 30)
        fetch_result.wait()  # Wait for completion
        
        if not fetch_result.result['success']:
            return {
                'success': False,
                'error': fetch_result.result['error']
            }
        
        tasks_data = fetch_result.result['data']
        df = pd.DataFrame(tasks_data)
        
        if df.empty:
            return {
                'success': True,
                'employee_name': employee_name,
                'metrics': {},
                'trends': {},
                'recommendations': []
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Filtering data...'}
        )
        
        # Filter by employee if specified
        if employee_name:
            df = df[df['employee'] == employee_name]
            if df.empty:
                return {
                    'success': True,
                    'employee_name': employee_name,
                    'metrics': {},
                    'trends': {},
                    'recommendations': ['No tasks found for this employee']
                }
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Calculating performance metrics...'}
        )
        
        # Calculate performance metrics
        metrics = {
            'total_tasks': len(df),
            'completed_tasks': len(df[df['status'] == 'Completed']),
            'in_progress_tasks': len(df[df['status'] == 'In Progress']),
            'pending_tasks': len(df[df['status'] == 'Pending']),
            'blocked_tasks': len(df[df['status'] == 'Blocked']),
            'completion_rate': round((len(df[df['status'] == 'Completed']) / len(df) * 100), 1) if len(df) > 0 else 0,
            'average_tasks_per_day': round(len(df) / 30, 1) if len(df) > 0 else 0
        }
        
        # Calculate trends
        try:
            df['date'] = pd.to_datetime(df['date'])
            trends = {
                'daily_completions': df[df['status'] == 'Completed'].groupby(df['date'].dt.strftime('%Y-%m-%d')).size().to_dict(),
                'category_performance': df[df['status'] == 'Completed']['category'].value_counts().to_dict()
            }
        except Exception as e:
            logger.warning(f"Error calculating trends: {str(e)}")
            trends = {}
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Generating recommendations...'}
        )
        
        # Generate recommendations
        recommendations = []
        
        if metrics['completion_rate'] < 60:
            recommendations.append("Focus on completing pending tasks to improve performance.")
        
        if metrics['blocked_tasks'] > metrics['total_tasks'] * 0.15:
            recommendations.append("Address blocked tasks to improve workflow efficiency.")
        
        if metrics['average_tasks_per_day'] < 1:
            recommendations.append("Consider taking on more tasks to increase productivity.")
        elif metrics['average_tasks_per_day'] > 5:
            recommendations.append("High task volume detected. Consider prioritizing and delegating.")
        
        logger.info(f"Successfully generated performance metrics for {employee_name or 'team'} in database {database_id}")
        
        return {
            'success': True,
            'employee_name': employee_name,
            'metrics': metrics,
            'trends': trends,
            'recommendations': recommendations,
            'database_id': database_id
        }
        
    except Exception as e:
        logger.error(f"Error generating performance metrics for {employee_name or 'team'} in {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id,
            'employee_name': employee_name
        } 