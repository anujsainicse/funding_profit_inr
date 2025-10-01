import asyncio
import json
import websockets
import redis.asyncio as redis
from datetime import datetime
from typing import List, Optional
import structlog

logger = structlog.get_logger()

class SimpleBybitSpotClient:
    """Simple Bybit spot price client without complex features."""

    def __init__(self, coins: List[str], redis_config: dict):
        self.coins = coins
        self.ws_url = "wss://stream.bybit.com/v5/public/spot"
        self.redis_config = redis_config
        self.redis_client: Optional[redis.Redis] = None
        self.websocket = None
        self.running = False

    async def connect_redis(self):
        """Connect to Redis."""
        try:
            if self.redis_config.get('password'):
                url = f"redis://:{self.redis_config['password']}@{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"
            else:
                url = f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"

            self.redis_client = redis.from_url(url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def connect_websocket(self):
        """Connect to Bybit WebSocket."""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info("Connected to Bybit WebSocket")

            # Subscribe to tickers
            subscribe_msg = {
                "op": "subscribe",
                "args": [f"tickers.{coin}" for coin in self.coins]
            }
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to coins: {self.coins}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False

    async def process_message(self, message):
        """Process WebSocket message."""
        try:
            data = json.loads(message)

            # Handle subscription response
            if data.get("op") == "subscribe":
                if data.get("success"):
                    logger.info("Subscription successful")
                else:
                    logger.error(f"Subscription failed: {data}")
                return

            # Handle ticker data
            if data.get("topic") and "tickers" in data["topic"]:
                ticker = data.get("data", {})
                symbol = ticker.get("symbol")
                price = ticker.get("lastPrice")

                if symbol and price:
                    coin_name = symbol.replace("USDT", "")
                    timestamp = datetime.utcnow()

                    # Display price
                    print(f"{coin_name}|{price}|{timestamp.isoformat()}Z")

                    # Store in Redis
                    if self.redis_client:
                        hash_key = f"bybit_spot:{coin_name}"
                        hash_data = {
                            "ltp": str(price),
                            "timestamp": timestamp.isoformat() + "Z",
                            "original_symbol": symbol
                        }
                        await self.redis_client.hset(hash_key, mapping=hash_data)

        except json.JSONDecodeError:
            logger.error("Failed to parse JSON message")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def run(self):
        """Run the client."""
        self.running = True

        # Connect to Redis
        if not await self.connect_redis():
            return False

        while self.running:
            try:
                # Connect to WebSocket
                if not await self.connect_websocket():
                    await asyncio.sleep(5)
                    continue

                # Listen for messages
                async for message in self.websocket:
                    if not self.running:
                        break
                    await self.process_message(message)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)

        # Cleanup
        if self.websocket:
            await self.websocket.close()
        if self.redis_client:
            await self.redis_client.aclose()

    async def stop(self):
        """Stop the client."""
        self.running = False
        if self.websocket:
            await self.websocket.close()