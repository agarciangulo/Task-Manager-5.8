"""
Embedding generation and management using OpenAI.
"""
import os
import json
import sqlite3
import pickle
from hashlib import md5
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    OPENAI_API_KEY,
    EMBEDDING_CACHE_PATH,
    EMBEDDING_MODEL,
    DEBUG_MODE,
    MIN_TASK_LENGTH,
    MAX_CACHE_ENTRIES,
    AI_PROVIDER
)

from openai import OpenAI

class EmbeddingProvider:
    """Base class for embedding providers."""
    def __init__(self, cache_path: str = EMBEDDING_CACHE_PATH):
        self.cache_path = cache_path
        self._setup_cache()
    
    def _setup_cache(self):
        """Initialize the SQLite-based embedding cache."""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            text_hash TEXT PRIMARY KEY,
            text TEXT,
            embedding BLOB,
            provider TEXT,
            last_used TIMESTAMP
        )
        ''')
        
        # Create indices if they don't exist
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_used ON embeddings(last_used)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_provider ON embeddings(provider)')
        
        # Count existing entries
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        count = cursor.fetchone()[0]
        print(f"Embedding cache initialized with {count} existing entries")
        
        conn.commit()
        conn.close()
    
    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache if available."""
        if not text or not isinstance(text, str) or len(text.strip()) < MIN_TASK_LENGTH:
            return None

        text_hash = md5(text.encode()).hexdigest()
        
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT embedding FROM embeddings WHERE text_hash = ? AND provider = ?',
            (text_hash, self.provider_name)
        )
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                'UPDATE embeddings SET last_used = ? WHERE text_hash = ?',
                (datetime.now().isoformat(), text_hash)
            )
            conn.commit()
            embedding = pickle.loads(result[0])
            conn.close()
            return embedding
        
        conn.close()
        return None
    
    def _cache_embedding(self, text: str, embedding: np.ndarray):
        """Cache an embedding."""
        text_hash = md5(text.encode()).hexdigest()
        
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR REPLACE INTO embeddings (text_hash, text, embedding, provider, last_used) VALUES (?, ?, ?, ?, ?)',
            (text_hash, text, pickle.dumps(embedding), self.provider_name, datetime.now().isoformat())
        )
        
        # Check cache size and prune if needed
        cursor.execute('SELECT COUNT(*) FROM embeddings WHERE provider = ?', (self.provider_name,))
        count = cursor.fetchone()[0]
        
        if count > MAX_CACHE_ENTRIES:
            prune_count = count - MAX_CACHE_ENTRIES
            cursor.execute(
                'DELETE FROM embeddings WHERE text_hash IN (SELECT text_hash FROM embeddings WHERE provider = ? ORDER BY last_used ASC LIMIT ?)',
                (self.provider_name, prune_count)
            )
        
        conn.commit()
        conn.close()
    
    def get_embedding(self, text: str, force_refresh: bool = False) -> Optional[np.ndarray]:
        """Get embedding for a single text."""
        if not force_refresh:
            cached = self._get_cached_embedding(text)
            if cached is not None:
                return cached
        
        embedding = self._generate_embedding(text)
        if embedding is not None:
            self._cache_embedding(text, embedding)
        return embedding
    
    def get_batch_embeddings(self, texts: List[str], force_refresh: bool = False) -> Dict[str, np.ndarray]:
        """Get embeddings for multiple texts."""
        if not texts:
            return {}
        
        valid_texts = [t for t in texts if isinstance(t, str) and len(t.strip()) >= MIN_TASK_LENGTH]
        if not valid_texts:
            return {}
        
        unique_texts = list(set(valid_texts))
        result = {}
        
        # Check cache first
        if not force_refresh:
            for text in unique_texts:
                cached = self._get_cached_embedding(text)
                if cached is not None:
                    result[text] = cached
        
        # Generate embeddings for remaining texts
        remaining_texts = [t for t in unique_texts if t not in result]
        if remaining_texts:
            new_embeddings = self._generate_batch_embeddings(remaining_texts)
            for text, embedding in zip(remaining_texts, new_embeddings):
                if embedding is not None:
                    result[text] = embedding
                    self._cache_embedding(text, embedding)
        
        return result

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.provider_name = "openai"
        self.client = OpenAI(api_key=api_key or OPENAI_API_KEY)
        self.model = EMBEDDING_MODEL
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error generating embedding: {e}")
            return None
    
    def _generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [np.array(item.embedding) for item in response.data]
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)

# Initialize the default provider
_provider = OpenAIEmbeddingProvider()

def get_embedding(text: str, force_refresh: bool = False) -> Optional[np.ndarray]:
    """Get embedding for a text using the default provider."""
    return _provider.get_embedding(text, force_refresh)

def get_batch_embeddings(texts: List[str], force_refresh: bool = False) -> Dict[str, np.ndarray]:
    """Get embeddings for multiple texts using the default provider."""
    return _provider.get_batch_embeddings(texts, force_refresh)
