"""
Simplified Chroma-based embedding manager without sentence-transformers.
Uses Chroma's built-in embedding capabilities for better compatibility.
"""
import os
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import chromadb
from chromadb.config import Settings
import logging

from core.logging_config import get_logger

logger = get_logger(__name__)

class SimpleChromaEmbeddingManager:
    """
    Simplified Chroma embedding manager using built-in embeddings.
    
    Features:
    - Persistent vector database with Chroma
    - Uses Chroma's default embedding function
    - Optimized similarity search
    - Automatic cache management
    - No external embedding dependencies
    """
    
    def __init__(self, 
                 collection_name: str = "task_embeddings",
                 persist_directory: str = "chroma_db"):
        """
        Initialize the simplified Chroma embedding manager.
        
        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist Chroma data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize Chroma client
        self._init_chroma_client()
        
        # Initialize collection
        self._init_collection()
        
        logger.info("SimpleChromaEmbeddingManager initialized successfully")
    
    def _init_chroma_client(self):
        """Initialize Chroma client with persistent storage."""
        try:
            # Create persist directory if it doesn't exist
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize Chroma client with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"Chroma client initialized with persist directory: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chroma client: {e}")
            raise
    
    def _init_collection(self):
        """Initialize or get the Chroma collection with default embedding function."""
        try:
            # Get or create collection with default embedding function
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Task embeddings for similarity matching",
                    "embedding_function": "default",
                    "created_at": time.time()
                }
            )
            
            # Get collection info
            count = self.collection.count()
            logger.info(f"Collection '{self.collection_name}' initialized with {count} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding for a single text using Chroma's built-in embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Optional[np.ndarray]: Embedding vector
        """
        try:
            if not text or not text.strip():
                return None
            
            # Check if text already exists in collection
            existing = self.collection.get(
                where={"text": text},
                include=["embeddings"]
            )
            
            if existing["ids"] is not None and len(existing["ids"]) > 0:
                # Return existing embedding
                embedding = np.array(existing["embeddings"][0])
                logger.debug(f"Retrieved cached embedding for text: {text[:50]}...")
                return embedding
            
            # Generate new embedding by adding to collection
            self._add_to_collection([text])
            
            # Retrieve the embedding we just added
            new_embedding = self.collection.get(
                where={"text": text},
                include=["embeddings"]
            )
            
            if new_embedding["embeddings"] is not None and len(new_embedding["embeddings"]) > 0:
                embedding = np.array(new_embedding["embeddings"][0])
                logger.debug(f"Generated and stored new embedding for text: {text[:50]}...")
                return embedding
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting embedding for text: {e}")
            return None
    
    def get_batch_embeddings(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """
        Get embeddings for multiple texts with optimized batching.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Dict[str, np.ndarray]: Dictionary mapping texts to embeddings
        """
        try:
            if not texts:
                return {}
            
            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                return {}
            
            # Check for existing embeddings
            existing_embeddings = {}
            texts_to_generate = []
            
            # Query existing embeddings in batches
            batch_size = 100  # Chroma batch limit
            for i in range(0, len(valid_texts), batch_size):
                batch_texts = valid_texts[i:i + batch_size]
                
                # Get existing embeddings for this batch
                existing = self.collection.get(
                    where={"text": {"$in": batch_texts}},
                    include=["embeddings", "metadatas"]
                )
                
                # Map existing embeddings
                if existing["metadatas"] is not None and len(existing["metadatas"]) > 0:
                    for j, text in enumerate(batch_texts):
                        # Find the text in existing metadata
                        text_found = False
                        for k, metadata in enumerate(existing["metadatas"]):
                            if metadata.get("text") == text:
                                existing_embeddings[text] = np.array(existing["embeddings"][k])
                                text_found = True
                                break
                        if not text_found:
                            texts_to_generate.append(text)
                else:
                    # No existing embeddings found
                    texts_to_generate.extend(batch_texts)
            
            # Generate embeddings for new texts
            if texts_to_generate:
                logger.info(f"Generating embeddings for {len(texts_to_generate)} new texts")
                
                # Add new texts to collection (Chroma will generate embeddings automatically)
                self._add_to_collection(texts_to_generate)
                
                # Retrieve the new embeddings
                new_embeddings_data = self.collection.get(
                    where={"text": {"$in": texts_to_generate}},
                    include=["embeddings", "metadatas"]
                )
                
                # Add to results
                if new_embeddings_data["metadatas"] is not None and len(new_embeddings_data["metadatas"]) > 0:
                    for i, text in enumerate(texts_to_generate):
                        # Find the text in new metadata
                        for k, metadata in enumerate(new_embeddings_data["metadatas"]):
                            if metadata.get("text") == text:
                                existing_embeddings[text] = np.array(new_embeddings_data["embeddings"][k])
                                break
            
            logger.info(f"Retrieved {len(existing_embeddings)} embeddings")
            return existing_embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embeddings: {e}")
            return {}
    
    def find_similar(self, 
                    query_text: str, 
                    texts: List[str], 
                    top_k: int = 5,
                    threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find similar texts using Chroma's optimized similarity search.
        
        Args:
            query_text: Text to find similarities for
            texts: List of texts to search in
            top_k: Number of top results to return
            threshold: Similarity threshold (0-1)
            
        Returns:
            List[Dict[str, Any]]: List of similar texts with scores
        """
        try:
            if not query_text or not texts:
                return []
            
            # Ensure query text is in collection
            query_embedding = self.get_embedding(query_text)
            if query_embedding is None:
                return []
            
            # Ensure all texts are in collection
            text_embeddings = self.get_batch_embeddings(texts)
            if not text_embeddings:
                return []
            
            # Use Chroma's query method directly
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(top_k, len(texts)),
                where={"text": {"$in": texts}},
                include=["distances", "documents"]
            )
            
            # Process results
            similar_texts = []
            if results["documents"] is not None and results["distances"] is not None:
                for i, (text, distance) in enumerate(zip(
                    results["documents"][0], 
                    results["distances"][0]
                )):
                    # Convert distance to similarity score (Chroma uses L2 distance)
                    # Normalize to 0-1 range where 1 is most similar
                    similarity = 1.0 / (1.0 + distance)
                    
                    if similarity >= threshold:
                        similar_texts.append({
                            "text": text,
                            "similarity": similarity,
                            "distance": distance,
                            "rank": i + 1
                        })
            
            return similar_texts
                    
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def find_similar_tasks(self, 
                          new_task: Dict[str, Any], 
                          existing_tasks: List[Dict[str, Any]], 
                          top_k: int = 5,
                          threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find similar tasks using optimized similarity search.
        
        Args:
            new_task: New task to find similarities for
            existing_tasks: List of existing tasks to search in
            top_k: Number of top results to return
            threshold: Similarity threshold
            
        Returns:
            List[Dict[str, Any]]: List of similar tasks with scores
        """
        try:
            if not new_task or not existing_tasks:
                return []
            
            # Extract task texts
            new_task_text = new_task.get("task", "")
            existing_task_texts = [task.get("task", "") for task in existing_tasks]
            
            # Find similar texts
            similar_texts = self.find_similar(
                new_task_text, 
                existing_task_texts, 
                top_k, 
                threshold
            )
            
            # Map back to full task objects
            similar_tasks = []
            for result in similar_texts:
                # Find the corresponding task object
                for task in existing_tasks:
                    if task.get("task", "") == result["text"]:
                        similar_tasks.append({
                            "task": task,
                            "similarity": result["similarity"],
                            "distance": result["distance"],
                            "rank": result["rank"]
                        })
                        break
            
            return similar_tasks
            
        except Exception as e:
            logger.error(f"Error finding similar tasks: {e}")
            return []
    
    def _add_to_collection(self, texts: List[str]):
        """Add texts to the collection (Chroma will generate embeddings automatically)."""
        try:
            if not texts:
                return
            
            # Generate unique IDs
            ids = [f"task_{uuid.uuid4().hex}" for _ in texts]
            
            # Add to collection (Chroma will handle embedding generation)
            self.collection.add(
                documents=texts,
                metadatas=[{"text": text} for text in texts],
                ids=ids
            )
            
            logger.debug(f"Added {len(texts)} texts to collection")
            
        except Exception as e:
            logger.error(f"Error adding to collection: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            
            # Get sample embeddings to determine dimension
            sample = self.collection.peek(limit=1)
            dimension = 0
            if sample["embeddings"] is not None and len(sample["embeddings"]) > 0:
                dimension = len(sample["embeddings"][0])
            
            return {
                "total_embeddings": count,
                "embedding_dimension": dimension,
                "embedding_function": "chroma_default",
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all embeddings from the collection."""
        try:
            self.chroma_client.delete_collection(self.collection_name)
            self._init_collection()
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
    
    def migrate_from_old_cache(self, old_embeddings: Dict[str, Any]):
        """
        Migrate embeddings from old cache format to Chroma.
        Note: This will regenerate embeddings using Chroma's default function.
        
        Args:
            old_embeddings: Dictionary of old embeddings
        """
        try:
            if not old_embeddings:
                return
            
            texts = list(old_embeddings.keys())
            
            # Add texts to collection (Chroma will generate new embeddings)
            self._add_to_collection(texts)
            
            logger.info(f"Migrated {len(texts)} texts from old cache (embeddings regenerated)")
            
        except Exception as e:
            logger.error(f"Error migrating from old cache: {e}") 