"""
Embedding manager for handling all embedding operations.
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path

from core.logging_config import get_logger
from core.openai_client import EnhancedOpenAIClient

logger = get_logger(__name__)

class EmbeddingManager:
    """Manager for handling all embedding operations."""
    
    def __init__(self):
        """Initialize the embedding manager."""
        self.client = EnhancedOpenAIClient()
        self._cache = {}
        self._cache_file = Path("cache/embeddings.json")
        self._cache_file.parent.mkdir(exist_ok=True)
        self._load_cache()
    
    def _load_cache(self):
        """Load embeddings from cache file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, 'r') as f:
                    self._cache = json.load(f)
                logger.info("Embedding cache initialized", 
                          extra={"count": len(self._cache)})
        except Exception as e:
            logger.error("Error loading embedding cache", 
                        extra={"error": str(e)})
            self._cache = {}
    
    def _save_cache(self):
        """Save embeddings to cache file."""
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            logger.error("Error saving embedding cache", 
                        extra={"error": str(e)})
    
    def _prune_cache(self, max_size: int = 1000):
        """
        Prune the cache to maintain a maximum size.
        
        Args:
            max_size: Maximum number of entries to keep.
        """
        if len(self._cache) > max_size:
            # Sort by last accessed time
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1].get('last_accessed', 0)
            )
            # Keep only the most recently accessed items
            self._cache = dict(sorted_items[-max_size:])
            logger.debug("Pruned embedding cache", 
                        extra={"remaining_count": len(self._cache)})
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding for a text.
        
        Args:
            text: Text to get embedding for.
            
        Returns:
            Optional[np.ndarray]: Embedding vector.
        """
        try:
            # Check cache first
            if text in self._cache:
                self._cache[text]['last_accessed'] = time.time()
                return np.array(self._cache[text]['embedding'])
            
            # Generate new embedding
            embedding = self.client.get_embedding(text)
            if embedding is not None:
                # Add to cache
                self._cache[text] = {
                    'embedding': embedding.tolist(),
                    'last_accessed': time.time()
                }
                self._prune_cache()
                self._save_cache()
                return embedding
            
            return None
            
        except Exception as e:
            logger.error("Error generating embedding", 
                        extra={
                            "text": text[:100],  # Log first 100 chars
                            "error": str(e)
                        })
            return None
    
    def get_batch_embeddings(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """
        Get embeddings for a batch of texts.
        
        Args:
            texts: List of texts to get embeddings for.
            
        Returns:
            Dict[str, np.ndarray]: Dictionary mapping texts to their embeddings.
        """
        try:
            # Filter out empty texts
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding")
                return {}
            
            # Check cache first
            cached_embeddings = {}
            texts_to_generate = []
            
            for text in valid_texts:
                if text in self._cache:
                    self._cache[text]['last_accessed'] = time.time()
                    cached_embeddings[text] = np.array(self._cache[text]['embedding'])
                else:
                    texts_to_generate.append(text)
            
            # Generate embeddings for uncached texts
            if texts_to_generate:
                logger.info("Generating batch embeddings", 
                           extra={"count": len(texts_to_generate)})
                new_embeddings = self.client.get_batch_embeddings(texts_to_generate)
                
                # Add new embeddings to cache
                for text, embedding in zip(texts_to_generate, new_embeddings):
                    if embedding is not None:
                        self._cache[text] = {
                            'embedding': embedding.tolist(),
                            'last_accessed': time.time()
                        }
                        cached_embeddings[text] = embedding
            
            # Prune and save cache
            self._prune_cache()
            self._save_cache()
            
            return cached_embeddings
            
        except Exception as e:
            logger.error("Error generating batch embeddings", 
                        extra={"error": str(e)})
            return {} 