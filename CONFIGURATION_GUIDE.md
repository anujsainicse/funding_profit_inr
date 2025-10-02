# Configuration Guide - Cryptocurrency Monitoring System

This guide explains how to configure and customize the cryptocurrency monitoring system for your specific needs.

## 📋 Configuration Overview

The system uses multiple configuration files to control different aspects:

| File | Purpose | Format |
|------|---------|---------|
| `coindcx-symbol-config.json` | CoinDCX symbols & settings | JSON |
| `bybitspotpy/.env` | Bybit environment variables | ENV |
| `bybitspotpy/config/coins.json` | Bybit coin list | JSON |
| `crypto_monitor_launcher.py` | Process management settings | Python |

## 🎯 Quick Configuration

### **1. Add/Remove Cryptocurrencies**

**For both CoinDCX and Bybit:**
```bash
# Edit CoinDCX symbols
nano coindcx-symbol-config.json

# Edit Bybit symbols
nano bybitspotpy/config/coins.json
```

**Example - Adding AVAX:**
```json
// coindcx-symbol-config.json
{
  "symbols": [
    "B-BTC_USDT",
    "B-ETH_USDT",
    "B-SOL_USDT",
    "B-BNB_USDT",
    "B-DOGE_USDT",
    "B-AVAX_USDT"  // ← Add this
  ]
}

// bybitspotpy/config/coins.json
{
  "coins": [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "DOGEUSDT",
    "AVAXUSDT"  // ← Add this
  ]
}
```

### **2. Change Update Intervals**

**Funding Rate Updates (CoinDCX):**
```python
# In coindcx_fu_fr.py, line ~470
time.sleep(30 * 60)  # 30 minutes
# Change to: time.sleep(15 * 60)  # 15 minutes
```

**WebSocket Reconnection:**
```env
# In bybitspotpy/.env
RECONNECT_INTERVAL_MS=5000    # 5 seconds
RECONNECT_MAX_ATTEMPTS=10     # 10 attempts
```

### **3. Modify Redis Settings**

```json
// In coindcx-symbol-config.json
{
  "settings": {
    "redis_ttl": 3600,        // 1 hour data expiry
    "api_timeout": 10,        // 10 second API timeout
    "reconnect_delay": 5,     // 5 second reconnect delay
    "max_reconnect_attempts": 10
  }
}
```

---

## 🔧 Detailed Configuration

### **1. CoinDCX Configuration**

#### **Symbol Configuration**
File: `coindcx-symbol-config.json`

```json
{
  "symbols": [
    "B-BTC_USDT",     // Binance-style perpetual
    "B-ETH_USDT",     // Popular altcoin
    "B-SOL_USDT",     // Layer 1 blockchain
    "B-BNB_USDT",     // Exchange token
    "B-DOGE_USDT",    // Meme coin
    "F-BTC_USDT",     // Futures contract (quarterly)
    "BM-BTC_USD"      // USD margined contract
  ],
  "settings": {
    "api_timeout": 10,              // HTTP request timeout (seconds)
    "redis_ttl": 3600,              // Redis key expiry (seconds)
    "reconnect_delay": 5,           // WebSocket reconnect delay (seconds)
    "max_reconnect_attempts": 10,   // Max reconnection tries
    "funding_rate_interval": 1800,  // Funding rate fetch interval (seconds)
    "health_check_interval": 30     // Health check frequency (seconds)
  }
}
```

#### **Available Symbol Formats**
```json
{
  "perpetual_contracts": [
    "B-BTC_USDT",    // Binance-style USDT margined
    "B-ETH_USDT",    // Popular perpetuals
    "B-ADA_USDT"     // Altcoin perpetuals
  ],
  "futures_contracts": [
    "F-BTC_USDT",    // Quarterly futures
    "F-ETH_USDT"     // Expiring contracts
  ],
  "usd_margined": [
    "BM-BTC_USD",    // USD margined (if available)
    "BM-ETH_USD"     // Settled in USD
  ]
}
```

### **2. Bybit Configuration**

#### **Environment Variables**
File: `bybitspotpy/.env`

```env
# ========================================
# BYBIT WEBSOCKET CONFIGURATION
# ========================================
BYBIT_WS_URL=wss://stream.bybit.com/v5/public/spot
# Alternative: wss://stream-testnet.bybit.com/v5/public/spot (for testing)

# ========================================
# REDIS CONFIGURATION
# ========================================
REDIS_HOST=localhost          # Redis server host
REDIS_PORT=6379              # Redis server port
REDIS_PASSWORD=              # Redis password (leave empty if none)
REDIS_DB=0                   # Redis database number
REDIS_TIMEOUT=5              # Connection timeout (seconds)

# ========================================
# APPLICATION CONFIGURATION
# ========================================
LOG_LEVEL=info               # Logging level: debug, info, warning, error
ENABLE_HEALTH_CHECK=false    # Enable health check endpoint
HEALTH_CHECK_PORT=3000       # Health check server port

# ========================================
# RECONNECTION CONFIGURATION
# ========================================
RECONNECT_INTERVAL_MS=5000   # Base reconnection interval (milliseconds)
RECONNECT_MAX_ATTEMPTS=10    # Maximum reconnection attempts
RECONNECT_BACKOFF=exponential # Backoff strategy: linear, exponential

# ========================================
# PERFORMANCE TUNING
# ========================================
PING_INTERVAL=20             # WebSocket ping interval (seconds)
PING_TIMEOUT=10              # WebSocket ping timeout (seconds)
MAX_MESSAGE_SIZE=1048576     # Max WebSocket message size (bytes)
BUFFER_SIZE=8192             # Network buffer size (bytes)
```

#### **Coin List Configuration**
File: `bybitspotpy/config/coins.json`

```json
{
  "coins": [
    "BTCUSDT",        // Bitcoin
    "ETHUSDT",        // Ethereum
    "SOLUSDT",        // Solana
    "BNBUSDT",        // Binance Coin
    "DOGEUSDT",       // Dogecoin
    "ADAUSDT",        // Cardano
    "DOTUSDT",        // Polkadot
    "AVAXUSDT",       // Avalanche
    "MATICUSDT",      // Polygon
    "LINKUSDT"        // Chainlink
  ],
  "settings": {
    "update_interval": 1,      // Minimum update interval (seconds)
    "price_precision": 8,      // Decimal places for prices
    "volume_threshold": 0.01   // Minimum volume for updates
  }
}
```

### **3. Launcher Configuration**

#### **Process Settings**
File: `crypto_monitor_launcher.py` (lines 25-45)

```python
self.process_configs = {
    'coindcx_funding_rates': {
        'script': '/path/to/coindcx_fu_fr.py',
        'description': 'CoinDCX Futures Funding Rate Monitor',
        'restart_on_exit': True,          # Auto-restart on crash
        'restart_delay': 10,              # Delay before restart (seconds)
        'max_restarts': 5,                # Max restarts per hour
        'priority': 'normal'              # Process priority
    },
    'coindcx_ltp_websocket': {
        'script': '/path/to/coindcx_fu_ltp_ws_redis.py',
        'description': 'CoinDCX Futures LTP WebSocket Monitor',
        'restart_on_exit': True,
        'restart_delay': 5,
        'max_restarts': 10,
        'priority': 'high'                # Higher priority for real-time data
    },
    'bybit_spot_monitor': {
        'script': '/path/to/bybitspotpy/src/main.py',
        'description': 'Bybit Spot Price Monitor',
        'restart_on_exit': True,
        'restart_delay': 5,
        'working_dir': '/path/to/bybitspotpy',
        'run_as_module': True,
        'module_path': 'src.main',
        'priority': 'high'
    }
}
```

#### **Monitoring Settings**
```python
# Status update frequency (seconds)
status_interval = 30

# Process health check interval (seconds)
health_check_interval = 5

# Log file configuration
log_file = 'crypto_monitor_launcher.log'
log_level = logging.INFO
log_rotation = True
max_log_size = '10MB'
backup_count = 5
```

## 🎨 Customization Examples

### **Example 1: High-Frequency Trading Setup**

**Goal**: Sub-second updates, minimal latency

```json
// coindcx-symbol-config.json
{
  "symbols": ["B-BTC_USDT", "B-ETH_USDT"],  // Only major pairs
  "settings": {
    "api_timeout": 5,                        // Faster timeout
    "redis_ttl": 300,                        // 5-minute expiry
    "reconnect_delay": 1,                    // Immediate reconnection
    "max_reconnect_attempts": 50,            // Aggressive reconnection
    "health_check_interval": 1               // Every second
  }
}
```

```env
# bybitspotpy/.env
RECONNECT_INTERVAL_MS=1000    # 1 second
LOG_LEVEL=warning             # Reduce log noise
PING_INTERVAL=5               # Frequent pings
```

### **Example 2: Research/Analytics Setup**

**Goal**: Historical data retention, all symbols

```json
// Extended symbol list
{
  "symbols": [
    "B-BTC_USDT", "B-ETH_USDT", "B-SOL_USDT", "B-BNB_USDT",
    "B-DOGE_USDT", "B-ADA_USDT", "B-DOT_USDT", "B-AVAX_USDT",
    "B-MATIC_USDT", "B-LINK_USDT", "B-UNI_USDT", "B-LTC_USDT"
  ],
  "settings": {
    "redis_ttl": 86400,         // 24-hour retention
    "api_timeout": 15,          // Longer timeout for stability
    "reconnect_delay": 10,      // Conservative reconnection
    "funding_rate_interval": 900 // 15-minute intervals
  }
}
```

### **Example 3: Production Monitoring**

**Goal**: Maximum stability, monitoring alerts

```python
# Enhanced launcher configuration
self.process_configs = {
    'coindcx_funding_rates': {
        'restart_on_exit': True,
        'restart_delay': 30,        # Conservative restart
        'max_restarts': 3,          # Limited restarts
        'alert_on_failure': True,   # Send alerts
        'health_check_url': 'http://localhost:8080/health'
    }
}

# Monitoring settings
status_interval = 60           # Every minute
alert_threshold = 300          # Alert if no data for 5 minutes
log_level = logging.WARNING    # Only warnings and errors
```

## 🔀 Advanced Configuration

### **1. Multi-Exchange Setup**

**Adding Binance Support:**
```python
# In crypto_monitor_launcher.py
self.process_configs['binance_spot_monitor'] = {
    'script': '/path/to/binance_monitor.py',
    'description': 'Binance Spot Price Monitor',
    'restart_on_exit': True,
    'restart_delay': 5
}
```

### **2. Database Integration**

**PostgreSQL Storage:**
```python
# Add to coindcx_fu_fr.py
import psycopg2

def save_to_postgres(funding_data):
    conn = psycopg2.connect(
        host="localhost",
        database="crypto_db",
        user="crypto_user",
        password="password"
    )
    # Insert funding rate data
```

### **3. Real-time Alerts**

**Slack Integration:**
```python
# Add to any monitor
import requests

def send_alert(message):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    requests.post(webhook_url, json={"text": message})

# Alert on funding rate changes
if abs(current_rate - previous_rate) > 0.001:  # 0.1% change
    send_alert(f"BTC funding rate changed: {current_rate:.4f}%")
```

### **4. Load Balancing**

**Multiple Redis Instances:**
```python
# Redis cluster configuration
REDIS_CLUSTERS = [
    {"host": "redis1.local", "port": 6379},
    {"host": "redis2.local", "port": 6379},
    {"host": "redis3.local", "port": 6379}
]

# Hash-based distribution
def get_redis_client(symbol):
    cluster_id = hash(symbol) % len(REDIS_CLUSTERS)
    return redis.Redis(**REDIS_CLUSTERS[cluster_id])
```

## 🎯 Configuration Best Practices

### **1. Environment-Specific Configs**

```bash
# Development
cp .env.example .env.dev

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.prod
```

### **2. Configuration Validation**

Create `validate_config.py`:
```python
#!/usr/bin/env python3
import json
import os

def validate_coindcx_config():
    with open('coindcx-symbol-config.json') as f:
        config = json.load(f)

    # Validate symbols format
    for symbol in config['symbols']:
        if not symbol.startswith(('B-', 'F-', 'BM-')):
            print(f"Invalid symbol format: {symbol}")
            return False

    # Validate settings
    settings = config.get('settings', {})
    if settings.get('redis_ttl', 0) < 300:
        print("Redis TTL too low (minimum 300 seconds)")
        return False

    return True

def validate_bybit_config():
    env_file = 'bybitspotpy/.env'
    if not os.path.exists(env_file):
        print(f"Missing {env_file}")
        return False

    with open(env_file) as f:
        lines = f.readlines()

    required_vars = ['BYBIT_WS_URL', 'REDIS_HOST', 'REDIS_PORT']
    for var in required_vars:
        if not any(line.startswith(f"{var}=") for line in lines):
            print(f"Missing required variable: {var}")
            return False

    return True

if __name__ == "__main__":
    if validate_coindcx_config() and validate_bybit_config():
        print("✅ Configuration validation passed")
    else:
        print("❌ Configuration validation failed")
```

### **3. Configuration Backup**

```bash
# Create configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    coindcx-symbol-config.json \
    bybitspotpy/.env \
    bybitspotpy/config/coins.json

# Restore configuration
tar -xzf config_backup_20241001.tar.gz
```

### **4. Hot Configuration Reload**

```python
# Add to monitors for dynamic config updates
import signal
import json

def reload_config(signum, frame):
    global config
    with open('coindcx-symbol-config.json') as f:
        config = json.load(f)
    print("Configuration reloaded")

signal.signal(signal.SIGUSR1, reload_config)

# Send reload signal
# kill -USR1 <process_id>
```

## 📊 Configuration Monitoring

### **Check Active Configuration**
```bash
# View current CoinDCX symbols
cat coindcx-symbol-config.json | jq '.symbols'

# View Bybit environment
cat bybitspotpy/.env | grep -v "^#"

# Check Redis keys pattern
redis-cli KEYS "*" | head -10
```

### **Configuration Drift Detection**
```python
import hashlib
import json

def config_checksum():
    configs = [
        'coindcx-symbol-config.json',
        'bybitspotpy/.env',
        'bybitspotpy/config/coins.json'
    ]

    content = ""
    for config_file in configs:
        with open(config_file, 'r') as f:
            content += f.read()

    return hashlib.md5(content.encode()).hexdigest()

# Store baseline checksum
baseline = config_checksum()

# Check for changes
if config_checksum() != baseline:
    print("⚠️ Configuration has changed!")
```

---

## 🔄 Configuration Update Workflow

1. **Backup Current Config**: Always backup before changes
2. **Update Configuration Files**: Make targeted changes
3. **Validate Configuration**: Run validation scripts
4. **Test with Subset**: Test with limited symbols first
5. **Deploy to Production**: Apply changes to full system
6. **Monitor Results**: Verify data collection continues
7. **Rollback if Needed**: Restore backup if issues arise

**Ready to customize your crypto monitoring system!** 🚀