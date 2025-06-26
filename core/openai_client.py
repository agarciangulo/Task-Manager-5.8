"""
OpenAI API integration for Task Manager with throttling and retries.
Handles embeddings and AI-generated insights.
"""
import os
import sqlite3
import pickle
import traceback
from hashlib import md5
from datetime import datetime
import time
import random
import numpy as np
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    OPENAI_API_KEY, 
    EMBEDDING_CACHE_PATH, 
    EMBEDDING_MODEL, 
    CHAT_MODEL, 
    DEBUG_MODE,
    MIN_TASK_LENGTH,
    MAX_CACHE_ENTRIES,
    AI_PROVIDER
)

# Only import OpenAI if we're using it
if AI_PROVIDER == 'openai':
    from openai import OpenAI

logger = logging.getLogger(__name__)

# OPTIMIZATION: Enhanced OpenAI client with retries and rate limiting
class EnhancedOpenAIClient:
    """OpenAI client with retries, rate limiting, and concurrency control."""
    
    def __init__(self):
        """Initialize the OpenAI client with rate limiting and retries."""
        self.max_retries = 3
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit vocabulary size
            min_df=1,  # Include terms that appear in at least 1 document
            max_df=1.0,  # Include terms that appear in at most 100% of documents
            norm='l2'  # Normalize vectors to unit length
        )
        if AI_PROVIDER == 'openai':
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.client = None
        
        self.embeddings_cache = {}
        
    def _wait_if_needed(self):
        """Wait if needed to respect rate limits."""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            if DEBUG_MODE:
                print(f"Rate limiting: Waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def embeddings_create(self, text: str) -> List[float]:
        """Create embeddings using TF-IDF vectorizer."""
        try:
            # Transform the text into TF-IDF vector
            vector = self.vectorizer.fit_transform([text])
            # Convert to dense array and normalize
            embedding = vector.toarray()[0]
            # Ensure the vector has the correct length
            if len(embedding) < 1000:
                embedding = np.pad(embedding, (0, 1000 - len(embedding)))
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            return [0.0] * 1000  # Return zero vector as fallback
            
    def embeddings_create_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a batch of texts."""
        try:
            # Transform all texts at once
            vectors = self.vectorizer.fit_transform(texts)
            # Convert to dense arrays and normalize
            embeddings = vectors.toarray()
            # Normalize each vector
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = np.divide(embeddings, norms, where=norms>0)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {str(e)}")
            return [[0.0] * 1000] * len(texts)  # Return zero vectors as fallback
                    
    def chat_completions_create(self, **kwargs):
        """Create chat completions with retries and rate limiting."""
        for attempt in range(self.max_retries + 1):
            try:
                self._wait_if_needed()
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < self.max_retries:
                    # Rate limit error - implement exponential backoff
                    sleep_time = (2 ** attempt) + random.random()
                    if DEBUG_MODE:
                        print(f"Rate limited on attempt {attempt+1}. Retrying in {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    continue
                elif attempt < self.max_retries:
                    # Other error - retry with shorter backoff
                    sleep_time = (attempt + 1) + random.random()
                    if DEBUG_MODE:
                        print(f"API error on attempt {attempt+1}: {e}. Retrying in {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    continue
                else:
                    # Max retries exceeded
                    raise
                    
    def completions_create(self, **kwargs):
        """Create completions with retries and rate limiting."""
        return self.chat_completions_create(**kwargs)

    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.embeddings_create(text)
        return np.array(embedding)

    def get_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        embeddings = self.embeddings_create_batch(texts)
        return [np.array(e) for e in embeddings]

# Initialize enhanced OpenAI client only if using OpenAI
client = EnhancedOpenAIClient() if AI_PROVIDER == 'openai' else None

def setup_embedding_cache():
    """Initialize the SQLite-based embedding cache."""
    # Create database if it doesn't exist
    conn = sqlite3.connect(EMBEDDING_CACHE_PATH)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        text_hash TEXT PRIMARY KEY,
        text TEXT,
        embedding BLOB,
        last_used TIMESTAMP
    )
    ''')
    
    # Create index for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_used ON embeddings(last_used)')
    
    # Check existing entries count
    cursor.execute('SELECT COUNT(*) FROM embeddings')
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    # Only log if there are actually entries (to avoid confusion)
    if count > 0:
        print(f"✅ SQLite embedding cache initialized with {count} existing entries")
    else:
        # Suppress the "0 entries" message since it's misleading
        # The actual similarity matching uses Chroma, not this SQLite cache
        pass
    
    return EMBEDDING_CACHE_PATH

# Initialize the cache on module load
setup_embedding_cache()

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def get_cached_embedding(text):
    """Get embedding for a single text, using cache if available."""
    if not text or not isinstance(text, str) or len(text.strip()) < MIN_TASK_LENGTH:
        return None

    text_hash = md5(text.encode()).hexdigest()
    
    # Connect to SQLite
    conn = sqlite3.connect(EMBEDDING_CACHE_PATH)
    cursor = conn.cursor()
    
    # Look for cache hit
    cursor.execute('SELECT embedding FROM embeddings WHERE text_hash = ?', (text_hash,))
    result = cursor.fetchone()
    
    if result:
        # Update last_used timestamp
        cursor.execute('UPDATE embeddings SET last_used = ? WHERE text_hash = ?', 
                      (datetime.now().isoformat(), text_hash))
        conn.commit()
        embedding = pickle.loads(result[0])
        conn.close()
        return embedding

    # Cache miss - get from OpenAI
    try:
        response = client.embeddings_create(
            text=text
        )
        embedding = response
        
        # Store in cache
        cursor.execute(
            'INSERT INTO embeddings (text_hash, text, embedding, last_used) VALUES (?, ?, ?, ?)',
            (text_hash, text, pickle.dumps(embedding), datetime.now().isoformat())
        )
        
        # Check if cache size is too large and prune if needed
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        count = cursor.fetchone()[0]
        
        if count > MAX_CACHE_ENTRIES:
            # Delete oldest entries
            prune_count = count - MAX_CACHE_ENTRIES
            cursor.execute(
                'DELETE FROM embeddings WHERE text_hash IN (SELECT text_hash FROM embeddings ORDER BY last_used ASC LIMIT ?)',
                (prune_count,)
            )
            debug_print(f"Pruned {prune_count} entries from embedding cache")
        
        conn.commit()
        conn.close()
        return embedding
    except Exception as e:
        conn.close()
        debug_print(f"Error getting embedding: {e}")
        return None

def get_batch_embeddings(texts, force_refresh=False):
    """
    Get embeddings for multiple texts with optimized batching and caching.
    
    Args:
        texts: List of texts to embed
        force_refresh: Whether to ignore cache and fetch fresh embeddings
        
    Returns:
        Dict mapping texts to their embeddings
    """
    if not texts:
        return {}

    # Filter out invalid texts
    valid_texts = [t for t in texts if isinstance(t, str) and len(t.strip()) >= MIN_TASK_LENGTH]
    if not valid_texts:
        return {}
        
    # Use sets to remove duplicates - this reduces API calls
    unique_texts = list(set(valid_texts))
    print(f"Processing {len(unique_texts)} unique texts out of {len(valid_texts)} total")

    # Create lookup dictionaries
    hash_lookup = {md5(t.encode()).hexdigest(): t for t in unique_texts}
    embeddings = {}
    texts_to_request = []
    text_hashes_to_request = []

    # Connect to SQLite
    conn = sqlite3.connect(EMBEDDING_CACHE_PATH)
    cursor = conn.cursor()
    
    # If force refresh, skip cache lookup
    if not force_refresh:
        # Check cache first for all texts
        for text_hash, text in hash_lookup.items():
            cursor.execute('SELECT embedding FROM embeddings WHERE text_hash = ?', (text_hash,))
            result = cursor.fetchone()
            
            if result:
                # Update last_used timestamp
                cursor.execute('UPDATE embeddings SET last_used = ? WHERE text_hash = ?', 
                            (datetime.now().isoformat(), text_hash))
                embeddings[text_hash] = pickle.loads(result[0])
            else:
                texts_to_request.append(text)
                text_hashes_to_request.append(text_hash)
    else:
        # Skip cache for all texts if force_refresh
        texts_to_request = list(unique_texts)
        text_hashes_to_request = list(hash_lookup.keys())
    
    conn.commit()

    # Only call API if we have texts not in cache
    if texts_to_request:
        try:
            # OPTIMIZATION: Use larger batch size to reduce number of API calls
            batch_size = 1000  # Increased from 100 (adjust based on API limits)
            
            for i in range(0, len(texts_to_request), batch_size):
                batch = texts_to_request[i:i+batch_size]
                batch_hashes = text_hashes_to_request[i:i+batch_size]

                print(f"Processing batch {i//batch_size + 1} with {len(batch)} texts")
                batch_embeddings = client.embeddings_create_batch(batch)

                # Store new embeddings in cache and results
                for j, embedding in enumerate(batch_embeddings):
                    text_hash = batch_hashes[j]
                    text = batch[j]
                    
                    cursor.execute(
                        'INSERT OR REPLACE INTO embeddings (text_hash, text, embedding, last_used) VALUES (?, ?, ?, ?)',
                        (text_hash, text, pickle.dumps(embedding), datetime.now().isoformat())
                    )
                    
                    embeddings[text_hash] = embedding
            
            # Check if cache size is too large and prune if needed
            cursor.execute('SELECT COUNT(*) FROM embeddings')
            count = cursor.fetchone()[0]
            
            if count > MAX_CACHE_ENTRIES:
                # Delete oldest entries
                prune_count = count - MAX_CACHE_ENTRIES
                cursor.execute(
                    'DELETE FROM embeddings WHERE text_hash IN (SELECT text_hash FROM embeddings ORDER BY last_used ASC LIMIT ?)',
                    (prune_count,)
                )
                debug_print(f"Pruned {prune_count} entries from embedding cache")
            
            conn.commit()
        except Exception as e:
            debug_print(f"Error in batch embeddings: {e}")
    
    conn.close()

    # Reconstruct the result mapping to include all original texts
    # This handles any duplicates in the original list
    result = {}
    for text in valid_texts:
        text_hash = md5(text.encode()).hexdigest()
        if text_hash in embeddings:
            result[text] = embeddings[text_hash]
    
    return result

def get_coaching_insight(person_name, tasks, recent_tasks, peer_feedback):
    """Generate coaching insights using OpenAI with optimized prompting."""
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

    feedback_prompt = f"""
    You are CoachAI, a friendly and helpful workplace assistant who offers coaching insights in a conversational, supportive tone.

    ANALYZE THE FOLLOWING DATA FOR {person_name}:
    1. Current tasks: {tasks}
    2. Task history (14 days): {recent_tasks[['task', 'status', 'employee', 'date', 'category']].to_dict(orient='records') if not recent_tasks.empty else []}
    3. Basic statistics: {basic_stats}
    4. Peer feedback: {peer_feedback}

    FIRST, ANALYZE THIS DATA TO IDENTIFY PATTERNS:
    - Task completion rates and patterns
    - Work distribution across different projects
    - Recent productivity trends
    - Task complexity and priority handling
    - Collaboration patterns

    THEN, PROVIDE INSIGHTS ON THE ANALYSIS IN A CONVERSATIONAL TONE, INCLUDING:
    1. A specific strength or accomplishment to recognize
    2. Specific instances that require their immediate attention
    3. A friendly, practical, and tactical suggestion that could help them improve

    IMPORTANT STYLE GUIDANCE:
    - Write as a helpful colleague, not a formal report
    - Use personal language ("I notice...", "You're doing well at...")
    - Keep it brief and conversational (3-4 sentences per insight)
    - Avoid technical terms like "metadata analysis" or "velocity metrics"
    - Don't list categories like "STRENGTH:" or "OPPORTUNITY:" - just flow naturally
    - Sound encouraging and supportive throughout
    """

    try:
        response = client.chat_completions_create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": feedback_prompt}],
            temperature=0.4
        )
        reflection = response.choices[0].message.content
        return reflection
    except Exception as e:
        debug_print(f"Error generating coaching insights: {e}")
        return "Unable to generate coaching insights at this time."

def get_project_insight(selected_category, filtered_tasks):
    """Generate project insights using OpenAI with optimized prompting."""
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

    # AI-generated insight based on tasks in the category
    project_prompt = f"""
    You are ProjectAnalyst, a strategic advisor on project management and team productivity.

    ANALYZE PROJECT '{selected_category}' TASKS:
    {filtered_tasks[['task', 'status', 'employee', 'date']].to_dict(orient='records')}

    PROJECT METADATA:
    {basic_stats}

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

    try:
        response = client.chat_completions_create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": project_prompt}],
            temperature=0.5
        )
        insight = response.choices[0].message.content
        return insight.strip()
    except Exception as e:
        debug_print(f"Error generating project insight: {e}")
        return f"⚠️ Unable to generate AI insight: {e}"

# Utility function to combine multiple API calls
def batch_api_requests(prompts, model=CHAT_MODEL, temperature=0.4):
    """
    Batch multiple prompts into fewer API calls.
    
    Args:
        prompts: List of prompt strings or prompt dicts
        model: Model to use
        temperature: Temperature setting
        
    Returns:
        List of response strings
    """
    if not prompts:
        return []
        
    # Convert simple strings to message objects
    messages_list = []
    for prompt in prompts:
        if isinstance(prompt, str):
            messages_list.append([{"role": "user", "content": prompt}])
        else:
            messages_list.append(prompt)
    
    results = []
    
    # Process in batches of 5 to avoid overwhelming the API
    batch_size = 5
    for i in range(0, len(messages_list), batch_size):
        batch = messages_list[i:i+batch_size]
        batch_results = []
        
        # Process batch in parallel (API will automatically rate limit)
        for messages in batch:
            try:
                response = client.chat_completions_create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
                batch_results.append(response.choices[0].message.content)
            except Exception as e:
                debug_print(f"Error in batch API request: {e}")
                batch_results.append(f"Error: {str(e)}")
                
        results.extend(batch_results)
    
    return results