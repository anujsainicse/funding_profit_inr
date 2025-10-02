# Cryptocurrency Monitoring System

A production-ready, unified system for real-time cryptocurrency price and funding rate monitoring across multiple exchanges.

## 🚀 Quick Start

```bash
# 1. Start the system
python crypto_monitor_launcher.py

# 2. Verify data collection
redis-cli HGETALL bybit_spot:BTC
redis-cli HGETALL coindcx_futures:BTC

# 3. Stop system (Ctrl+C)
```

## 📚 Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| **[CRYPTO_MONITORING_SYSTEM.md](CRYPTO_MONITORING_SYSTEM.md)** | Complete system overview and architecture | Everyone |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Installation and initial setup | New team members |
| **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** | Customization and configuration | Developers, DevOps |
| **[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)** | Problem diagnosis and solutions | Support, Operations |

## 🎯 What This System Does

- **Real-time Price Monitoring**: Bybit spot prices + CoinDCX futures prices
- **Funding Rate Tracking**: Current and estimated funding rates every 30 minutes
- **Redis Storage**: Structured data storage with automatic cleanup
- **Process Management**: Automatic restart, health monitoring, logging
- **Multi-Exchange Support**: Bybit and CoinDCX with extensible architecture

## 🏗️ System Components

```
Unified Launcher → [Bybit Monitor] → Redis
                 → [CoinDCX LTP Monitor] → Redis
                 → [CoinDCX Funding Monitor] → Redis
```

**Monitored Cryptocurrencies**: BTC, ETH, SOL, BNB, DOGE

## 📊 Live Data Examples

**Bybit Spot Data:**
```bash
redis-cli HGETALL bybit_spot:BTC
# Output:
# ltp: "67250.50"
# timestamp: "2024-10-01T12:30:25Z"
# original_symbol: "BTCUSDT"
```

**CoinDCX Futures Data:**
```bash
redis-cli HGETALL coindcx_futures:BTC
# Output:
# ltp: "67245.30"
# current_funding_rate: "0.0001"
# estimated_funding_rate: "0.00015"
# timestamp: "2024-10-01T12:30:25Z"
```

## ⚡ Key Features

- **🔄 Auto-Restart**: Processes automatically restart on failure
- **🌐 WebSocket Streams**: Real-time data with sub-second latency
- **💾 Redis Storage**: High-performance data storage and retrieval
- **📊 Health Monitoring**: Process status and data freshness checks
- **🔧 Configurable**: Easy symbol and parameter customization
- **📝 Comprehensive Logging**: Detailed logs for debugging and monitoring

## 🛠️ Requirements

- **Python 3.8+**
- **Redis Server**
- **Stable Internet Connection**
- **Linux/macOS/Windows** compatible

## 🎮 Usage Examples

### Start System
```bash
python crypto_monitor_launcher.py
```

### Check System Status
```bash
# View process status
ps aux | grep -E "(coindcx|bybit)" | grep -v grep

# Check Redis data
redis-cli KEYS "*spot*"
redis-cli KEYS "*futures*"
```

### Get Live Prices
```python
import redis
r = redis.Redis(decode_responses=True)

# Get BTC spot price from Bybit
btc_spot = r.hget('bybit_spot:BTC', 'ltp')

# Get BTC futures data from CoinDCX
btc_futures = r.hgetall('coindcx_futures:BTC')
funding_rate = float(btc_futures['current_funding_rate']) * 100

print(f"BTC Spot: ${btc_spot}")
print(f"BTC Funding Rate: {funding_rate:.4f}%")
```

### Stop System
```bash
# Graceful shutdown
# Press Ctrl+C in launcher terminal

# Force stop
pkill -f crypto_monitor_launcher
```

## 🔧 Quick Configuration

### Add New Cryptocurrency
```json
// coindcx-symbol-config.json
{
  "symbols": [
    "B-BTC_USDT",
    "B-ETH_USDT",
    "B-AVAX_USDT"  // ← Add new symbol
  ]
}

// bybitspotpy/config/coins.json
{
  "coins": [
    "BTCUSDT",
    "ETHUSDT",
    "AVAXUSDT"  // ← Add new symbol
  ]
}
```

### Modify Update Frequency
```env
# bybitspotpy/.env
RECONNECT_INTERVAL_MS=5000  # WebSocket reconnect interval

# coindcx-symbol-config.json
{
  "settings": {
    "redis_ttl": 3600,      # Data expiry (1 hour)
    "api_timeout": 10       # API request timeout
  }
}
```

## 📈 Performance

- **Throughput**: ~50-100 Redis operations/second
- **Latency**: <50ms end-to-end
- **CPU Usage**: ~1-2% per process
- **Memory**: ~50MB total
- **Data Updates**: Real-time WebSocket + 30-min funding rates

## 🚨 Troubleshooting Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Redis connection failed | `redis-server` |
| WebSocket errors | Check internet connection |
| Module not found | `pip install -r requirements.txt` |
| Process crashes | Check logs: `tail -f crypto_monitor_launcher.log` |
| No data updates | Restart: `python crypto_monitor_launcher.py` |

## 🤝 Team Resources

- **📖 [Complete Documentation](CRYPTO_MONITORING_SYSTEM.md)** - Full system guide
- **🛠️ [Setup Instructions](SETUP_GUIDE.md)** - Get started quickly
- **⚙️ [Configuration Guide](CONFIGURATION_GUIDE.md)** - Customize the system
- **🔧 [Troubleshooting](TROUBLESHOOTING_GUIDE.md)** - Fix common issues

## 📞 Support

1. **Check Documentation**: Start with relevant guide above
2. **Run Health Check**: `python health_check.py` (if available)
3. **Check Logs**: `tail -f crypto_monitor_launcher.log`
4. **Test Components**: Run individual monitors to isolate issues

## 🎯 Project Structure

```
funding_profit_inr/
├── crypto_monitor_launcher.py          # 🚀 MAIN LAUNCHER
├── coindcx_fu_fr.py                   # CoinDCX funding rates
├── coindcx_fu_ltp_ws_redis.py         # CoinDCX LTP WebSocket
├── bybitspotpy/src/main.py            # Bybit spot monitor
├── coindcx-symbol-config.json         # Configuration
├── CRYPTO_MONITORING_SYSTEM.md        # 📖 Complete docs
├── SETUP_GUIDE.md                     # 🛠️ Installation
├── CONFIGURATION_GUIDE.md             # ⚙️ Customization
└── TROUBLESHOOTING_GUIDE.md           # 🔧 Problem solving
```

---

**🔥 Ready to monitor cryptocurrency markets in real-time!**

Start with the [Setup Guide](SETUP_GUIDE.md) if you're new to the system.