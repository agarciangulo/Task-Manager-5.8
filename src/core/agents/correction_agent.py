"""
Simplified AI agent for interpreting user correction requests.
"""
import json
import re
from typing import List, Dict, Any, Optional
from src.core.gemini_client import client
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class CorrectionAgent:
    """Simplified AI agent for interpreting user correction requests."""
    
    def __init__(self):
        """Initialize the correction agent."""
        self.ai_client = client
    
    def interpret_corrections(self, reply_text: str, task_ids: List[str]) -> Dict[str, Any]:
        """
        Interpret user correction request using AI.
        
        Args:
            reply_text: User's correction request
            task_ids: List of task IDs from the original email
            
        Returns:
            Dict: Interpretation result with corrections
        """
        try:
            # Build simple, focused prompt
            prompt = self._build_simple_correction_prompt(reply_text, task_ids)
            
            # Get AI response
            response = self.ai_client.generate_content(prompt)
            
            # Parse response (response is already a string)
            corrections = self._parse_simple_response(response, task_ids)
            
            return {
                'corrections': corrections,
                'confidence_score': self._calculate_simple_confidence(corrections),
                'requires_clarification': len(corrections) == 0,
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Error interpreting corrections: {str(e)}")
            return {
                'corrections': [],
                'confidence_score': 0.0,
                'requires_clarification': True,
                'error': str(e)
            }
    
    def _build_simple_correction_prompt(self, reply_text: str, task_ids: List[str]) -> str:
        """
        Build a simple, focused prompt for correction interpretation.
        
        Args:
            reply_text: User's correction request
            task_ids: List of task IDs
            
        Returns:
            str: AI prompt
        """
        # Create numbered list of tasks
        tasks_text = "\n".join([f"{i+1}. Task ID: {task_id}" for i, task_id in enumerate(task_ids)])
        
        prompt = f"""
You are helping interpret a user's correction request for their tasks.

TASKS FROM ORIGINAL EMAIL:
{tasks_text}

USER'S CORRECTION REQUEST:
{reply_text}

INSTRUCTIONS:
1. Identify which tasks the user wants to change (by number)
2. Determine what changes they want to make
3. Return a simple JSON response

SUPPORTED CORRECTION TYPES:
- Update: Change task properties (status, priority, due_date, etc.)
- Delete: Remove a task entirely

EXAMPLES:

User says: "Change task 1 status to completed"
Response: {{
    "corrections": [
        {{
            "task_index": 1,
            "type": "update",
            "changes": {{"status": "Completed"}}
        }}
    ]
}}

User says: "Delete task 2"
Response: {{
    "corrections": [
        {{
            "task_index": 2,
            "type": "delete",
            "changes": {{}}
        }}
    ]
}}

User says: "Update task 1 priority to high and due date to 2024-01-15"
Response: {{
    "corrections": [
        {{
            "task_index": 1,
            "type": "update",
            "changes": {{"priority": "High", "due_date": "2024-01-15"}}
        }}
    ]
}}

IMPORTANT:
- Use 1-based indexing (task 1, task 2, etc.)
- Only include corrections that are clearly requested
- If unclear, return empty corrections array
- For dates, use YYYY-MM-DD format
- For status, use: "Not Started", "In Progress", "Completed", "On Hold"
- For priority, use: "Low", "Medium", "High", "Urgent"

Return only the JSON response.
"""
        
        return prompt
    
    def _parse_simple_response(self, response: str, task_ids: List[str]) -> List[Dict]:
        """
        Parse AI response into simple corrections.
        
        Args:
            response: AI response text
            task_ids: List of task IDs
            
        Returns:
            List[Dict]: Parsed corrections
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in AI response")
                return []
            
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            
            if 'corrections' not in parsed:
                logger.warning("No corrections array in AI response")
                return []
            
            # Validate and format corrections
            valid_corrections = []
            for correction in parsed['corrections']:
                if self._validate_correction(correction, task_ids):
                    valid_corrections.append({
                        'task_id': task_ids[correction['task_index'] - 1],
                        'correction_type': correction['type'],
                        'updates': correction.get('changes', {})
                    })
            
            return valid_corrections
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing correction response: {e}")
            return []
    
    def _validate_correction(self, correction: Dict, task_ids: List[str]) -> bool:
        """
        Validate a single correction.
        
        Args:
            correction: Correction data
            task_ids: List of task IDs
            
        Returns:
            bool: True if valid
        """
        try:
            # Check required fields
            if 'task_index' not in correction or 'type' not in correction:
                return False
            
            # Validate task index
            task_index = correction['task_index']
            if not isinstance(task_index, int) or task_index < 1 or task_index > len(task_ids):
                return False
            
            # Validate correction type
            correction_type = correction['type']
            if correction_type not in ['update', 'delete']:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_simple_confidence(self, corrections: List[Dict]) -> float:
        """
        Calculate simple confidence score.
        
        Args:
            corrections: List of corrections
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        if not corrections:
            return 0.0
        
        # Simple confidence based on number of corrections and types
        base_confidence = 0.7
        
        # Boost confidence for clear, simple corrections
        if len(corrections) == 1:
            base_confidence += 0.2
        
        # Boost for common correction types
        for correction in corrections:
            if correction['correction_type'] == 'update':
                changes = correction.get('updates', {})
                if 'status' in changes or 'priority' in changes:
                    base_confidence += 0.1
                    break
        
        return min(base_confidence, 1.0) 