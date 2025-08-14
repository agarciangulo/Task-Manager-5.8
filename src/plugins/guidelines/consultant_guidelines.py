"""
Consultant guidelines plugin for Task Manager.
Enforces consultant best practices in task management.
"""
import os
from typing import Dict, List, Any, Optional

from src.core.adapters.plugin_base import PluginBase
from src.core.models.task import Task

class ConsultantGuidelinesPlugin(PluginBase):
    """Plugin for enforcing consultant guidelines in task management."""
    
    def __init__(self, config=None):
        """
        Initialize the plugin.
        
        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        self.guidelines = []
        self.guideline_source = self.config.get('guideline_source', 'embedded')  # Default to embedded since docs are processed separately
        self.guideline_file = self.config.get('guideline_file', 'docs/guidelines/process/project_management.md')
        
    def initialize(self):
        """
        Initialize the plugin by loading guidelines.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            self.guidelines = self._load_guidelines()
            return len(self.guidelines) > 0
        except Exception as e:
            print(f"Error initializing ConsultantGuidelinesPlugin: {e}")
            return False
    
    def _load_guidelines(self) -> List[Dict[str, Any]]:
        """
        Load guidelines from the configured source.
        
        Returns:
            List[Dict[str, Any]]: List of guideline dictionaries.
        """
        if self.guideline_source == 'embedded':
            return self._get_embedded_guidelines()
        elif self.guideline_source == 'file':
            return self._load_from_file(self.guideline_file)
        else:
            print(f"Unknown guideline source: {self.guideline_source}")
            return []
    
    def _get_embedded_guidelines(self) -> List[Dict[str, Any]]:
        """
        Get the embedded consultant guidelines based on actual project management and technical standards.
        
        Returns:
            List[Dict[str, Any]]: List of guideline dictionaries.
        """
        # Guidelines based on actual project management and technical field guide documents
        return [
            {
                "id": "requirements_gathering",
                "category": "Project Management",
                "title": "Requirements Gathering",
                "description": "Tasks should demonstrate proper requirements gathering including stakeholder interviews, functional requirements, and acceptance criteria.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "requirements", "stakeholder", "interview", "functional", "acceptance", "criteria"
                ])
            },
            {
                "id": "project_planning",
                "category": "Project Management", 
                "title": "Project Planning",
                "description": "Tasks should include proper project planning elements like objectives, schedule, resources, and risk management.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "plan", "schedule", "timeline", "resource", "risk", "objective", "milestone"
                ])
            },
            {
                "id": "code_quality",
                "category": "Technical Standards",
                "title": "Code Quality Standards",
                "description": "Development tasks should mention code quality measures like testing, reviews, and linting.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "test", "review", "lint", "quality", "coverage", "unit", "integration"
                ])
            },
            {
                "id": "security_practices",
                "category": "Technical Standards",
                "title": "Security Practices",
                "description": "Technical tasks should include security considerations like authentication, validation, and OWASP guidelines.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "security", "authentication", "authorization", "validation", "owasp", "https", "encryption"
                ])
            },
            {
                "id": "documentation",
                "category": "Project Management",
                "title": "Documentation Standards",
                "description": "Tasks should include appropriate documentation with context, purpose, and outcomes.",
                "check": lambda task: len(task.description) >= 30 and any(keyword in task.description.lower() for keyword in [
                    "document", "context", "purpose", "outcome", "procedure", "process"
                ])
            },
            {
                "id": "communication",
                "category": "Project Management",
                "title": "Communication Management",
                "description": "Tasks involving stakeholders should include communication plans and status reporting.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "communicate", "stakeholder", "report", "status", "meeting", "update", "escalate"
                ])
            },
            {
                "id": "deployment",
                "category": "Technical Standards",
                "title": "Deployment Procedures",
                "description": "Deployment tasks should include pre-deployment checks, monitoring, and rollback procedures.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "deploy", "pipeline", "monitor", "rollback", "blue-green", "automation"
                ])
            },
            {
                "id": "quality_assurance",
                "category": "Project Management",
                "title": "Quality Assurance",
                "description": "Tasks should include quality checkpoints, testing procedures, and review processes.",
                "check": lambda task: any(keyword in task.description.lower() for keyword in [
                    "quality", "assurance", "testing", "review", "check", "verify", "validate"
                ])
            }
        ]
    
    def _load_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load guidelines from a file.
        
        Args:
            file_path: Path to the guideline file.
            
        Returns:
            List[Dict[str, Any]]: List of guideline dictionaries.
        """
        if not os.path.exists(file_path):
            print(f"Guideline file not found: {file_path}")
            return self._get_embedded_guidelines()
            
        try:
            guidelines = []
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Parse the file format - this is a simple implementation
            # The file should have sections separated by ---
            sections = content.split('---')
            
            for section in sections:
                if not section.strip():
                    continue
                    
                lines = section.strip().split('\n')
                if len(lines) < 3:
                    continue
                    
                guideline = {
                    "id": lines[0].strip(),
                    "category": lines[1].strip(),
                    "title": lines[2].strip(),
                    "description": '\n'.join(lines[3:]).strip()
                }
                
                guidelines.append(guideline)
                
            return guidelines if guidelines else self._get_embedded_guidelines()
            
        except Exception as e:
            print(f"Error loading guidelines from file: {e}")
            return self._get_embedded_guidelines()
    
    def check_task(self, task: Task) -> Dict[str, Any]:
        """
        Check a task against consultant guidelines.
        
        Args:
            task: The task to check.
            
        Returns:
            Dict[str, Any]: Analysis results with violations and suggestions.
        """
        violations = []
        suggestions = []
        
        # Check against each guideline
        for guideline in self.guidelines:
            # If the guideline has a check function, use it
            if "check" in guideline and callable(guideline["check"]):
                if not guideline["check"](task):
                    violations.append(guideline["id"])
                    suggestions.append({
                        "guideline": guideline["title"],
                        "suggestion": f"Improve: {guideline['description']}"
                    })
            # Otherwise, use a simple text search (this could be enhanced with AI)
            else:
                # Example: check if any key terms from the description are in the task
                key_terms = guideline.get("key_terms", [])
                if key_terms and not any(term.lower() in task.description.lower() for term in key_terms):
                    violations.append(guideline["id"])
                    suggestions.append({
                        "guideline": guideline["title"],
                        "suggestion": f"Consider: {guideline['description']}"
                    })
        
        # Calculate adherence score
        adherence_score = 1.0 - (len(violations) / max(len(self.guidelines), 1))
        
        return {
            "task_id": task.id,
            "task_description": task.description,
            "adherence_score": adherence_score,
            "violations": violations,
            "suggestions": suggestions,
            "passes_guidelines": len(violations) == 0
        }
    
    def suggest_improvements(self, task: Task) -> List[str]:
        """
        Suggest improvements to make task adhere to guidelines.
        
        Args:
            task: The task to suggest improvements for.
            
        Returns:
            List[str]: List of improvement suggestions.
        """
        analysis = self.check_task(task)
        
        if analysis['adherence_score'] < 0.8:  # Threshold for suggestions
            return [s['suggestion'] for s in analysis['suggestions']]
        return []