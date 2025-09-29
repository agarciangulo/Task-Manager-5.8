import time
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.utils.gmail_processor_enhanced import check_gmail_for_updates_enhanced
from src.config.settings import GMAIL_ADDRESS

def main():
    """Run the Enhanced Gmail checker on a schedule."""
    interval_minutes = 5  # Check every 5 minutes
    
    print(f"🚀 Starting Enhanced Gmail Processor")
    print(f"📧 Checking for emails sent to: {GMAIL_ADDRESS}")
    print(f"⏰ Will check every {interval_minutes} minutes")
    print("Press Ctrl+C to exit.")
    print("=" * 50)
    
    try:
        while True:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Checking for new emails...")
            check_gmail_for_updates_enhanced()
            
            # Wait for the next check
            print(f"⏳ Next check in {interval_minutes} minutes...")
            for i in range(interval_minutes * 60):
                time.sleep(1)
                # Add a simple progress indicator every minute
                if i % 60 == 0 and i > 0:
                    minutes_passed = i // 60
                    minutes_left = interval_minutes - minutes_passed
                    print(f"  {minutes_left} minutes until next check...")
                    
    except KeyboardInterrupt:
        print("\n🛑 Enhanced Gmail processor stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error in main loop: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 