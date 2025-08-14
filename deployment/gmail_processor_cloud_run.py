"""
Cloud Run compatible Gmail processor for Google Cloud deployment.
This version is designed to be triggered by Cloud Scheduler every 5 minutes.
"""

import os
import sys
import traceback
from datetime import datetime
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_gmail_batch():
    """
    Process Gmail batch - designed for Cloud Run execution.
    This function will be called by Cloud Scheduler every 5 minutes.
    """
    try:
        logger.info("🚀 Starting Gmail batch processing...")
        
        # Import here to avoid issues during container build
        from src.utils.gmail_processor_enhanced import check_gmail_for_updates_enhanced
        
        # Run the enhanced processor
        check_gmail_for_updates_enhanced()
        
        logger.info("✅ Gmail batch processing completed successfully")
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'message': 'Gmail processing completed'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Gmail batch processing: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

def health_check():
    """
    Health check endpoint for Cloud Run.
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'gmail-processor'
    }

# For local testing
if __name__ == "__main__":
    result = process_gmail_batch()
    print(f"Result: {result}") 