# Setup Guide - Cryptocurrency Monitoring System

This guide will help your team members set up the cryptocurrency monitoring system from scratch.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.8+** installed
- [ ] **Redis server** installed and running
- [ ] **Git** access to the repository
- [ ] **Stable internet connection** for WebSocket streams
- [ ] **Administrator/sudo access** (for Redis installation if needed)

## 🚀 Quick Setup (5 Minutes)

### **Step 1: Clone the Repository**
```bash
git clone <your-repository-url>
cd funding_profit_inr
```

### **Step 2: Install Redis (if not installed)**

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
```bash
# Download Redis from: https://redis.io/download
# Or use Docker: docker run -d -p 6379:6379 redis:latest
```

### **Step 3: Install Python Dependencies**
```bash
# Install main dependencies
pip install requests redis python-dotenv websockets structlog watchdog

# Or if you have a requirements file
pip install -r requirements.txt
```

### **Step 4: Verify Redis Connection**
```bash
redis-cli ping
# Should return: PONG
```

### **Step 5: Start the System**
```bash
python crypto_monitor_launcher.py
```

### **Step 6: Verify Data Collection**
```bash
# In another terminal, check if data is flowing
redis-cli HGETALL bybit_spot:BTC
redis-cli HGETALL coindcx_futures:BTC
```

**✅ If you see price data, you're ready to go!**

---

## 🔧 Detailed Setup Instructions

### **1. Environment Setup**

#### **Python Environment (Recommended)**
```bash
# Create virtual environment
python -m venv crypto_monitor_env

# Activate environment
source crypto_monitor_env/bin/activate  # Linux/macOS
crypto_monitor_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### **System Dependencies**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip
pip --version

# Check git
git --version
```

### **2. Redis Setup & Configuration**

#### **Installation Verification**
```bash
# Check if Redis is running
redis-cli ping

# Check Redis version
redis-server --version

# View Redis configuration
redis-cli CONFIG GET "*"
```

#### **Redis Configuration (Optional)**
Create `/etc/redis/redis.conf` (or edit existing):
```conf
# Basic Redis configuration for crypto monitoring
bind 127.0.0.1
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### **Start Redis Automatically**
```bash
# macOS
brew services start redis

# Linux
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Manual start
redis-server
```

### **3. Project Configuration**

#### **Bybit Configuration**
Edit `bybitspotpy/.env`:
```env
# Bybit WebSocket Configuration
BYBIT_WS_URL=wss://stream.bybit.com/v5/public/spot

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Application Configuration
LOG_LEVEL=info
ENABLE_HEALTH_CHECK=false
HEALTH_CHECK_PORT=3000

# Reconnection Configuration
RECONNECT_INTERVAL_MS=5000
RECONNECT_MAX_ATTEMPTS=10
```

#### **CoinDCX Configuration**
Edit `coindcx-symbol-config.json`:
```json
{
  "symbols": [
    "B-BTC_USDT",
    "B-ETH_USDT",
    "B-SOL_USDT",
    "B-BNB_USDT",
    "B-DOGE_USDT"
  ],
  "settings": {
    "api_timeout": 10,
    "redis_ttl": 3600,
    "reconnect_delay": 5,
    "max_reconnect_attempts": 10
  }
}
```

#### **Bybit Coins Configuration**
Edit `bybitspotpy/config/coins.json`:
```json
{
  "coins": [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "DOGEUSDT"
  ]
}
```

### **4. Testing Individual Components**

#### **Test Redis Connection**
```bash
python -c "
import redis
r = redis.Redis(host='localhost', port=6379)
print('Redis connection:', r.ping())
"
```

#### **Test CoinDCX Funding Rates**
```bash
python coindcx_fu_fr.py
# Should fetch funding rates and store in Redis
```

#### **Test CoinDCX LTP WebSocket**
```bash
python coindcx_fu_ltp_ws_redis.py
# Should connect to WebSocket and stream prices
```

#### **Test Bybit Spot Monitor**
```bash
cd bybitspotpy
python -m src.main
# Should connect to Bybit and stream spot prices
```

### **5. Production Setup**

#### **Systemd Service (Linux)**
Create `/etc/systemd/system/crypto-monitor.service`:
```ini
[Unit]
Description=Cryptocurrency Monitoring System
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/funding_profit_inr
ExecStart=/path/to/python crypto_monitor_launcher.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/path/to/funding_profit_inr

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-monitor
sudo systemctl start crypto-monitor
```

#### **Docker Setup (Optional)**
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install Redis
RUN apt-get update && apt-get install -y redis-server

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Start script
COPY start_services.sh .
RUN chmod +x start_services.sh

EXPOSE 6379
CMD ["./start_services.sh"]
```

Create `start_services.sh`:
```bash
#!/bin/bash
redis-server --daemonize yes
python crypto_monitor_launcher.py
```

```bash
docker build -t crypto-monitor .
docker run -d -p 6379:6379 crypto-monitor
```

## 🔍 Verification & Testing

### **Health Check Script**
Create `health_check.py`:
```python
#!/usr/bin/env python3
import redis
import json
from datetime import datetime

def health_check():
    try:
        # Test Redis connection
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis: Connected")

        # Check Bybit data
        btc_spot = r.hgetall('bybit_spot:BTC')
        if btc_spot:
            print(f"✅ Bybit Spot: BTC = ${btc_spot.get('ltp', 'N/A')}")
        else:
            print("❌ Bybit Spot: No data")

        # Check CoinDCX data
        btc_futures = r.hgetall('coindcx_futures:BTC')
        if btc_futures:
            print(f"✅ CoinDCX Futures: BTC = ${btc_futures.get('ltp', 'N/A')}")
            print(f"✅ Funding Rate: {float(btc_futures.get('current_funding_rate', 0)) * 100:.4f}%")
        else:
            print("❌ CoinDCX Futures: No data")

        # Data freshness check
        if btc_spot and 'timestamp' in btc_spot:
            from datetime import datetime
            last_update = datetime.fromisoformat(btc_spot['timestamp'].replace('Z', '+00:00'))
            age = (datetime.now().astimezone() - last_update).total_seconds()
            if age < 60:
                print(f"✅ Data Freshness: {age:.1f} seconds old")
            else:
                print(f"⚠️ Data Freshness: {age:.1f} seconds old (might be stale)")

        print("✅ System Health: OK")
        return True

    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

if __name__ == "__main__":
    health_check()
```

Run health check:
```bash
python health_check.py
```

### **Performance Monitoring**
```bash
# Check CPU and memory usage
ps aux | grep -E "(python|redis)" | grep -v grep

# Check Redis memory usage
redis-cli INFO memory | grep used_memory_human

# Check network connections
netstat -an | grep -E "(6379|443|80)"

# Monitor log files
tail -f crypto_monitor_launcher.log
```

### **Data Verification**
```bash
# Count total symbols
redis-cli EVAL "return #redis.call('keys', 'bybit_spot:*')" 0
redis-cli EVAL "return #redis.call('keys', 'coindcx_futures:*')" 0

# Check data update frequency
redis-cli MONITOR | grep -E "(bybit_spot|coindcx_futures)"
```

## 🎯 Team Onboarding Checklist

### **For New Team Members**

#### **Developer Setup**
- [ ] Clone repository
- [ ] Install Python dependencies
- [ ] Install and start Redis
- [ ] Run health check script
- [ ] Start crypto monitor launcher
- [ ] Verify data in Redis
- [ ] Review code structure
- [ ] Run individual components

#### **Operations Setup**
- [ ] Set up systemd service (Linux)
- [ ] Configure log rotation
- [ ] Set up monitoring alerts
- [ ] Test backup/restore procedures
- [ ] Document runbook procedures

#### **Data Analyst Setup**
- [ ] Install Redis CLI tools
- [ ] Install data analysis libraries
- [ ] Connect to Redis from Python/R
- [ ] Understand data schema
- [ ] Create sample queries
- [ ] Set up data export scripts

## 🚨 Common Setup Issues

### **"Redis connection refused"**
```bash
# Check if Redis is running
ps aux | grep redis-server

# Start Redis manually
redis-server

# Check Redis configuration
redis-cli CONFIG GET bind
redis-cli CONFIG GET port
```

### **"Permission denied"**
```bash
# Fix file permissions
chmod +x crypto_monitor_launcher.py
chmod +x bybitspotpy/auto_restart.sh

# Fix directory permissions
chmod -R 755 funding_profit_inr/
```

### **"Module not found"**
```bash
# Install missing dependencies
pip install requests redis python-dotenv websockets structlog watchdog

# Check Python path
python -c "import sys; print(sys.path)"

# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **"WebSocket connection failed"**
```bash
# Check internet connectivity
ping google.com

# Check DNS resolution
nslookup stream.bybit.com
nslookup api.coindcx.com

# Check firewall
sudo ufw status
sudo iptables -L
```

### **"No data in Redis"**
```bash
# Check if monitors are actually running
ps aux | grep -E "(coindcx|bybit|main.py)"

# Check monitor logs
tail -f crypto_monitor_launcher.log

# Manually test components
python coindcx_fu_fr.py
python coindcx_fu_ltp_ws_redis.py
cd bybitspotpy && python -m src.main
```

## 🎓 Next Steps

After successful setup:

1. **Review the main documentation**: `CRYPTO_MONITORING_SYSTEM.md`
2. **Understand configuration options**: See configuration guides
3. **Set up monitoring dashboards**: Connect to Redis for visualization
4. **Implement alerting**: Monitor for data gaps or system issues
5. **Scale the system**: Add more exchanges or symbols as needed

---

**🎉 Welcome to the team! Your crypto monitoring system is ready.**