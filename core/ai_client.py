"""
AI client for task processing.
Handles API calls to Claude or OpenAI for AI-based task matching.
"""

import os
import json
import requests
import time
import re
from requests.exceptions import RequestException

# Import config
from config import (
    DEBUG_MODE,
    OPENAI_API_KEY, 
    CHAT_MODEL
)

# Add these to your config.py file
AI_PROVIDER = "openai"  # or "anthropic"

# Example: Load Anthropic API key from environment variable
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def extract_json_from_text(text):
    """
    Extract JSON from text response that may contain additional content.
    This helps parse AI responses that might include explanatory text.
    """
    if not text:
        return None
        
    # Try to find JSON-like content (between curly braces)
    json_pattern = r'\{.*\}'
    json_matches = re.findall(json_pattern, text, re.DOTALL)
    
    if json_matches:
        # Try each potential JSON match
        for json_str in json_matches:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    
    return None

def call_ai_api(prompt):
    """
    Call an AI API (Claude or OpenAI) to process the prompt.
    
    Args:
        prompt (str): The prompt to send to the AI
        
    Returns:
        str: The AI's response as a string
    """
    if AI_PROVIDER.lower() == "anthropic":
        return call_claude_api(prompt)
    else:
        # Default to OpenAI
        return call_openai_api(prompt)

def call_claude_api(prompt):
    """Call Claude API to process the prompt."""
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": AI_MODEL,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        debug_print("Calling Claude API...")
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            debug_print(f"Claude API error: {response.status_code} - {response.text}")
            return json.dumps({
                "best_match_id": None, 
                "similarity_score": 0, 
                "reasoning": f"API Error: {response.status_code}"
            })
        
        response_json = response.json()
        
        # Extract the response content
        if "content" in response_json and len(response_json["content"]) > 0:
            content_text = response_json["content"][0]["text"]
            
            # Try to extract JSON from the response
            json_data = extract_json_from_text(content_text)
            if json_data:
                return json.dumps(json_data)
                
            return content_text
        
        return json.dumps({
            "best_match_id": None, 
            "similarity_score": 0, 
            "reasoning": "Empty API response"
        })
            
    except Exception as e:
        debug_print(f"Claude API error: {e}")
        return json.dumps({
            "best_match_id": None, 
            "similarity_score": 0, 
            "reasoning": f"API error: {str(e)}"
        })

def call_openai_api(prompt):
    """Call OpenAI API to process the prompt."""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Make sure the prompt specifies we need JSON output
        refined_prompt = prompt + "\n\nIMPORTANT: Your response must be in valid JSON format. Only return a JSON object containing 'best_match_id', 'similarity_score', and 'reasoning' keys."
        
        data = {
            "model": CHAT_MODEL,  # e.g., "gpt-4"
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that responds only with valid JSON."},
                {"role": "user", "content": refined_prompt}
            ],
            "max_tokens": 1024
            # Removed the response_format parameter as it's not supported by all models
        }
        
        debug_print("Calling OpenAI API...")
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            debug_print(f"OpenAI API error: {response.status_code} - {response.text}")
            return json.dumps({
                "best_match_id": None, 
                "similarity_score": 0, 
                "reasoning": f"API Error: {response.status_code}"
            })
        
        response_json = response.json()
        
        # Extract the response content
        if "choices" in response_json and len(response_json["choices"]) > 0:
            content = response_json["choices"][0]["message"]["content"]
            
            # Try to extract JSON from the response
            json_data = extract_json_from_text(content)
            if json_data:
                return json.dumps(json_data)
                
            return content
        
        return json.dumps({
            "best_match_id": None, 
            "similarity_score": 0, 
            "reasoning": "Empty API response"
        })
            
    except Exception as e:
        debug_print(f"OpenAI API error: {e}")
        return json.dumps({
            "best_match_id": None, 
            "similarity_score": 0, 
            "reasoning": f"API error: {str(e)}"
        })

def test_ai_connection():
    """Test the AI API connection."""
    test_prompt = "Reply with the following exact JSON: {\"status\": \"connected\", \"message\": \"AI API connection successful\"}"
    
    try:
        response = call_ai_api(test_prompt)
        debug_print(f"AI API test response: {response}")
        
        # Try to parse as JSON to verify format
        try:
            json_response = json.loads(response)
            if "status" in json_response and json_response["status"] == "connected":
                return True
            return False
        except json.JSONDecodeError:
            return False
    except Exception as e:
        debug_print(f"AI API connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Run a test if this file is executed directly
    if test_ai_connection():
        print("AI API connection test passed!")
    else:
        print("AI API connection test failed!")