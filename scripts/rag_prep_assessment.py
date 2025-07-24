#!/usr/bin/env python3
"""
RAG System Preparation Assessment Script

This script performs a comprehensive assessment of the current infrastructure
to ensure it's ready for RAG system implementation.
"""
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_dependencies() -> Dict[str, Any]:
    """Check if all required dependencies are available."""
    print("🔍 Checking RAG system dependencies...")
    
    required_packages = [
        'langchain',
        'unstructured', 
        'pypdf',
        'docx',
        'markdown',
        'chromadb'
    ]
    
    results = {
        'available': [],
        'missing': [],
        'version_info': {}
    }
    
    for package in required_packages:
        try:
            module = __import__(package)
            results['available'].append(package)
            
            # Get version if available
            if hasattr(module, '__version__'):
                results['version_info'][package] = module.__version__
            else:
                results['version_info'][package] = 'Unknown'
                
        except ImportError:
            results['missing'].append(package)
    
    return results

def check_chromadb_health() -> Dict[str, Any]:
    """Check ChromaDB health and performance."""
    print("🔍 Checking ChromaDB health...")
    
    try:
        import chromadb
        from src.core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager
        
        # Test basic ChromaDB functionality
        chroma_manager = SimpleChromaEmbeddingManager()
        
        # Get collection stats
        stats = chroma_manager.get_collection_stats()
        
        # Test embedding generation
        test_text = "This is a test for RAG system preparation"
        embedding = chroma_manager.get_embedding(test_text)
        
        return {
            'status': 'healthy',
            'collection_stats': stats,
            'embedding_test': 'passed' if embedding is not None else 'failed',
            'embedding_dimension': len(embedding) if embedding is not None else 0
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }

def check_document_structure() -> Dict[str, Any]:
    """Check if document directory structure is properly set up."""
    print("🔍 Checking document structure...")
    
    base_path = Path("../docs/guidelines")
    technical_path = base_path / "technical"
    process_path = base_path / "process"
    
    results = {
        'base_exists': base_path.exists(),
        'technical_exists': technical_path.exists(),
        'process_exists': process_path.exists(),
        'technical_files': [],
        'process_files': [],
        'main_files': [],
        'total_files': 0
    }
    
    # Check main guidelines directory
    if base_path.exists():
        results['main_files'] = [f.name for f in base_path.glob("*") if f.is_file()]
    
    # Check technical subdirectory
    if technical_path.exists():
        results['technical_files'] = [f.name for f in technical_path.glob("*") if f.is_file()]
    
    # Check process subdirectory
    if process_path.exists():
        results['process_files'] = [f.name for f in process_path.glob("*") if f.is_file()]
    
    results['total_files'] = len(results['main_files']) + len(results['technical_files']) + len(results['process_files'])
    
    return results

def check_storage_capacity() -> Dict[str, Any]:
    """Check available storage capacity."""
    print("🔍 Checking storage capacity...")
    
    try:
        import shutil
        
        # Check current directory space
        total, used, free = shutil.disk_usage(".")
        
        # Estimate RAG storage requirements
        # Rough estimate: 1MB per document + embeddings
        estimated_rag_storage = 100 * 1024 * 1024  # 100MB estimate
        
        return {
            'total_space_gb': total / (1024**3),
            'used_space_gb': used / (1024**3),
            'free_space_gb': free / (1024**3),
            'estimated_rag_storage_mb': estimated_rag_storage / (1024**2),
            'sufficient_space': free > estimated_rag_storage
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'status': 'unknown'
        }

def check_performance_baseline() -> Dict[str, Any]:
    """Establish performance baseline for comparison."""
    print("🔍 Establishing performance baseline...")
    
    try:
        from src.core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager
        
        chroma_manager = SimpleChromaEmbeddingManager()
        
        # Test embedding generation performance
        test_texts = [
            "Sample text for performance testing",
            "Another sample text for testing",
            "Third sample text for performance baseline"
        ]
        
        start_time = time.time()
        embeddings = chroma_manager.get_batch_embeddings(test_texts)
        embedding_time = time.time() - start_time
        
        # Test similarity search performance
        start_time = time.time()
        similar = chroma_manager.find_similar(
            "performance test query",
            test_texts,
            top_k=3
        )
        search_time = time.time() - start_time
        
        return {
            'embedding_generation_time': embedding_time,
            'similarity_search_time': search_time,
            'embeddings_generated': len(embeddings),
            'similar_results_found': len(similar)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }

def check_security_considerations() -> Dict[str, Any]:
    """Check security considerations for RAG system."""
    print("🔍 Checking security considerations...")
    
    # Check for sensitive files in document directories
    sensitive_patterns = [
        'password', 'secret', 'key', 'token', 'credential',
        'private', 'confidential', 'internal'
    ]
    
    results = {
        'sensitive_files_found': [],
        'recommendations': []
    }
    
    docs_path = Path("docs/guidelines")
    if docs_path.exists():
        for file_path in docs_path.rglob("*"):
            if file_path.is_file():
                file_content = file_path.read_text().lower()
                for pattern in sensitive_patterns:
                    if pattern in file_content:
                        results['sensitive_files_found'].append(str(file_path))
                        break
    
    if results['sensitive_files_found']:
        results['recommendations'].append(
            "Review files for sensitive content before RAG ingestion"
        )
    
    return results

def generate_assessment_report() -> Dict[str, Any]:
    """Generate comprehensive assessment report."""
    print("📋 Generating RAG system assessment report...")
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'dependencies': check_dependencies(),
        'chromadb_health': check_chromadb_health(),
        'document_structure': check_document_structure(),
        'storage_capacity': check_storage_capacity(),
        'performance_baseline': check_performance_baseline(),
        'security_considerations': check_security_considerations()
    }
    
    # Add overall readiness assessment
    readiness_score = 0
    total_checks = 0
    
    # Check dependencies
    if report['dependencies']['missing']:
        readiness_score += 0
    else:
        readiness_score += 25
    total_checks += 25
    
    # Check ChromaDB health
    if report['chromadb_health']['status'] == 'healthy':
        readiness_score += 25
    total_checks += 25
    
    # Check document structure
    if report['document_structure']['base_exists']:
        readiness_score += 25
    total_checks += 25
    
    # Check storage capacity
    if report['storage_capacity'].get('sufficient_space', False):
        readiness_score += 25
    total_checks += 25
    
    report['readiness_score'] = readiness_score
    report['readiness_percentage'] = (readiness_score / total_checks) * 100 if total_checks > 0 else 0
    
    return report

def print_report(report: Dict[str, Any]):
    """Print formatted assessment report."""
    print("\n" + "="*80)
    print("🔍 RAG SYSTEM PREPARATION ASSESSMENT REPORT")
    print("="*80)
    print(f"Generated: {report['timestamp']}")
    print(f"Overall Readiness: {report['readiness_percentage']:.1f}%")
    print("="*80)
    
    # Dependencies
    print("\n📦 DEPENDENCIES:")
    if report['dependencies']['missing']:
        print(f"❌ Missing: {', '.join(report['dependencies']['missing'])}")
        print("   Run: pip install " + " ".join(report['dependencies']['missing']))
    else:
        print("✅ All required dependencies are available")
    
    # ChromaDB Health
    print("\n🗄️  CHROMADB HEALTH:")
    if report['chromadb_health']['status'] == 'healthy':
        stats = report['chromadb_health']['collection_stats']
        print(f"✅ Status: Healthy")
        print(f"   Collection: {stats.get('collection_name', 'Unknown')}")
        print(f"   Embeddings: {stats.get('total_embeddings', 0)}")
        print(f"   Dimension: {stats.get('embedding_dimension', 0)}")
    else:
        print(f"❌ Status: {report['chromadb_health']['status']}")
        print(f"   Error: {report['chromadb_health'].get('error', 'Unknown')}")
    
    # Document Structure
    print("\n📁 DOCUMENT STRUCTURE:")
    doc_structure = report['document_structure']
    if doc_structure['base_exists']:
        print("✅ Guidelines directory exists")
        print(f"   Main files: {len(doc_structure['main_files'])}")
        print(f"   Technical files: {len(doc_structure['technical_files'])}")
        print(f"   Process files: {len(doc_structure['process_files'])}")
        print(f"   Total files: {doc_structure['total_files']}")
        
        if doc_structure['main_files']:
            print("   Main documents:")
            for file in doc_structure['main_files'][:3]:  # Show first 3
                print(f"     - {file}")
    else:
        print("❌ Guidelines directory missing")
    
    # Storage Capacity
    print("\n💾 STORAGE CAPACITY:")
    storage = report['storage_capacity']
    if 'error' not in storage:
        print(f"   Free space: {storage['free_space_gb']:.1f} GB")
        print(f"   Estimated RAG storage: {storage['estimated_rag_storage_mb']:.1f} MB")
        if storage.get('sufficient_space', False):
            print("✅ Sufficient storage available")
        else:
            print("⚠️  Consider freeing up space")
    
    # Security
    print("\n🔒 SECURITY CONSIDERATIONS:")
    security = report['security_considerations']
    if security['sensitive_files_found']:
        print(f"⚠️  {len(security['sensitive_files_found'])} files may contain sensitive content")
        for file in security['sensitive_files_found'][:3]:  # Show first 3
            print(f"   - {file}")
    else:
        print("✅ No obvious sensitive content detected")
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    if report['readiness_percentage'] >= 90:
        print("✅ System is ready for RAG implementation")
    elif report['readiness_percentage'] >= 70:
        print("⚠️  Minor issues to address before implementation")
    else:
        print("❌ Significant issues need to be resolved")
    
    if report['dependencies']['missing']:
        print("   1. Install missing dependencies")
    if report['document_structure']['total_files'] == 0:
        print("   2. Add sample guideline documents")
    if not report['storage_capacity'].get('sufficient_space', False):
        print("   3. Free up disk space")
    
    print("\n" + "="*80)

def save_report(report: Dict[str, Any], filename: str = "rag_assessment_report.json"):
    """Save assessment report to file."""
    report_path = Path("logs") / filename
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Report saved to: {report_path}")

def main():
    """Main assessment function."""
    print("🚀 Starting RAG System Preparation Assessment...")
    print("This will check your infrastructure readiness for RAG implementation.\n")
    
    try:
        # Generate comprehensive report
        report = generate_assessment_report()
        
        # Print formatted report
        print_report(report)
        
        # Save detailed report
        save_report(report)
        
        # Return exit code based on readiness
        if report['readiness_percentage'] >= 70:
            print("\n✅ Assessment completed. System appears ready for RAG implementation.")
            return 0
        else:
            print("\n❌ Assessment completed. Please address the issues above before proceeding.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Assessment failed with error: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main()) 