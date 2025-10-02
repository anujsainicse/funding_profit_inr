#!/usr/bin/env python3
"""
Health Check Script for Cryptocurrency Monitoring System

Quick diagnostic tool to verify system components are working correctly.
Run this script to check the health of Redis, data collection, and process status.
"""

import redis
import subprocess
import sys
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(check: str, status: bool, details: str = ""):
    """Print a check result with status icon"""
    icon = "✅" if status else "❌"
    print(f"{icon} {check:<40} {details}")

def check_redis_connection() -> Tuple[bool, str]:
    """Check Redis server connectivity"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_timeout=5)
        response = r.ping()
        if response:
            info = r.info('server')
            redis_version = info.get('redis_version', 'Unknown')
            return True, f"Connected (v{redis_version})"
        else:
            return False, "Ping failed"
    except redis.ConnectionError:
        return False, "Connection refused (Redis not running?)"
    except redis.TimeoutError:
        return False, "Connection timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_redis_data() -> Tuple[bool, Dict]:
    """Check if monitoring data exists in Redis"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Check Bybit spot data
        bybit_keys = r.keys('bybit_spot:*')

        # Check CoinDCX futures data
        coindcx_keys = r.keys('coindcx_futures:*')

        return True, {
            'bybit_symbols': len(bybit_keys),
            'coindcx_symbols': len(coindcx_keys),
            'bybit_keys': sorted([key.split(':')[1] for key in bybit_keys]),
            'coindcx_keys': sorted([key.split(':')[1] for key in coindcx_keys])
        }
    except Exception as e:
        return False, {'error': str(e)}

def check_data_freshness() -> Tuple[bool, Dict]:
    """Check how fresh the data is (last update time)"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        now = datetime.now(timezone.utc)
        results = {}

        # Check Bybit BTC data
        btc_spot = r.hgetall('bybit_spot:BTC')
        if btc_spot and 'timestamp' in btc_spot:
            try:
                last_update = datetime.fromisoformat(btc_spot['timestamp'].replace('Z', '+00:00'))
                age_seconds = (now - last_update).total_seconds()
                results['bybit_btc'] = {
                    'price': btc_spot.get('ltp', 'N/A'),
                    'age_seconds': age_seconds,
                    'fresh': age_seconds < 60  # Fresh if less than 1 minute old
                }
            except ValueError:
                results['bybit_btc'] = {'error': 'Invalid timestamp format'}
        else:
            results['bybit_btc'] = {'error': 'No data found'}

        # Check CoinDCX BTC data
        btc_futures = r.hgetall('coindcx_futures:BTC')
        if btc_futures and 'timestamp' in btc_futures:
            try:
                last_update = datetime.fromisoformat(btc_futures['timestamp'].replace('Z', '+00:00'))
                age_seconds = (now - last_update).total_seconds()
                funding_rate = btc_futures.get('current_funding_rate', 'N/A')
                results['coindcx_btc'] = {
                    'price': btc_futures.get('ltp', 'N/A'),
                    'funding_rate': funding_rate,
                    'age_seconds': age_seconds,
                    'fresh': age_seconds < 300  # Fresh if less than 5 minutes old
                }
            except ValueError:
                results['coindcx_btc'] = {'error': 'Invalid timestamp format'}
        else:
            results['coindcx_btc'] = {'error': 'No data found'}

        return True, results
    except Exception as e:
        return False, {'error': str(e)}

def check_processes() -> Tuple[bool, List[Dict]]:
    """Check if monitoring processes are running"""
    try:
        # Get all Python processes that might be our monitors
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')

        processes = []
        for line in lines:
            if 'python' in line and any(keyword in line for keyword in [
                'crypto_monitor_launcher',
                'coindcx_fu_fr',
                'coindcx_fu_ltp_ws_redis',
                'src.main'
            ]):
                parts = line.split()
                if len(parts) >= 11:
                    process_info = {
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3],
                        'command': ' '.join(parts[10:])
                    }
                    processes.append(process_info)

        return True, processes
    except Exception as e:
        return False, [{'error': str(e)}]

def check_configuration() -> Tuple[bool, Dict]:
    """Check if configuration files exist and are valid"""
    try:
        config_status = {}

        # Check CoinDCX config
        try:
            with open('coindcx-symbol-config.json', 'r') as f:
                coindcx_config = json.load(f)
                config_status['coindcx_config'] = {
                    'exists': True,
                    'symbols_count': len(coindcx_config.get('symbols', [])),
                    'has_settings': 'settings' in coindcx_config
                }
        except FileNotFoundError:
            config_status['coindcx_config'] = {'exists': False, 'error': 'File not found'}
        except json.JSONDecodeError:
            config_status['coindcx_config'] = {'exists': True, 'error': 'Invalid JSON'}

        # Check Bybit config
        try:
            with open('bybitspotpy/.env', 'r') as f:
                env_content = f.read()
                has_redis_config = 'REDIS_HOST' in env_content
                has_ws_url = 'BYBIT_WS_URL' in env_content
                config_status['bybit_env'] = {
                    'exists': True,
                    'has_redis_config': has_redis_config,
                    'has_ws_url': has_ws_url
                }
        except FileNotFoundError:
            config_status['bybit_env'] = {'exists': False, 'error': 'File not found'}

        # Check Bybit coins config
        try:
            with open('bybitspotpy/config/coins.json', 'r') as f:
                coins_config = json.load(f)
                config_status['bybit_coins'] = {
                    'exists': True,
                    'coins_count': len(coins_config.get('coins', []))
                }
        except FileNotFoundError:
            config_status['bybit_coins'] = {'exists': False, 'error': 'File not found'}
        except json.JSONDecodeError:
            config_status['bybit_coins'] = {'exists': True, 'error': 'Invalid JSON'}

        return True, config_status
    except Exception as e:
        return False, {'error': str(e)}

def main():
    """Run comprehensive health check"""
    print("🏥 Cryptocurrency Monitoring System - Health Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    overall_health = True

    # Redis Connection Check
    print_header("Redis Connection")
    redis_ok, redis_details = check_redis_connection()
    print_result("Redis Server", redis_ok, redis_details)
    overall_health &= redis_ok

    if redis_ok:
        # Redis Data Check
        print_header("Data Collection")
        data_ok, data_info = check_redis_data()
        if data_ok:
            print_result("Bybit Spot Data",
                        data_info['bybit_symbols'] > 0,
                        f"{data_info['bybit_symbols']} symbols: {', '.join(data_info['bybit_keys'])}")
            print_result("CoinDCX Futures Data",
                        data_info['coindcx_symbols'] > 0,
                        f"{data_info['coindcx_symbols']} symbols: {', '.join(data_info['coindcx_keys'])}")
            overall_health &= (data_info['bybit_symbols'] > 0 and data_info['coindcx_symbols'] > 0)
        else:
            print_result("Redis Data", False, f"Error: {data_info.get('error', 'Unknown')}")
            overall_health = False

        # Data Freshness Check
        print_header("Data Freshness")
        fresh_ok, fresh_info = check_data_freshness()
        if fresh_ok:
            # Bybit BTC check
            btc_spot = fresh_info.get('bybit_btc', {})
            if 'error' not in btc_spot:
                age = btc_spot['age_seconds']
                print_result("Bybit BTC Data",
                            btc_spot['fresh'],
                            f"${btc_spot['price']} ({age:.1f}s ago)")
            else:
                print_result("Bybit BTC Data", False, btc_spot['error'])
                overall_health = False

            # CoinDCX BTC check
            btc_futures = fresh_info.get('coindcx_btc', {})
            if 'error' not in btc_futures:
                age = btc_futures['age_seconds']
                funding_rate = btc_futures['funding_rate']
                if funding_rate != 'N/A':
                    funding_pct = float(funding_rate) * 100
                    details = f"${btc_futures['price']}, {funding_pct:.4f}% funding ({age:.1f}s ago)"
                else:
                    details = f"${btc_futures['price']} ({age:.1f}s ago)"
                print_result("CoinDCX BTC Data",
                            btc_futures['fresh'],
                            details)
            else:
                print_result("CoinDCX BTC Data", False, btc_futures['error'])
                overall_health = False

    # Process Check
    print_header("Running Processes")
    proc_ok, processes = check_processes()
    if proc_ok and processes:
        for proc in processes:
            if 'error' not in proc:
                process_name = proc['command'].split()[-1] if proc['command'] else 'Unknown'
                if 'crypto_monitor_launcher' in proc['command']:
                    process_name = "Crypto Monitor Launcher"
                elif 'coindcx_fu_fr' in proc['command']:
                    process_name = "CoinDCX Funding Rates"
                elif 'coindcx_fu_ltp_ws_redis' in proc['command']:
                    process_name = "CoinDCX LTP WebSocket"
                elif 'src.main' in proc['command']:
                    process_name = "Bybit Spot Monitor"

                print_result(process_name, True, f"PID {proc['pid']} (CPU: {proc['cpu']}%, MEM: {proc['mem']}%)")

        # Check if we have all expected processes
        expected_processes = ['crypto_monitor_launcher', 'coindcx_fu_fr', 'coindcx_fu_ltp_ws_redis', 'src.main']
        running_processes = [proc['command'] for proc in processes if 'error' not in proc]

        for expected in expected_processes:
            found = any(expected in cmd for cmd in running_processes)
            if not found:
                print_result(f"Missing: {expected}", False, "Process not running")
                overall_health = False
    else:
        print_result("Process Detection", False, "No monitoring processes found")
        overall_health = False

    # Configuration Check
    print_header("Configuration Files")
    config_ok, config_info = check_configuration()
    if config_ok:
        coindcx_cfg = config_info.get('coindcx_config', {})
        print_result("CoinDCX Config",
                    coindcx_cfg.get('exists', False),
                    f"{coindcx_cfg.get('symbols_count', 0)} symbols" if coindcx_cfg.get('exists') else coindcx_cfg.get('error', ''))

        bybit_env = config_info.get('bybit_env', {})
        print_result("Bybit Environment",
                    bybit_env.get('exists', False),
                    "Redis + WebSocket configured" if bybit_env.get('has_redis_config') and bybit_env.get('has_ws_url') else bybit_env.get('error', ''))

        bybit_coins = config_info.get('bybit_coins', {})
        print_result("Bybit Coins Config",
                    bybit_coins.get('exists', False),
                    f"{bybit_coins.get('coins_count', 0)} coins" if bybit_coins.get('exists') else bybit_coins.get('error', ''))

    # Final Result
    print_header("Overall System Health")
    status_icon = "🟢" if overall_health else "🔴"
    status_text = "HEALTHY" if overall_health else "ISSUES DETECTED"
    print(f"{status_icon} System Status: {status_text}")

    if not overall_health:
        print("\n💡 Troubleshooting Tips:")
        print("   • Check if Redis is running: redis-cli ping")
        print("   • Start the system: python crypto_monitor_launcher.py")
        print("   • Check logs: tail -f crypto_monitor_launcher.log")
        print("   • Review documentation: TROUBLESHOOTING_GUIDE.md")

    print(f"\n📋 Health check completed at {datetime.now().strftime('%H:%M:%S')}")
    return 0 if overall_health else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)