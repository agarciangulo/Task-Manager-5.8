#!/bin/bash

# LOCAL Gmail Processor Deployment with Cost Controls
# This runs your enhanced Gmail processor locally with safety features

set -e

echo "🛡️ LOCAL Gmail Processor Deployment"
echo "==================================="
echo "Running enhanced Gmail processor locally with cost controls"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ ERROR: Please activate your virtual environment first"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment is active: $VIRTUAL_ENV"

# Check if required environment variables are set
echo "🔍 Checking environment variables..."
source local_env.txt 2>/dev/null || echo "⚠️ local_env.txt not found, using system environment"

# Test the enhanced processor locally
echo "🧪 Testing enhanced Gmail processor..."
python deployment/gmail_processor_cloud_run_safe.py

echo ""
echo "✅ Local test completed!"
echo ""
echo "🚀 To run continuously (with cost controls):"
echo "   python check_gmail_enhanced.py"
echo ""
echo "📊 To monitor costs:"
echo "   ./deployment/monitor-costs-local.sh"
echo ""
echo "🛑 To stop: Press Ctrl+C"
echo ""
echo "💡 Cost Controls Active:"
echo "   - Maximum execution time: 5 minutes"
echo "   - Conservative scheduling: Every 10 minutes"
echo "   - Resource limits enforced"
echo "   - Cost logging enabled" 