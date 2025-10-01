# Unified Crypto Monitor

A centralized orchestrator that manages all your crypto monitoring services in one unified system.

## 🎯 Overview

The Unified Crypto Monitor provides a single point of control for running all three crypto monitoring services:

1. **CoinDCX Futures LTP Monitor** - Real-time last traded prices
2. **CoinDCX Funding Rate Monitor** - Periodic funding rate data
3. **Bybit Spot Price Monitor** - Real-time spot prices

## 🚀 Quick Start

### Option 1: Python Launcher (Recommended)
```bash
python3 start_all.py
```

### Option 2: Shell Script
```bash
./start_all.sh
```

### Option 3: Direct Launch
```bash
python3 unified_crypto_monitor.py
```

## ⚙️ Configuration

All services are configured through a single file: `config/unified_config.json`

### Key Configuration Sections:

- **`redis`** - Redis connection settings
- **`services`** - Individual service configurations
- **`logging`** - Centralized logging setup
- **`monitoring`** - Health monitoring and auto-restart
- **`symbol_mapping`** - Cross-exchange symbol mapping

### Service Configuration:

Each service can be individually enabled/disabled:

```json
{
  "services": {
    "coindcx_ltp": {
      "enabled": true,
      "symbols": ["B-BTC_USDT", "B-ETH_USDT"],
      "settings": {
        "redis_ttl": 3600,
        "reconnect_delay": 5
      }
    }
  }
}
```

## 📊 Features

### Centralized Management
- **Single Command**: Start/stop all services with one command
- **Unified Configuration**: One config file for all services
- **Centralized Logging**: All logs in one place with rotation

### Health Monitoring
- **Real-time Health Checks**: Continuous service monitoring
- **Auto-restart**: Automatically restart failed services
- **Status Reporting**: Regular health status updates

### Graceful Shutdown
- **Signal Handling**: Responds to Ctrl+C and system signals
- **Clean Termination**: Properly closes all WebSocket connections
- **Resource Cleanup**: Ensures Redis connections are closed

## 📁 Project Structure

```
funding_profit_inr/
├── unified_crypto_monitor.py    # Main orchestrator
├── start_all.py                 # Python launcher
├── start_all.sh                 # Shell launcher
├── config/
│   └── unified_config.json      # Main configuration
├── services/                    # Service wrappers
│   ├── __init__.py
│   ├── coindcx_ltp_service.py
│   ├── coindcx_funding_service.py
│   └── bybit_spot_service.py
├── logs/                        # Log files
│   └── unified_crypto_monitor.log
└── ... (existing files)
```

## 🔧 Service Details

### CoinDCX LTP Service
- **Purpose**: Real-time futures price monitoring
- **Protocol**: WebSocket
- **Update Frequency**: ~10 seconds
- **Redis Keys**: `coindcx_futures:{COIN}`

### CoinDCX Funding Service
- **Purpose**: Periodic funding rate collection
- **Protocol**: REST API
- **Update Frequency**: 5 minutes (configurable)
- **Redis Keys**: `coindcx_funding:{COIN}`

### Bybit Spot Service
- **Purpose**: Real-time spot price monitoring
- **Protocol**: WebSocket
- **Update Frequency**: Real-time
- **Redis Keys**: `bybit_spot:{COIN}`

## 📈 Monitoring & Health Checks

The system performs automatic health monitoring:

- **Health Check Interval**: 30 seconds (configurable)
- **Status Updates**: Every 60 seconds (configurable)
- **Auto-restart**: Enabled by default
- **Max Restart Attempts**: 5 per service

### Health Status Indicators:
- ✅ **HEALTHY** - Service running and receiving data
- ❌ **UNHEALTHY** - Service failed or not receiving data

## 📝 Logging

Centralized logging with rotation:

- **Console Output**: Real-time status and errors
- **File Logging**: Detailed logs with rotation (100MB max, 5 backups)
- **Log Levels**: INFO, DEBUG, WARNING, ERROR
- **Location**: `logs/unified_crypto_monitor.log`

## 🛠️ Troubleshooting

### Common Issues:

1. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   redis-cli ping

   # Start Redis if needed
   redis-server
   ```

2. **Service Import Errors**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Permission Denied**
   ```bash
   # Make scripts executable
   chmod +x start_all.py start_all.sh
   ```

### Checking Service Status:

Monitor the console output or check the log files for service health status.

## 🔄 Stopping Services

To stop all services gracefully:

1. **Press Ctrl+C** in the terminal
2. **Send SIGTERM** to the process
3. The system will gracefully shutdown all services

## ⚡ Performance

- **Memory Usage**: Shared Redis connections across services
- **CPU Usage**: Async/await for efficient resource utilization
- **Network**: Optimized WebSocket connections with auto-reconnect

## 🔒 Security

- **Environment Variables**: API credentials loaded from `.env`
- **Redis Security**: Connection settings configurable
- **Error Handling**: Comprehensive exception management

## 📞 Support

For issues or questions:
1. Check the log files in `logs/`
2. Verify Redis connectivity
3. Check service configurations
4. Review the console output for error messages

---

**Note**: Make sure Redis is running before starting the unified monitor, as all services depend on Redis for data storage.