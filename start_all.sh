#!/bin/bash
# Convenience launcher script for Unified Crypto Monitor
# Starts all crypto monitoring services in one command

echo "🚀 Starting Unified Crypto Monitor..."
echo "📊 This will start all crypto monitoring services:"
echo "   • CoinDCX Futures LTP Monitor"
echo "   • CoinDCX Funding Rate Monitor"
echo "   • Bybit Spot Price Monitor"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================================="

# Navigate to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "env" ]; then
    echo "🐍 Activating virtual environment..."
    source env/bin/activate
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required dependencies are installed
if ! python3 -c "import redis, requests, asyncio" 2>/dev/null; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the unified monitor
echo "🎯 Starting unified crypto monitor..."
python3 unified_crypto_monitor.py

echo "👋 All services stopped"