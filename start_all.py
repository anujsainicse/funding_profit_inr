#!/usr/bin/env python3
"""
Convenience launcher for Unified Crypto Monitor
Simple way to start all crypto monitoring services
"""

import sys
import os
import asyncio
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from unified_crypto_monitor import main

if __name__ == "__main__":
    print("🚀 Starting Unified Crypto Monitor...")
    print("📊 This will start all crypto monitoring services:")
    print("   • CoinDCX Futures LTP Monitor")
    print("   • CoinDCX Funding Rate Monitor")
    print("   • Bybit Spot Price Monitor")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 All services stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)