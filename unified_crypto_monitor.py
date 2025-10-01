#!/usr/bin/env python3
"""
Unified Crypto Monitor - Central Orchestrator
Manages CoinDCX LTP, CoinDCX Funding Rate, and Bybit Spot monitoring services
"""

import asyncio
import json
import logging
import signal
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from logging.handlers import RotatingFileHandler

# Import service wrappers
from services.coindcx_ltp_service import CoinDCXLTPService
from services.coindcx_funding_service import CoinDCXFundingService
from services.bybit_spot_service import BybitSpotServiceClass


class UnifiedCryptoMonitor:
    """
    Central orchestrator for all crypto monitoring services.
    Manages lifecycle, health monitoring, and graceful shutdown.
    """

    def __init__(self, config_path: str = "config/unified_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.logger = self.setup_logging()

        # Service instances
        self.services = {}
        self.service_tasks = {}
        self.running = False
        self.shutdown_event = asyncio.Event()

        # Initialize services
        self.init_services()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

            with open(config_file, 'r') as f:
                config = json.load(f)

            print(f"✅ Configuration loaded from {self.config_path}")
            return config

        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            sys.exit(1)

    def setup_logging(self) -> logging.Logger:
        """Setup centralized logging configuration."""
        log_config = self.config.get('logging', {})

        # Create logs directory if it doesn't exist
        log_file_path = log_config.get('file', {}).get('path', 'logs/unified_crypto_monitor.log')
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(exist_ok=True)

        # Configure logging
        logger = logging.getLogger('UnifiedCryptoMonitor')
        logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))

        # Clear existing handlers
        logger.handlers.clear()

        # Console handler
        if log_config.get('console', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # File handler with rotation
        if log_config.get('file', {}).get('enabled', True):
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=log_config.get('file', {}).get('max_size_mb', 100) * 1024 * 1024,
                backupCount=log_config.get('file', {}).get('backup_count', 5)
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def init_services(self):
        """Initialize all monitoring services."""
        services_config = self.config.get('services', {})

        # Initialize CoinDCX LTP Service
        if services_config.get('coindcx_ltp', {}).get('enabled', True):
            self.services['coindcx_ltp'] = CoinDCXLTPService(self.config, self.logger)

        # Initialize CoinDCX Funding Service
        if services_config.get('coindcx_funding', {}).get('enabled', True):
            self.services['coindcx_funding'] = CoinDCXFundingService(self.config, self.logger)

        # Initialize Bybit Spot Service
        if services_config.get('bybit_spot', {}).get('enabled', True):
            self.services['bybit_spot'] = BybitSpotServiceClass(self.config, self.logger)

        self.logger.info(f"Initialized {len(self.services)} services: {list(self.services.keys())}")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def start_service(self, name: str, service) -> bool:
        """Start a single service and create its task."""
        try:
            self.logger.info(f"Starting service: {name}")
            task = asyncio.create_task(service.start())
            self.service_tasks[name] = task
            return True

        except Exception as e:
            self.logger.error(f"Failed to start service {name}: {e}")
            return False

    async def stop_service(self, name: str, service) -> bool:
        """Stop a single service and its task."""
        try:
            self.logger.info(f"Stopping service: {name}")

            # Stop the service
            await service.stop()

            # Cancel the task if it exists
            if name in self.service_tasks:
                task = self.service_tasks[name]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self.service_tasks[name]

            return True

        except Exception as e:
            self.logger.error(f"Error stopping service {name}: {e}")
            return False

    async def health_monitor(self):
        """Monitor health of all services."""
        monitoring_config = self.config.get('monitoring', {})
        check_interval = monitoring_config.get('health_check_interval', 30)
        status_interval = monitoring_config.get('status_update_interval', 60)

        last_status_update = 0

        while self.running:
            try:
                current_time = datetime.now()

                # Collect health data from all services
                health_data = {}
                for name, service in self.services.items():
                    try:
                        health_data[name] = await service.health_check()
                    except Exception as e:
                        health_data[name] = {
                            'service': name,
                            'healthy': False,
                            'error': str(e)
                        }

                # Log detailed status periodically
                if (current_time.timestamp() - last_status_update) >= status_interval:
                    self.logger.info("=== Service Health Status ===")
                    for name, health in health_data.items():
                        status = "✅ HEALTHY" if health.get('healthy', False) else "❌ UNHEALTHY"
                        self.logger.info(f"{status} {name}: {health}")
                    last_status_update = current_time.timestamp()

                # Check for unhealthy services that need restart
                auto_restart = monitoring_config.get('auto_restart', True)
                if auto_restart:
                    await self.handle_unhealthy_services(health_data)

                await asyncio.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(check_interval)

    async def handle_unhealthy_services(self, health_data: Dict[str, Dict]):
        """Handle unhealthy services by attempting restart."""
        monitoring_config = self.config.get('monitoring', {})
        max_restart_attempts = monitoring_config.get('max_restart_attempts', 5)
        restart_delay = monitoring_config.get('restart_delay', 10)

        for name, health in health_data.items():
            if not health.get('healthy', False) and name in self.services:
                # Check if service task has failed
                task = self.service_tasks.get(name)
                if task and task.done() and not task.cancelled():
                    self.logger.warning(f"Service {name} task has completed unexpectedly, restarting...")

                    # Stop and restart the service
                    service = self.services[name]
                    await self.stop_service(name, service)
                    await asyncio.sleep(restart_delay)
                    await self.start_service(name, service)

    async def shutdown(self):
        """Graceful shutdown of all services."""
        self.logger.info("🛑 Initiating graceful shutdown...")
        self.running = False

        # Stop all services
        stop_tasks = []
        for name, service in self.services.items():
            task = asyncio.create_task(self.stop_service(name, service))
            stop_tasks.append(task)

        # Wait for all services to stop
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        self.shutdown_event.set()
        self.logger.info("✅ Graceful shutdown completed")

    async def run(self):
        """Main run loop for the unified monitor."""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🚀 UNIFIED CRYPTO MONITOR STARTING")
            self.logger.info("=" * 60)
            self.logger.info(f"Services to start: {list(self.services.keys())}")

            self.setup_signal_handlers()
            self.running = True

            # Start all services
            start_tasks = []
            for name, service in self.services.items():
                task = asyncio.create_task(self.start_service(name, service))
                start_tasks.append(task)

            # Wait for all services to start
            start_results = await asyncio.gather(*start_tasks, return_exceptions=True)

            # Check which services started successfully
            started_services = [
                name for i, name in enumerate(self.services.keys())
                if start_results[i] is True
            ]

            self.logger.info(f"✅ Started {len(started_services)} services successfully")

            if not started_services:
                self.logger.error("❌ No services started successfully, shutting down")
                return

            # Start health monitor
            health_task = asyncio.create_task(self.health_monitor())

            # Wait for shutdown signal
            await self.shutdown_event.wait()

            # Cancel health monitor
            health_task.cancel()
            try:
                await health_task
            except asyncio.CancelledError:
                pass

        except Exception as e:
            self.logger.error(f"❌ Fatal error in main run loop: {e}")
        finally:
            self.logger.info("🏁 Unified Crypto Monitor stopped")


async def main():
    """Main entry point."""
    # Handle command line arguments
    config_path = "config/unified_config.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    try:
        monitor = UnifiedCryptoMonitor(config_path)
        await monitor.run()

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unhandled error: {e}")
        sys.exit(1)