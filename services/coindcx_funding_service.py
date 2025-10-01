"""
CoinDCX Funding Rate Service Wrapper
Wraps the existing coindcx_fu_fr.py for unified management
"""

import asyncio
import requests
import time
import redis
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any


class CoinDCXFundingService:
    """Wrapper for CoinDCX Funding Rate monitoring service."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.service_config = config['services']['coindcx_funding']
        self.redis_config = config['redis']
        self.symbols = self.service_config['symbols']
        self.settings = self.service_config['settings']

        self.redis_client = None
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
            self.logger.info("✅ CoinDCX Funding: Redis connected successfully!")
            return redis_client

        except Exception as e:
            self.logger.error(f"❌ CoinDCX Funding: Redis connection failed: {e}")
            return None

    def extract_coin_name(self, symbol: str) -> str:
        """Extract coin name from CoinDCX symbol format."""
        if symbol.startswith('B-') and '_' in symbol:
            return symbol.split('_')[0][2:]  # Remove 'B-' prefix and get coin
        return symbol

    async def fetch_funding_rates(self):
        """Fetch funding rates from CoinDCX API."""
        try:
            url = "https://api.coindcx.com/exchange/v1/derivatives/get_funding_rate"

            for attempt in range(self.settings['retry_attempts']):
                try:
                    response = requests.get(url, timeout=self.settings['api_timeout'])
                    response.raise_for_status()

                    funding_data = response.json()
                    await self.process_funding_data(funding_data)
                    self.last_update = datetime.now()
                    self.logger.info(f"✅ CoinDCX Funding: Successfully fetched funding rates")
                    return

                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"⚠️ CoinDCX Funding: API request failed (attempt {attempt + 1}): {e}")
                    if attempt < self.settings['retry_attempts'] - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise

        except Exception as e:
            self.logger.error(f"❌ CoinDCX Funding: Error fetching funding rates: {e}")

    async def process_funding_data(self, funding_data: list):
        """Process and store funding rate data in Redis."""
        try:
            if not self.redis_client:
                return

            timestamp = datetime.now().isoformat()

            for item in funding_data:
                symbol = item.get('symbol', '')

                # Only process symbols we're monitoring
                if symbol in self.symbols:
                    coin = self.extract_coin_name(symbol)

                    redis_key = f"{self.service_config['redis_key_prefix']}:{coin}"

                    redis_data = {
                        'funding_rate': str(item.get('funding_rate', 0)),
                        'next_funding_time': str(item.get('next_funding_time', '')),
                        'timestamp': timestamp,
                        'original_symbol': symbol
                    }

                    # Store hash data with TTL
                    pipe = self.redis_client.pipeline()
                    pipe.hset(redis_key, mapping=redis_data)
                    pipe.expire(redis_key, self.settings['redis_ttl'])
                    pipe.execute()

                    self.logger.debug(f"CoinDCX Funding: Updated {coin} funding rate = {item.get('funding_rate', 0)}")

        except Exception as e:
            self.logger.error(f"❌ CoinDCX Funding: Error processing funding data: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        status = {
            'service': 'coindcx_funding',
            'running': self.running,
            'redis_connected': self.redis_client is not None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'symbols_count': len(self.symbols),
            'fetch_interval': self.settings['fetch_interval']
        }

        # Check if we've received data recently
        if self.last_update:
            seconds_since_update = (datetime.now() - self.last_update).total_seconds()
            status['seconds_since_last_update'] = seconds_since_update
            # Consider healthy if updated within 2 fetch intervals
            status['healthy'] = seconds_since_update < (self.settings['fetch_interval'] * 2)
        else:
            status['healthy'] = False

        return status

    async def start(self):
        """Start the CoinDCX Funding Rate monitoring service."""
        try:
            self.logger.info("🚀 Starting CoinDCX Funding Rate Service...")

            # Setup Redis connection
            self.redis_client = self.setup_redis_connection()
            if not self.redis_client:
                self.logger.error("❌ CoinDCX Funding: Cannot start without Redis connection")
                return

            self.running = True
            self.logger.info(f"✅ CoinDCX Funding Service started - monitoring {len(self.symbols)} symbols")

            # Main loop for periodic funding rate fetching
            while self.running:
                try:
                    await self.fetch_funding_rates()
                    await asyncio.sleep(self.settings['fetch_interval'])

                except Exception as e:
                    self.logger.error(f"❌ CoinDCX Funding: Error in main loop: {e}")
                    await asyncio.sleep(30)  # Wait before retrying

        except Exception as e:
            self.logger.error(f"❌ CoinDCX Funding Service error: {e}")
            self.running = False

    async def stop(self):
        """Stop the CoinDCX Funding Rate monitoring service."""
        try:
            self.logger.info("🛑 Stopping CoinDCX Funding Service...")
            self.running = False

            if self.redis_client:
                self.redis_client.close()

            self.logger.info("✅ CoinDCX Funding Service stopped")

        except Exception as e:
            self.logger.error(f"❌ Error stopping CoinDCX Funding Service: {e}")