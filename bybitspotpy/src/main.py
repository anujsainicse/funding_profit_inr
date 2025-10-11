import asyncio
import json
import os
import signal
import logging
import logging.handlers
from pathlib import Path
from dotenv import load_dotenv
import structlog
from .bybit_client import SimpleBybitSpotClient

# Load environment variables
load_dotenv()

# Create logs directory
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Configure standard logging
log_file = LOG_DIR / 'bybit_spot.log'
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    handlers=[file_handler, console_handler]
)

logger = structlog.get_logger()
logger.info("Logging configured", log_file=str(log_file), log_dir=str(LOG_DIR))

class SimpleCryptoPriceBot:
    """Simple crypto price bot for Bybit spot."""

    def __init__(self):
        # Load coins configuration
        config_path = Path(__file__).parent.parent / 'config' / 'coins.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.coins = config.get('coins', [])

        # Redis configuration
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'password': os.getenv('REDIS_PASSWORD') or None,
            'db': int(os.getenv('REDIS_DB', 0))
        }

        self.client = SimpleBybitSpotClient(self.coins, self.redis_config)
        self.shutdown_event = asyncio.Event()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def shutdown(self):
        """Shutdown the bot."""
        await self.client.stop()
        self.shutdown_event.set()

    async def run(self):
        """Run the bot."""
        logger.info("=================================================")
        logger.info("Simple Bybit Spot Price Bot - Starting...")
        logger.info("=================================================")
        logger.info(f"Monitoring coins: {self.coins}")

        self.setup_signal_handlers()

        # Start the client
        client_task = asyncio.create_task(self.client.run())
        shutdown_task = asyncio.create_task(self.shutdown_event.wait())

        # Wait for either client to finish or shutdown signal
        done, pending = await asyncio.wait(
            [client_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("Bot stopped")

async def main():
    """Main entry point."""
    bot = SimpleCryptoPriceBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")