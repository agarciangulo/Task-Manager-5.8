"""
Chroma-based embedding manager for improved similarity matching and performance.
"""
import os
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

from core.logging_config import get_logger

logger = get_logger(__name__)

class ChromaEmbeddingManager:
    """
    Chroma-based embedding manager for improved similarity matching.
    
    Features:
    - Persistent vector database with Chroma
    - Consistent embedding dimensions using SentenceTransformers
    - Optimized similarity search
    - Automatic cache management
    - Batch operations support
    """
    
    def __init__(self, 
                 collection_name: str = "task_embeddings",
                 model_name: str = "all-MiniLM-L6-v2",
                 persist_directory: str = "chroma_db"):
        """
        Initialize the Chroma embedding manager.
        
        Args:
            collection_name: Name of the Chroma collection
            model_name: SentenceTransformer model to use
            persist_directory: Directory to persist Chroma data
        """
        self.collection_name = collection_name
        self.model_name = model_name
        self.persist_directory = persist_directory
        
        # Initialize SentenceTransformer for consistent embeddings
        logger.info(f"Initializing SentenceTransformer with model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize Chroma client
        self._init_chroma_client()
        
        # Initialize collection
        self._init_collection()
        
        logger.info("ChromaEmbeddingManager initialized successfully")
    
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
        """Initialize or get the Chroma collection."""
        try:
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Task embeddings for similarity matching",
                    "model": self.model_name,
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
        Get embedding for a single text.
        
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
            
            if existing["ids"]:
                # Return existing embedding
                embedding = np.array(existing["embeddings"][0])
                logger.debug(f"Retrieved cached embedding for text: {text[:50]}...")
                return embedding
            
            # Generate new embedding
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            
            # Store in collection
            self._add_to_collection([text], [embedding.tolist()])
            
            logger.debug(f"Generated and stored new embedding for text: {text[:50]}...")
            return embedding
            
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
                for j, text in enumerate(batch_texts):
                    if text in existing["metadatas"]:
                        idx = existing["metadatas"].index({"text": text})
                        existing_embeddings[text] = np.array(existing["embeddings"][idx])
                    else:
                        texts_to_generate.append(text)
            
            # Generate embeddings for new texts
            if texts_to_generate:
                logger.info(f"Generating embeddings for {len(texts_to_generate)} new texts")
                
                # Generate embeddings in batches
                new_embeddings = []
                for i in range(0, len(texts_to_generate), batch_size):
                    batch_texts = texts_to_generate[i:i + batch_size]
                    batch_embeddings = self.embedding_model.encode(
                        batch_texts, 
                        convert_to_numpy=True,
                        show_progress_bar=False
                    )
                    new_embeddings.extend(batch_embeddings)
                
                # Store new embeddings
                if new_embeddings:
                    self._add_to_collection(
                        texts_to_generate,
                        [emb.tolist() for emb in new_embeddings]
                    )
                
                # Add to results
                for text, embedding in zip(texts_to_generate, new_embeddings):
                    existing_embeddings[text] = embedding
            
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
            
            # Get query embedding
            query_embedding = self.get_embedding(query_text)
            if query_embedding is None:
                return []
            
            # Get embeddings for all texts
            text_embeddings = self.get_batch_embeddings(texts)
            if not text_embeddings:
                return []
            
            # Prepare data for similarity search
            collection_texts = []
            collection_embeddings = []
            
            for text in texts:
                if text in text_embeddings:
                    collection_texts.append(text)
                    collection_embeddings.append(text_embeddings[text].tolist())
            
            if not collection_texts:
                return []
            
            # Create temporary collection for this search
            temp_collection_name = f"temp_search_{uuid.uuid4().hex[:8]}"
            temp_collection = self.chroma_client.create_collection(
                name=temp_collection_name,
                metadata={"temporary": True}
            )
            
            try:
                # Add texts to temporary collection
                temp_collection.add(
                    embeddings=collection_embeddings,
                    documents=collection_texts,
                    ids=[f"temp_{i}" for i in range(len(collection_texts))]
                )
                
                # Perform similarity search
                results = temp_collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=min(top_k, len(collection_texts)),
                    include=["distances", "documents"]
                )
                
                # Process results
                similar_texts = []
                if results["documents"] and results["distances"]:
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
                
            finally:
                # Clean up temporary collection
                try:
                    self.chroma_client.delete_collection(temp_collection_name)
                except:
                    pass
                    
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
    
    def _add_to_collection(self, texts: List[str], embeddings: List[List[float]]):
        """Add texts and embeddings to the collection."""
        try:
            if not texts or not embeddings:
                return
            
            # Generate unique IDs
            ids = [f"task_{uuid.uuid4().hex}" for _ in texts]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=[{"text": text} for text in texts],
                ids=ids
            )
            
            logger.debug(f"Added {len(texts)} embeddings to collection")
            
        except Exception as e:
            logger.error(f"Error adding to collection: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            
            # Get sample embeddings to determine dimension
            sample = self.collection.peek(limit=1)
            dimension = len(sample["embeddings"][0]) if sample["embeddings"] else 0
            
            return {
                "total_embeddings": count,
                "embedding_dimension": dimension,
                "model_name": self.model_name,
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
        
        Args:
            old_embeddings: Dictionary of old embeddings
        """
        try:
            if not old_embeddings:
                return
            
            texts = list(old_embeddings.keys())
            embeddings = []
            
            for text in texts:
                embedding_data = old_embeddings[text]
                if isinstance(embedding_data, dict) and "embedding" in embedding_data:
                    embeddings.append(embedding_data["embedding"])
                elif isinstance(embedding_data, list):
                    embeddings.append(embedding_data)
                else:
                    # Skip invalid embeddings
                    continue
            
            if embeddings:
                self._add_to_collection(texts, embeddings)
                logger.info(f"Migrated {len(texts)} embeddings from old cache")
            
        except Exception as e:
            logger.error(f"Error migrating from old cache: {e}") 