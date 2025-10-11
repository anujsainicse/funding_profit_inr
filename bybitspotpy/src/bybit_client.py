import asyncio
import json
import websockets
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import List, Optional
import structlog
import traceback

logger = structlog.get_logger()

class SimpleBybitSpotClient:
    """Simple Bybit spot price client with comprehensive logging and health monitoring."""

    def __init__(self, coins: List[str], redis_config: dict):
        self.coins = coins
        self.ws_url = "wss://stream.bybit.com/v5/public/spot"
        self.redis_config = redis_config
        self.redis_client: Optional[redis.Redis] = None
        self.websocket = None
        self.running = False

        # Health monitoring
        self.last_message_time = None
        self.message_count = 0
        self.reconnect_count = 0
        self.ping_interval = 20  # Send ping every 20 seconds
        self.timeout_threshold = 60  # Consider connection dead after 60 seconds of no messages

        logger.info("Bybit client initialized", coins=self.coins, ws_url=self.ws_url)

    async def connect_redis(self):
        """Connect to Redis."""
        logger.info("Attempting to connect to Redis", host=self.redis_config['host'], port=self.redis_config['port'])
        try:
            if self.redis_config.get('password'):
                url = f"redis://:{self.redis_config['password']}@{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"
            else:
                url = f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"

            self.redis_client = redis.from_url(url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully", db=self.redis_config['db'])
            return True
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e), traceback=traceback.format_exc())
            return False

    async def connect_websocket(self):
        """Connect to Bybit WebSocket."""
        self.reconnect_count += 1
        logger.info("Attempting to connect to Bybit WebSocket",
                   attempt=self.reconnect_count, url=self.ws_url)
        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=self.ping_interval,
                ping_timeout=10,
                close_timeout=10
            )
            self.last_message_time = datetime.utcnow()
            logger.info("Connected to Bybit WebSocket successfully", reconnect_count=self.reconnect_count)

            # Subscribe to tickers
            subscribe_msg = {
                "op": "subscribe",
                "args": [f"tickers.{coin}" for coin in self.coins]
            }
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info("Subscription message sent", coins=self.coins)
            return True
        except Exception as e:
            logger.error("Failed to connect to WebSocket",
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc())
            return False

    async def process_message(self, message):
        """Process WebSocket message."""
        self.last_message_time = datetime.utcnow()
        self.message_count += 1

        # Log every 100 messages to avoid log spam
        if self.message_count % 100 == 0:
            logger.info("Message processing stats",
                       total_messages=self.message_count,
                       reconnects=self.reconnect_count)

        try:
            data = json.loads(message)

            # Handle ping/pong
            if data.get("op") == "pong":
                logger.debug("Received pong from server")
                return

            # Handle subscription response
            if data.get("op") == "subscribe":
                if data.get("success"):
                    logger.info("Subscription successful", response=data)
                else:
                    logger.error("Subscription failed", response=data)
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
                        try:
                            hash_key = f"bybit_spot:{coin_name}"
                            hash_data = {
                                "ltp": str(price),
                                "timestamp": timestamp.isoformat() + "Z",
                                "original_symbol": symbol
                            }
                            await self.redis_client.hset(hash_key, mapping=hash_data)
                        except Exception as redis_error:
                            logger.error("Failed to write to Redis",
                                       error=str(redis_error),
                                       coin=coin_name,
                                       price=price)
                else:
                    logger.warning("Received ticker without symbol or price", data=ticker)
            else:
                # Log unknown message types
                logger.debug("Received unknown message type", message_preview=str(data)[:200])

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON message",
                        error=str(e),
                        message_preview=str(message)[:200])
        except Exception as e:
            logger.error("Error processing message",
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc())

    async def health_monitor(self):
        """Monitor connection health and force reconnect if needed."""
        logger.info("Health monitor started",
                   timeout_threshold=self.timeout_threshold)

        while self.running:
            await asyncio.sleep(30)  # Check every 30 seconds

            if self.last_message_time:
                time_since_last_message = (datetime.utcnow() - self.last_message_time).total_seconds()

                if time_since_last_message > self.timeout_threshold:
                    logger.error("Connection appears stuck - no messages received",
                               seconds_since_last_message=time_since_last_message,
                               threshold=self.timeout_threshold,
                               total_messages=self.message_count,
                               reconnects=self.reconnect_count)

                    # Force close the websocket to trigger reconnection
                    if self.websocket:
                        try:
                            await self.websocket.close()
                            logger.info("Forced websocket close due to timeout")
                        except Exception as e:
                            logger.error("Error closing stuck websocket", error=str(e))
                else:
                    logger.info("Connection health check",
                               seconds_since_last_message=time_since_last_message,
                               total_messages=self.message_count,
                               reconnects=self.reconnect_count)

    async def run(self):
        """Run the client."""
        self.running = True
        logger.info("Starting Bybit client")

        # Connect to Redis
        if not await self.connect_redis():
            logger.error("Failed to connect to Redis, exiting")
            return False

        # Start health monitor
        health_task = asyncio.create_task(self.health_monitor())
        logger.info("Health monitor task started")

        while self.running:
            try:
                # Connect to WebSocket
                logger.info("Initiating WebSocket connection")
                if not await self.connect_websocket():
                    logger.warning("WebSocket connection failed, retrying in 5 seconds")
                    await asyncio.sleep(5)
                    continue

                logger.info("WebSocket connected, starting message loop")
                # Listen for messages
                async for message in self.websocket:
                    if not self.running:
                        logger.info("Stop signal received, breaking message loop")
                        break
                    await self.process_message(message)

                logger.warning("Message loop ended normally (unexpected)")

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning("WebSocket connection closed",
                             code=e.code if hasattr(e, 'code') else None,
                             reason=e.reason if hasattr(e, 'reason') else None,
                             reconnecting=True)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("Client task cancelled")
                break
            except Exception as e:
                logger.error("Error in main loop",
                           error=str(e),
                           error_type=type(e).__name__,
                           traceback=traceback.format_exc())
                await asyncio.sleep(5)

        # Cleanup
        logger.info("Cleaning up resources")
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass

        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("WebSocket closed")
            except Exception as e:
                logger.error("Error closing websocket", error=str(e))

        if self.redis_client:
            try:
                await self.redis_client.aclose()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error("Error closing Redis connection", error=str(e))

    async def stop(self):
        """Stop the client."""
        self.running = False
        if self.websocket:
            await self.websocket.close()