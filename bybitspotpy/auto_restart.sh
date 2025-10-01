#!/bin/bash

# Auto-restart script for Python Bybit Spot bot
# This script automatically restarts the bot when it fails

cd /Users/xtz/claude/bybitspotpy
source venv/bin/activate

echo "Starting Bybit Spot Python Bot with auto-restart..."
echo "Press Ctrl+C to stop"

while true; do
    echo "[$(date)] Starting spot bot..."
    python3 -m src.main
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "[$(date)] Bot exited normally (exit code 0). Restarting in 5 seconds..."
    else
        echo "[$(date)] Bot crashed (exit code $exit_code). Restarting in 5 seconds..."
    fi
    
    sleep 5
done