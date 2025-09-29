"""
Cloud Run compatible Gmail processor for Google Cloud deployment.
This version is designed to be triggered by Cloud Scheduler every 5 minutes.
"""

import os
import sys
import traceback
from datetime import datetime
import logging
from flask import Flask, request, jsonify

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

def process_gmail_batch():
    """
    Process Gmail batch - designed for Cloud Run execution.
    This function will be called by Cloud Scheduler every 5 minutes.
    """
    try:
        logger.info("🚀 Starting Gmail batch processing...")
        
        # Import here to avoid heavy initialization at startup
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

@app.route('/', methods=['POST', 'GET'])
def handle_request():
    """Handle requests from Cloud Scheduler."""
    try:
        logger.info("📧 Received Gmail processing request")
        result = process_gmail_batch()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'gmail-processor'
    })

if __name__ == "__main__":
    # Always start Flask server for Cloud Run
    logger.info("🚀 Starting Gmail processor service...")
    app.run(host='0.0.0.0', port=8080, debug=False) 