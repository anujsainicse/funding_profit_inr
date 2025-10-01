"""
CoinDCX Futures LTP Service Wrapper
Wraps the existing coindcx_fu_ltp_ws_redis.py for unified management
"""

import asyncio
import json
import sys
import os
import redis
import logging
from datetime import datetime
from typing import Dict, Optional, Any

# Add coindcx-futures directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'coindcx-futures'))

from coindcx_futures import CoinDCXFutures


class CoinDCXLTPService:
    """Wrapper for CoinDCX Futures LTP monitoring service."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.service_config = config['services']['coindcx_ltp']
        self.redis_config = config['redis']
        self.symbols = self.service_config['symbols']
        self.settings = self.service_config['settings']

        self.redis_client = None
        self.coindcx_client = None
        self.running = False
        self.last_update = None

    def setup_redis_connection(self) -> Optional[redis.Redis]:
        """Setup Redis connection with error handling."""
        try:
            redis_client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config['password'],
                db=self.redis_config['db'],
                decode_responses=self.redis_config['decode_responses']
            )

            # Test connection
            redis_client.ping()
            self.logger.info("✅ CoinDCX LTP: Redis connected successfully!")
            return redis_client

        except Exception as e:
            self.logger.error(f"❌ CoinDCX LTP: Redis connection failed: {e}")
            return None

    def extract_coin_name(self, symbol: str) -> str:
        """Extract coin name from CoinDCX symbol format."""
        if symbol.startswith('B-') and '_' in symbol:
            return symbol.split('_')[0][2:]  # Remove 'B-' prefix and get coin
        return symbol

    async def on_ltp_update(self, data):
        """Handle LTP updates from WebSocket."""
        try:
            if not self.redis_client:
                return

            symbol = data.get('symbol', '')
            ltp = data.get('ltp', 0)

            if symbol and ltp:
                coin = self.extract_coin_name(symbol)
                timestamp = datetime.now().isoformat()

                # Store in Redis using hash structure
                redis_key = f"{self.service_config['redis_key_prefix']}:{coin}"

                redis_data = {
                    'ltp': str(ltp),
                    'timestamp': timestamp,
                    'original_symbol': symbol
                }

                # Store hash data with TTL
                pipe = self.redis_client.pipeline()
                pipe.hset(redis_key, mapping=redis_data)
                pipe.expire(redis_key, self.settings['redis_ttl'])
                pipe.execute()

                self.last_update = datetime.now()
                self.logger.debug(f"CoinDCX LTP: Updated {coin} = {ltp}")

        except Exception as e:
            self.logger.error(f"CoinDCX LTP: Error processing update: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        status = {
            'service': 'coindcx_ltp',
            'running': self.running,
            'redis_connected': self.redis_client is not None,
            'websocket_connected': self.coindcx_client is not None and hasattr(self.coindcx_client, 'connected') and self.coindcx_client.connected,
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
        """Start the CoinDCX LTP monitoring service."""
        try:
            self.logger.info("🚀 Starting CoinDCX Futures LTP Service...")

            # Setup Redis connection
            self.redis_client = self.setup_redis_connection()
            if not self.redis_client:
                self.logger.error("❌ CoinDCX LTP: Cannot start without Redis connection")
                return

            # Initialize CoinDCX client
            self.coindcx_client = CoinDCXFutures()

            # Set up WebSocket callbacks
            self.coindcx_client.on_ltp_update = self.on_ltp_update

            # Connect to WebSocket
            await self.coindcx_client.connect()

            # Subscribe to symbols
            for symbol in self.symbols:
                await self.coindcx_client.subscribe_ltp(symbol)
                self.logger.info(f"CoinDCX LTP: Subscribed to {symbol}")

            self.running = True
            self.logger.info(f"✅ CoinDCX LTP Service started - monitoring {len(self.symbols)} symbols")

            # Keep the connection alive
            while self.running:
                await asyncio.sleep(self.settings['update_interval'])

        except Exception as e:
            self.logger.error(f"❌ CoinDCX LTP Service error: {e}")
            self.running = False

    async def stop(self):
        """Stop the CoinDCX LTP monitoring service."""
        try:
            self.logger.info("🛑 Stopping CoinDCX LTP Service...")
            self.running = False

            if self.coindcx_client:
                await self.coindcx_client.disconnect()

            if self.redis_client:
                self.redis_client.close()

            self.logger.info("✅ CoinDCX LTP Service stopped")

        except Exception as e:
            self.logger.error(f"❌ Error stopping CoinDCX LTP Service: {e}")