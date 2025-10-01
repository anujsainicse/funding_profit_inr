"""
Bybit Spot Service Wrapper
Wraps the existing bybitspotpy service for unified management
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

# Add bybitspotpy to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bybitspotpy', 'src'))

try:
    from bybit_client import SimpleBybitSpotClient
except ImportError:
    # Fallback if import fails
    SimpleBybitSpotClient = None


class BybitSpotService:
    """Wrapper for Bybit Spot price monitoring service."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.service_config = config['services']['bybit_spot']
        self.redis_config = config['redis']
        self.symbols = self.service_config['symbols']
        self.settings = self.service_config['settings']

        self.bybit_client = None
        self.running = False
        self.last_update = None

        if SimpleBybitSpotClient is None:
            self.logger.error("❌ Bybit Spot: Could not import SimpleBybitSpotClient")

    def extract_coin_name(self, symbol: str) -> str:
        """Extract coin name from Bybit symbol format."""
        if symbol.endswith('USDT'):
            return symbol[:-4]  # Remove 'USDT' suffix
        return symbol

    async def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        status = {
            'service': 'bybit_spot',
            'running': self.running,
            'client_available': SimpleBybitSpotClient is not None,
            'client_connected': self.bybit_client is not None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'symbols_count': len(self.symbols)
        }

        # Check if we've received data recently
        if self.last_update:
            seconds_since_update = (datetime.now() - self.last_update).total_seconds()
            status['seconds_since_last_update'] = seconds_since_update
            status['healthy'] = seconds_since_update < 60  # Consider healthy if updated within 60 seconds
        else:
            status['healthy'] = False

        return status

    async def start(self):
        """Start the Bybit Spot monitoring service."""
        try:
            self.logger.info("🚀 Starting Bybit Spot Service...")

            if SimpleBybitSpotClient is None:
                self.logger.error("❌ Bybit Spot: Cannot start - client not available")
                return

            # Initialize Bybit client with our configuration
            self.bybit_client = SimpleBybitSpotClient(
                coins=self.symbols,
                redis_config=self.redis_config
            )

            # Override the client's update callback to track our last update time
            original_on_price_update = getattr(self.bybit_client, 'on_price_update', None)

            async def tracked_price_update(*args, **kwargs):
                self.last_update = datetime.now()
                if original_on_price_update:
                    await original_on_price_update(*args, **kwargs)

            if hasattr(self.bybit_client, 'on_price_update'):
                self.bybit_client.on_price_update = tracked_price_update

            self.running = True
            self.logger.info(f"✅ Bybit Spot Service started - monitoring {len(self.symbols)} symbols")

            # Start the Bybit client
            await self.bybit_client.run()

        except Exception as e:
            self.logger.error(f"❌ Bybit Spot Service error: {e}")
            self.running = False

    async def stop(self):
        """Stop the Bybit Spot monitoring service."""
        try:
            self.logger.info("🛑 Stopping Bybit Spot Service...")
            self.running = False

            if self.bybit_client:
                await self.bybit_client.stop()

            self.logger.info("✅ Bybit Spot Service stopped")

        except Exception as e:
            self.logger.error(f"❌ Error stopping Bybit Spot Service: {e}")


class BybitSpotServiceFallback:
    """Fallback service when Bybit client is not available."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.service_config = config['services']['bybit_spot']
        self.running = False

    async def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        return {
            'service': 'bybit_spot',
            'running': False,
            'client_available': False,
            'error': 'Bybit client not available',
            'healthy': False
        }

    async def start(self):
        """Start method for fallback service."""
        self.logger.warning("⚠️ Bybit Spot Service: Running in fallback mode - client not available")
        self.running = True

        # Keep running but do nothing
        while self.running:
            await asyncio.sleep(30)

    async def stop(self):
        """Stop method for fallback service."""
        self.logger.info("🛑 Stopping Bybit Spot Service (fallback mode)")
        self.running = False


# Choose which service to export based on availability
if SimpleBybitSpotClient is not None:
    BybitSpotServiceClass = BybitSpotService
else:
    BybitSpotServiceClass = BybitSpotServiceFallback