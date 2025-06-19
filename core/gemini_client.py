"""
Gemini API integration for Task Manager with throttling and retries.
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
    GEMINI_API_KEY, 
    EMBEDDING_CACHE_PATH, 
    EMBEDDING_MODEL, 
    CHAT_MODEL, 
    DEBUG_MODE,
    MIN_TASK_LENGTH,
    MAX_CACHE_ENTRIES,
    AI_PROVIDER,
    GEMINI_MODEL,
    GEMINI_EMBEDDING_MODEL
)

# Only import Google AI if we're using Gemini
if AI_PROVIDER == 'gemini':
    import google.generativeai as genai

logger = logging.getLogger(__name__)

# OPTIMIZATION: Enhanced Gemini client with retries and rate limiting
class EnhancedGeminiClient:
    """Gemini client with retries, rate limiting, and concurrency control."""
    
    def __init__(self):
        """Initialize the Gemini client with rate limiting and retries."""
        self.max_retries = 3
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit vocabulary size
            min_df=1,  # Include terms that appear in at least 1 document
            max_df=1.0,  # Include terms that appear in at most 100% of documents
            norm='l2'  # Normalize vectors to unit length
        )
        if AI_PROVIDER == 'gemini':
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            self.embedding_model = genai.GenerativeModel(GEMINI_EMBEDDING_MODEL)
        else:
            self.model = None
            self.embedding_model = None
        
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
                    
    def generate_content(self, prompt: str, **kwargs):
        """Generate content using Gemini's native API."""
        for attempt in range(self.max_retries + 1):
            try:
                self._wait_if_needed()
                
                # Get parameters
                temperature = kwargs.get('temperature', 0.7)
                max_tokens = kwargs.get('max_tokens', 1000)
                
                # Generate response using Gemini's native API
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                
                return response.text
                
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

    def chat_completions_create(self, **kwargs):
        """Legacy method for OpenAI compatibility - converts to Gemini format."""
        messages = kwargs.get('messages', [])
        prompt = self._convert_messages_to_prompt(messages)
        response_text = self.generate_content(prompt, **kwargs)
        
        # Return in OpenAI format for compatibility
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': response_text
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
        }

    def completions_create(self, **kwargs):
        """Create completions with retries and rate limiting."""
        return self.chat_completions_create(**kwargs)

    def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert OpenAI message format to Gemini prompt format."""
        prompt = ""
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"User: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
        
        return prompt.strip()

    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.embeddings_create(text)
        return np.array(embedding)

    def get_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        embeddings = self.embeddings_create_batch(texts)
        return [np.array(e) for e in embeddings]

# Initialize enhanced Gemini client only if using Gemini
client = EnhancedGeminiClient() if AI_PROVIDER == 'gemini' else None

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
    
    print(f"✅ Embedding cache initialized with {count} existing entries")
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
        debug_print(f"Cache hit for text: {text[:50]}...")
        return embedding
    
    # Cache miss - get from Gemini
    debug_print(f"Cache miss for text: {text[:50]}...")
    
    try:
        if client:
            embedding = client.embeddings_create(text)
        else:
            # Fallback to TF-IDF if no client
            vectorizer = TfidfVectorizer(max_features=1000)
            vector = vectorizer.fit_transform([text])
            embedding = vector.toarray()[0].tolist()
            if len(embedding) < 1000:
                embedding = embedding + [0.0] * (1000 - len(embedding))
        
        # Store in cache
        cursor.execute('''
        INSERT OR REPLACE INTO embeddings (text_hash, text, embedding, last_used)
        VALUES (?, ?, ?, ?)
        ''', (text_hash, text, pickle.dumps(embedding), datetime.now().isoformat()))
        
        # Clean up old entries if cache is full
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        count = cursor.fetchone()[0]
        
        if count > MAX_CACHE_ENTRIES:
            cursor.execute('''
            DELETE FROM embeddings WHERE text_hash NOT IN (
                SELECT text_hash FROM embeddings 
                ORDER BY last_used DESC 
                LIMIT ?
            )
            ''', (MAX_CACHE_ENTRIES,))
        
        conn.commit()
        conn.close()
        
        return embedding
        
    except Exception as e:
        conn.close()
        logger.error(f"Error getting embedding: {str(e)}")
        return [0.0] * 1000  # Return zero vector as fallback

def get_batch_embeddings(texts, force_refresh=False):
    """Get embeddings for multiple texts, using cache when possible."""
    if not texts:
        return []
    
    embeddings = []
    texts_to_embed = []
    text_indices = []
    
    if not force_refresh:
        # Check cache for each text
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str) or len(text.strip()) < MIN_TASK_LENGTH:
                embeddings.append([0.0] * 1000)
                continue
                
            cached_embedding = get_cached_embedding(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                texts_to_embed.append(text)
                text_indices.append(i)
                embeddings.append(None)  # Placeholder
    else:
        # Force refresh all
        texts_to_embed = texts
        text_indices = list(range(len(texts)))
        embeddings = [None] * len(texts)
    
    # Get embeddings for texts not in cache
    if texts_to_embed:
        try:
            if client:
                batch_embeddings = client.embeddings_create_batch(texts_to_embed)
            else:
                # Fallback to TF-IDF
                vectorizer = TfidfVectorizer(max_features=1000)
                vectors = vectorizer.fit_transform(texts_to_embed)
                batch_embeddings = vectors.toarray().tolist()
                # Pad vectors to 1000 dimensions
                for i, embedding in enumerate(batch_embeddings):
                    if len(embedding) < 1000:
                        batch_embeddings[i] = embedding + [0.0] * (1000 - len(embedding))
            
            # Store in cache and update results
            conn = sqlite3.connect(EMBEDDING_CACHE_PATH)
            cursor = conn.cursor()
            
            for i, (text, embedding) in enumerate(zip(texts_to_embed, batch_embeddings)):
                text_hash = md5(text.encode()).hexdigest()
                
                # Store in cache
                cursor.execute('''
                INSERT OR REPLACE INTO embeddings (text_hash, text, embedding, last_used)
                VALUES (?, ?, ?, ?)
                ''', (text_hash, text, pickle.dumps(embedding), datetime.now().isoformat()))
                
                # Update results
                embeddings[text_indices[i]] = embedding
            
            # Clean up old entries if cache is full
            cursor.execute('SELECT COUNT(*) FROM embeddings')
            count = cursor.fetchone()[0]
            
            if count > MAX_CACHE_ENTRIES:
                cursor.execute('''
                DELETE FROM embeddings WHERE text_hash NOT IN (
                    SELECT text_hash FROM embeddings 
                    ORDER BY last_used DESC 
                    LIMIT ?
                )
                ''', (MAX_CACHE_ENTRIES,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting batch embeddings: {str(e)}")
            # Fill with zero vectors as fallback
            for i in text_indices:
                embeddings[i] = [0.0] * 1000
    
    return embeddings

def get_coaching_insight(person_name, tasks, recent_tasks, peer_feedback):
    """Generate coaching insights using Gemini with optimized prompting."""
    try:
        if not client:
            return "AI insights not available - no Gemini client configured."
        
        # Prepare the prompt
        prompt = f"""
        As an AI coach, analyze the following information about {person_name} and provide actionable insights:

        **Current Tasks:**
        {chr(10).join([f"- {task}" for task in tasks])}

        **Recent Completed Tasks:**
        {chr(10).join([f"- {task}" for task in recent_tasks])}

        **Peer Feedback:**
        {peer_feedback if peer_feedback else "No peer feedback available"}

        Please provide:
        1. **Strengths**: What patterns show this person's strengths?
        2. **Growth Areas**: What areas could they develop?
        3. **Recommendations**: 2-3 specific, actionable suggestions
        4. **Workload Balance**: Is their current task mix well-balanced?

        Keep your response concise, constructive, and actionable.
        """

        response = client.chat_completions_create(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        logger.error(f"Error generating coaching insight: {str(e)}")
        return f"Unable to generate coaching insights: {str(e)}"

def get_project_insight(selected_category, filtered_tasks):
    """Generate project insights using Gemini with optimized prompting."""
    try:
        if not client:
            return "AI insights not available - no Gemini client configured."
        
        # Prepare the prompt
        prompt = f"""
        As a project analyst, analyze the following tasks in the '{selected_category}' category and provide insights:

        **Tasks in {selected_category}:**
        {chr(10).join([f"- {task}" for task in filtered_tasks])}

        Please provide:
        1. **Category Overview**: What does this category focus on?
        2. **Task Patterns**: What common themes or patterns do you see?
        3. **Priority Assessment**: Which tasks seem most critical?
        4. **Resource Allocation**: Any insights about workload distribution?
        5. **Recommendations**: Suggestions for improving efficiency or outcomes

        Keep your response concise and actionable.
        """

        response = client.chat_completions_create(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        logger.error(f"Error generating project insight: {str(e)}")
        return f"Unable to generate project insights: {str(e)}"

def batch_api_requests(prompts, model=CHAT_MODEL, temperature=0.4):
    """Process multiple prompts in batch with rate limiting."""
    results = []
    
    for i, prompt in enumerate(prompts):
        try:
            if DEBUG_MODE:
                print(f"Processing prompt {i+1}/{len(prompts)}")
            
            response = client.chat_completions_create(
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=1000
            )
            
            result = response['choices'][0]['message']['content']
            results.append(result)
            
            # Rate limiting between requests
            if i < len(prompts) - 1:  # Don't sleep after the last request
                time.sleep(0.1)  # 100ms delay between requests
                
        except Exception as e:
            logger.error(f"Error processing prompt {i+1}: {str(e)}")
            results.append(f"Error: {str(e)}")
    
    return results 