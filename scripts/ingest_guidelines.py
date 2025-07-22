#!/usr/bin/env python3
"""
Guideline Document Ingestion Pipeline for RAG System

This script processes guideline documents (.md, .pdf, .docx) and stores their embeddings
in specialized ChromaDB collections for the RAG system.

Phase 1 of RAG System Implementation
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from src.core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class GuidelineIngestionPipeline:
    """
    Pipeline for ingesting guideline documents into ChromaDB collections.
    
    Features:
    - Multi-format document processing (PDF, DOCX, Markdown)
    - Intelligent text chunking with context preservation
    - Specialized collections for technical vs process documents
    - Metadata preservation for source tracking
    """
    
    def __init__(self, 
                 guidelines_dir: str = "../docs/guidelines",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 100):
        """
        Initialize the ingestion pipeline.
        
        Args:
            guidelines_dir: Directory containing guideline documents
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.guidelines_dir = Path(guidelines_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding manager
        self.embedding_manager = SimpleChromaEmbeddingManager()
        
        # Initialize text splitters
        self._init_text_splitters()
        
        logger.info(f"GuidelineIngestionPipeline initialized for {self.guidelines_dir}")
    
    def _init_text_splitters(self):
        """Initialize text splitters for different document types."""
        # General text splitter for most documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Markdown-specific splitter for better structure preservation
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]
        )
        
        logger.info("Text splitters initialized")
    
    def _determine_collection(self, filename: str) -> str:
        """
        Determine which ChromaDB collection to use based on filename.
        
        Args:
            filename: Name of the document file
            
        Returns:
            Collection name: 'guidelines_technical' or 'guidelines_process'
        """
        filename_lower = filename.lower()
        
        # Technical documents
        technical_keywords = [
            'field guide', 'technical', 'api', 'code', 'development',
            'architecture', 'infrastructure', 'security', 'database'
        ]
        
        # Process documents
        process_keywords = [
            'runbook', 'sdlc', 'process', 'workflow', 'procedure',
            'guide', 'manual', 'playbook', 'automation'
        ]
        
        # Check for technical keywords first
        for keyword in technical_keywords:
            if keyword in filename_lower:
                return 'guidelines_technical'
        
        # Check for process keywords
        for keyword in process_keywords:
            if keyword in filename_lower:
                return 'guidelines_process'
        
        # Default to process collection for unknown types
        logger.info(f"Unknown document type for {filename}, defaulting to process collection")
        return 'guidelines_process'
    
    def _load_documents(self) -> List[Dict[str, Any]]:
        """
        Load all documents from the guidelines directory.
        
        Returns:
            List of document dictionaries with content and metadata
        """
        documents = []
        
        if not self.guidelines_dir.exists():
            logger.error(f"Guidelines directory not found: {self.guidelines_dir}")
            return documents
        
        # Supported file extensions
        supported_extensions = {'.md', '.pdf', '.docx', '.txt'}
        
        # Recursively find all supported files
        for file_path in self.guidelines_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    logger.info(f"Loading document: {file_path.name}")
                    
                    # Load document content
                    loader = UnstructuredFileLoader(str(file_path))
                    doc_content = loader.load()
                    
                    if doc_content:
                        # Extract text content
                        text_content = doc_content[0].page_content if hasattr(doc_content[0], 'page_content') else str(doc_content[0])
                        
                        documents.append({
                            'filename': file_path.name,
                            'filepath': str(file_path),
                            'content': text_content,
                            'collection': self._determine_collection(file_path.name)
                        })
                        
                        logger.info(f"Successfully loaded {file_path.name} ({len(text_content)} chars)")
                    else:
                        logger.warning(f"No content extracted from {file_path.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load {file_path.name}: {e}")
                    continue
        
        logger.info(f"Loaded {len(documents)} documents")
        return documents
    
    def _chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split documents into chunks for embedding.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        
        for doc in documents:
            try:
                content = doc['content']
                filename = doc['filename']
                collection = doc['collection']
                
                # Choose appropriate splitter based on file type
                if filename.lower().endswith('.md'):
                    # Use markdown splitter for markdown files
                    doc_chunks = self.markdown_splitter.split_text(content)
                else:
                    # Use general text splitter for other files
                    doc_chunks = self.text_splitter.split_text(content)
                
                # Create chunk metadata
                for i, chunk in enumerate(doc_chunks):
                    chunks.append({
                        'content': chunk,
                        'filename': filename,
                        'collection': collection,
                        'chunk_index': i,
                        'total_chunks': len(doc_chunks),
                        'metadata': {
                            'source': filename,
                            'chunk_index': i,
                            'total_chunks': len(doc_chunks),
                            'collection': collection
                        }
                    })
                
                logger.info(f"Created {len(doc_chunks)} chunks for {filename}")
                
            except Exception as e:
                logger.error(f"Failed to chunk {doc['filename']}: {e}")
                continue
        
        logger.info(f"Created {len(chunks)} total chunks")
        return chunks
    
    def _store_chunks_in_chromadb(self, chunks: List[Dict[str, Any]]):
        """
        Store document chunks in ChromaDB collections.
        
        Args:
            chunks: List of chunk dictionaries
        """
        # Group chunks by collection
        collections = {}
        for chunk in chunks:
            collection_name = chunk['collection']
            if collection_name not in collections:
                collections[collection_name] = []
            collections[collection_name].append(chunk)
        
        # Store chunks in each collection
        for collection_name, collection_chunks in collections.items():
            try:
                logger.info(f"Storing {len(collection_chunks)} chunks in {collection_name}")
                
                # Create collection-specific embedding manager
                collection_manager = SimpleChromaEmbeddingManager(
                    collection_name=collection_name
                )
                
                # Prepare data for ChromaDB
                texts = [str(chunk['content']) for chunk in collection_chunks]
                metadatas = [chunk['metadata'] for chunk in collection_chunks]
                ids = [f"{chunk['filename']}_{chunk['chunk_index']}" for chunk in collection_chunks]
                
                # Store in ChromaDB
                collection_manager.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Successfully stored chunks in {collection_name}")
                
            except Exception as e:
                logger.error(f"Failed to store chunks in {collection_name}: {e}")
                continue
    
    def run_ingestion(self) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline.
        
        Returns:
            Dictionary with ingestion results and statistics
        """
        start_time = time.time()
        
        logger.info("🚀 Starting guideline document ingestion pipeline...")
        
        try:
            # Step 1: Load documents
            logger.info("📚 Loading documents...")
            documents = self._load_documents()
            
            if not documents:
                logger.error("No documents found to process")
                return {'success': False, 'error': 'No documents found'}
            
            # Step 2: Chunk documents
            logger.info("✂️ Chunking documents...")
            chunks = self._chunk_documents(documents)
            
            if not chunks:
                logger.error("No chunks created from documents")
                return {'success': False, 'error': 'No chunks created'}
            
            # Step 3: Store in ChromaDB
            logger.info("💾 Storing chunks in ChromaDB...")
            self._store_chunks_in_chromadb(chunks)
            
            # Calculate statistics
            total_time = time.time() - start_time
            
            # Group by collection
            collections = {}
            for chunk in chunks:
                collection = chunk['collection']
                if collection not in collections:
                    collections[collection] = 0
                collections[collection] += 1
            
            results = {
                'success': True,
                'total_documents': len(documents),
                'total_chunks': len(chunks),
                'collections': collections,
                'processing_time': total_time,
                'documents_processed': [doc['filename'] for doc in documents]
            }
            
            logger.info(f"✅ Ingestion completed successfully!")
            logger.info(f"   Documents processed: {len(documents)}")
            logger.info(f"   Chunks created: {len(chunks)}")
            logger.info(f"   Processing time: {total_time:.2f} seconds")
            logger.info(f"   Collections: {collections}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }

def main():
    """Main execution function."""
    print("🚀 Starting Guideline Document Ingestion Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = GuidelineIngestionPipeline()
    
    # Run ingestion
    results = pipeline.run_ingestion()
    
    # Print results
    print("\n" + "=" * 60)
    if results['success']:
        print("✅ INGESTION COMPLETED SUCCESSFULLY")
        print(f"📊 Documents processed: {results['total_documents']}")
        print(f"📊 Chunks created: {results['total_chunks']}")
        print(f"⏱️  Processing time: {results['processing_time']:.2f} seconds")
        print(f"🗄️  Collections: {results['collections']}")
        
        print("\n📄 Documents processed:")
        for doc in results['documents_processed']:
            print(f"   - {doc}")
    else:
        print("❌ INGESTION FAILED")
        print(f"Error: {results['error']}")
        print(f"Processing time: {results['processing_time']:.2f} seconds")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 