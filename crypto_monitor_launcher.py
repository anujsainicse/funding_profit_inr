#!/usr/bin/env python3
"""
Unified Crypto Monitor Launcher
Simultaneously runs multiple cryptocurrency monitoring programs:
1. CoinDCX Futures Funding Rate Monitor
2. CoinDCX Futures LTP WebSocket Monitor
3. Bybit Spot Price Monitor

Features:
- Runs all programs in separate processes
- Graceful shutdown handling
- Process monitoring and restart capabilities
- Centralized logging and status monitoring
"""

import asyncio
import multiprocessing
import signal
import sys
import os
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_monitor_launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CryptoLauncher')

class ProcessManager:
    """Manages multiple cryptocurrency monitoring processes"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # Try environment variable first, fallback to current directory
            base_dir = os.environ.get('CRYPTO_MONITOR_BASE_DIR', os.getcwd())

        # Ensure base_dir is absolute path
        self.base_dir = os.path.abspath(base_dir)

        # Smart path detection: if we're already in funding_profit_inr_ltp, use current dir
        # Otherwise, append funding_profit_inr_ltp to base_dir
        if os.path.basename(self.base_dir) == 'funding_profit_inr_ltp':
            self.funding_profit_dir = self.base_dir
        else:
            self.funding_profit_dir = os.path.join(self.base_dir, 'funding_profit_inr_ltp')

        self.processes: Dict[str, subprocess.Popen] = {}
        self.process_configs = {
            'coindcx_funding_rates': {
                'script': os.path.join(self.funding_profit_dir, 'coindcx_fu_fr.py'),
                'description': 'CoinDCX Futures Funding Rate Monitor',
                'restart_on_exit': True,
                'restart_delay': 10
            },
            'coindcx_ltp_websocket': {
                'script': os.path.join(self.funding_profit_dir, 'coindcx_fu_ltp_ws_redis.py'),
                'description': 'CoinDCX Futures LTP WebSocket Monitor',
                'restart_on_exit': True,
                'restart_delay': 5
            },
            'bybit_spot_monitor': {
                'script': os.path.join(self.funding_profit_dir, 'bybitspotpy', 'src', 'main.py'),
                'description': 'Bybit Spot Price Monitor',
                'restart_on_exit': True,
                'restart_delay': 5,
                'working_dir': os.path.join(self.funding_profit_dir, 'bybitspotpy'),
                'run_as_module': True,
                'module_path': 'src.main'
            }
        }
        self.shutdown_event = multiprocessing.Event()
        self.running = True

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_process(self, name: str, config: dict) -> bool:
        """Start a single process"""
        try:
            script_path = config['script']

            # Check if script exists
            if not os.path.exists(script_path):
                logger.error(f"Script not found: {script_path}")
                return False

            # Prepare command
            if config.get('run_as_module', False):
                # Run as Python module
                cmd = [sys.executable, '-m', config['module_path']]
                cwd = config.get('working_dir')
            else:
                # Run as script
                cmd = [sys.executable, script_path]
                cwd = os.path.dirname(script_path)

            logger.info(f"Starting {config['description']}...")
            logger.info(f"Command: {' '.join(cmd)}")
            logger.info(f"Working directory: {cwd}")

            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            self.processes[name] = process
            logger.info(f"✅ Started {config['description']} (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start {config['description']}: {e}")
            return False

    def stop_process(self, name: str) -> bool:
        """Stop a single process"""
        if name not in self.processes:
            return True

        process = self.processes[name]
        config = self.process_configs[name]

        try:
            logger.info(f"Stopping {config['description']} (PID: {process.pid})...")

            # Send SIGTERM first
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
                logger.info(f"✅ {config['description']} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning(f"Force killing {config['description']}...")
                process.kill()
                process.wait()
                logger.info(f"✅ {config['description']} force killed")

            del self.processes[name]
            return True

        except Exception as e:
            logger.error(f"❌ Error stopping {config['description']}: {e}")
            return False

    def check_process_health(self) -> Dict[str, bool]:
        """Check health of all processes"""
        health_status = {}

        for name, process in list(self.processes.items()):
            try:
                # Check if process is still running
                poll_result = process.poll()

                if poll_result is None:
                    # Process is still running
                    health_status[name] = True
                else:
                    # Process has exited
                    config = self.process_configs[name]
                    logger.warning(f"⚠️ {config['description']} has exited with code {poll_result}")
                    health_status[name] = False

                    # Remove from active processes
                    del self.processes[name]

                    # Schedule restart if configured
                    if config.get('restart_on_exit', False) and self.running:
                        restart_delay = config.get('restart_delay', 5)
                        logger.info(f"🔄 Scheduling restart for {config['description']} in {restart_delay} seconds...")

                        # Start restart in background
                        def delayed_restart():
                            time.sleep(restart_delay)
                            if self.running:  # Check if we're still supposed to be running
                                self.start_process(name, config)

                        import threading
                        restart_thread = threading.Thread(target=delayed_restart, daemon=True)
                        restart_thread.start()

            except Exception as e:
                logger.error(f"❌ Error checking health of {name}: {e}")
                health_status[name] = False

        return health_status

    def start_all_processes(self):
        """Start all configured processes"""
        logger.info("🚀 Starting all cryptocurrency monitoring processes...")
        logger.info("=" * 80)

        success_count = 0

        for name, config in self.process_configs.items():
            if self.start_process(name, config):
                success_count += 1
            time.sleep(1)  # Small delay between starts

        logger.info("=" * 80)
        logger.info(f"📊 Started {success_count}/{len(self.process_configs)} processes successfully")

        if success_count == 0:
            logger.error("❌ No processes started successfully. Exiting.")
            return False

        return True

    def stop_all_processes(self):
        """Stop all running processes"""
        logger.info("🛑 Stopping all processes...")

        # Stop all processes
        for name in list(self.processes.keys()):
            self.stop_process(name)

        logger.info("✅ All processes stopped")

    def monitor_processes(self):
        """Monitor process health and provide status updates"""
        logger.info("👁️ Starting process monitoring...")
        logger.info("📊 Status updates every 30 seconds")
        logger.info("⏹️ Press Ctrl+C to stop all processes")
        logger.info("=" * 80)

        status_interval = 30  # seconds
        last_status_time = 0

        while self.running:
            try:
                current_time = time.time()

                # Check process health
                health_status = self.check_process_health()

                # Provide periodic status updates
                if current_time - last_status_time >= status_interval:
                    self.print_status_update(health_status)
                    last_status_time = current_time

                # Check if any processes are still running
                if not self.processes and self.running:
                    logger.warning("⚠️ No processes are running. Exiting monitor.")
                    break

                time.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                logger.info("⏹️ Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)

    def print_status_update(self, health_status: Dict[str, bool]):
        """Print a status update of all processes"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"\n📊 Status Update - {timestamp}")
        logger.info("-" * 60)

        for name, config in self.process_configs.items():
            if name in self.processes:
                process = self.processes[name]
                status = "🟢 RUNNING" if health_status.get(name, False) else "🔴 DEAD"
                logger.info(f"{config['description']:<35} | {status} (PID: {process.pid})")
            else:
                logger.info(f"{config['description']:<35} | 🔴 NOT RUNNING")

        logger.info("-" * 60)
        logger.info(f"Active processes: {len(self.processes)}/{len(self.process_configs)}")

    def shutdown(self):
        """Graceful shutdown of all processes"""
        logger.info("🔄 Initiating graceful shutdown...")
        self.running = False

        # Stop all processes
        self.stop_all_processes()

        logger.info("👋 Crypto Monitor Launcher shutdown complete")

    def run(self):
        """Main execution method"""
        logger.info("🚀 Unified Crypto Monitor Launcher Starting...")
        logger.info("=" * 80)
        logger.info("Configured Processes:")
        for name, config in self.process_configs.items():
            logger.info(f"  • {config['description']}")
        logger.info("=" * 80)

        # Setup signal handlers
        self.setup_signal_handlers()

        # Start all processes
        if not self.start_all_processes():
            return False

        # Monitor processes
        try:
            self.monitor_processes()
        except Exception as e:
            logger.error(f"❌ Error in main execution: {e}")
        finally:
            self.shutdown()

        return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Unified Crypto Monitor Launcher - Runs multiple cryptocurrency monitoring programs simultaneously',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crypto_monitor_launcher.py
  python crypto_monitor_launcher.py --base-dir /path/to/your/project
  CRYPTO_MONITOR_BASE_DIR=/path/to/project python crypto_monitor_launcher.py

Environment Variables:
  CRYPTO_MONITOR_BASE_DIR    Base directory for the project (fallback if --base-dir not provided)
        """
    )

    parser.add_argument(
        '--base-dir', '-d',
        type=str,
        help='Base directory path for the crypto monitoring project (default: current directory or CRYPTO_MONITOR_BASE_DIR env var)'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Crypto Monitor Launcher 1.0.0'
    )

    return parser.parse_args()

def main():
    """Main entry point"""
    try:
        args = parse_arguments()

        # Log configuration info
        if args.base_dir:
            logger.info(f"Using base directory from command line: {args.base_dir}")
        elif os.environ.get('CRYPTO_MONITOR_BASE_DIR'):
            logger.info(f"Using base directory from environment: {os.environ.get('CRYPTO_MONITOR_BASE_DIR')}")
        else:
            logger.info(f"Using default base directory: {os.getcwd()}")

        manager = ProcessManager(base_dir=args.base_dir)
        logger.info(f"📁 Project base directory: {manager.base_dir}")
        logger.info(f"📁 Funding profit directory: {manager.funding_profit_dir}")

        success = manager.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()