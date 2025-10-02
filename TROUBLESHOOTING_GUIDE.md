# Troubleshooting Guide - Cryptocurrency Monitoring System

This guide helps you diagnose and fix common issues with the cryptocurrency monitoring system.

## 🔍 Quick Diagnostic Commands

**Run these first to identify the issue:**

```bash
# System health check
python health_check.py

# Check if all processes are running
ps aux | grep -E "(coindcx|bybit|main.py|python)" | grep -v grep

# Check Redis connectivity
redis-cli ping

# Check log file
tail -f crypto_monitor_launcher.log

# Check data freshness
redis-cli HGETALL bybit_spot:BTC
redis-cli HGETALL coindcx_futures:BTC
```

## 🚨 Common Issues & Solutions

### **1. "Redis connection refused" / "Redis not responding"**

**Symptoms:**
- Error messages about Redis connection
- No data being stored
- Health check fails

**Solutions:**

```bash
# Check if Redis is running
ps aux | grep redis-server

# If not running, start Redis
redis-server

# On macOS with Homebrew
brew services start redis

# On Ubuntu/Debian
sudo systemctl start redis-server

# Check Redis configuration
redis-cli CONFIG GET "*"

# Test connection manually
redis-cli ping
# Should return: PONG
```

**Alternative Redis setup:**
```bash
# Install Redis if not installed
brew install redis              # macOS
sudo apt install redis-server  # Ubuntu

# Start Redis with custom config
redis-server --port 6379 --bind 127.0.0.1
```

---

### **2. "WebSocket connection failed" / "No price updates"**

**Symptoms:**
- No real-time price data
- WebSocket connection errors
- Repeated reconnection attempts

**Diagnosis:**
```bash
# Check internet connectivity
ping google.com
ping stream.bybit.com

# Check DNS resolution
nslookup stream.bybit.com
nslookup api.coindcx.com

# Test WebSocket manually
curl -I https://stream.bybit.com
```

**Solutions:**

```bash
# Check firewall settings
sudo ufw status                    # Ubuntu
sudo iptables -L                   # Linux
netstat -an | grep -E "(443|80)"   # Check open ports

# Test with different network
# Try mobile hotspot or different WiFi

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Reset network configuration
sudo systemctl restart networking  # Ubuntu
sudo ifconfig en0 down && sudo ifconfig en0 up  # macOS
```

**Configuration fixes:**
```env
# In bybitspotpy/.env - increase timeouts
RECONNECT_INTERVAL_MS=10000
RECONNECT_MAX_ATTEMPTS=20
PING_TIMEOUT=30
```

---

### **3. "Process keeps crashing" / "Automatic restarts"**

**Symptoms:**
- Processes exit unexpectedly
- Frequent restart messages in logs
- Incomplete data collection

**Diagnosis:**
```bash
# Check system resources
free -h                    # Memory usage
df -h                      # Disk space
top                        # CPU usage

# Check for error patterns in logs
grep -i "error\|exception\|crash" crypto_monitor_launcher.log

# Run individual components to see specific errors
python coindcx_fu_fr.py
python coindcx_fu_ltp_ws_redis.py
cd bybitspotpy && python -m src.main
```

**Solutions:**

```bash
# Check Python dependencies
pip list | grep -E "(redis|websockets|requests)"

# Reinstall dependencies
pip install --upgrade redis websockets requests structlog

# Check Python version
python --version  # Should be 3.8+

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

**Memory issues:**
```bash
# Check memory usage of processes
ps aux --sort=-%mem | head -10

# Increase swap space if needed (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### **4. "No funding rate data" / "API timeout errors"**

**Symptoms:**
- Funding rates show as N/A
- API request timeout errors
- CoinDCX funding monitor failing

**Diagnosis:**
```bash
# Test CoinDCX API manually
curl -s "https://public.coindcx.com/market_data/v3/current_prices/futures/rt" | jq .

# Check if specific symbols exist
curl -s "https://public.coindcx.com/market_data/v3/current_prices/futures/rt" | \
  jq '.prices | keys[]' | grep BTC

# Test with single symbol
python -c "
from coindcx_fu_fr import get_coindcx_funding_rate
result = get_coindcx_funding_rate('B-BTC_USDT')
print(result)
"
```

**Solutions:**

```bash
# Check symbol format in config
cat coindcx-symbol-config.json

# Update to correct symbols
nano coindcx-symbol-config.json
# Use format: B-BTC_USDT, not BTC_USDT or BTC-USDT

# Increase API timeout
# Edit coindcx-symbol-config.json
{
  "settings": {
    "api_timeout": 30,  // Increase from 10 to 30 seconds
    "reconnect_delay": 10
  }
}
```

**Rate limiting:**
```python
# Add delays between requests in coindcx_fu_fr.py
import time
time.sleep(1)  # Add 1-second delay between API calls
```

---

### **5. "Module not found" / "Import errors"**

**Symptoms:**
- Python import errors
- "No module named..." errors
- Script fails to start

**Diagnosis:**
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if modules are installed
python -c "import redis; print('Redis OK')"
python -c "import websockets; print('WebSockets OK')"
python -c "import requests; print('Requests OK')"

# Check current working directory
pwd
ls -la
```

**Solutions:**

```bash
# Install missing dependencies
pip install redis websockets requests python-dotenv structlog watchdog

# Use virtual environment
python -m venv crypto_env
source crypto_env/bin/activate  # Linux/macOS
crypto_env\Scripts\activate     # Windows
pip install -r requirements.txt

# Check for CoinDCX futures module
ls -la coindcx-futures/
python -c "
import sys
sys.path.append('coindcx-futures')
from coindcx_futures import CoinDCXFutures
print('CoinDCX module OK')
"

# Fix path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/coindcx-futures"
```

---

### **6. "Data is stale" / "Old timestamps"**

**Symptoms:**
- Price data is outdated
- Timestamps are old
- Real-time updates stopped

**Diagnosis:**
```bash
# Check data freshness
redis-cli HGET bybit_spot:BTC timestamp
redis-cli HGET coindcx_futures:BTC timestamp

# Compare with current time
date -Iseconds

# Check process status
ps aux | grep -E "(coindcx|bybit)" | grep -v grep
```

**Solutions:**

```bash
# Restart specific monitor
pkill -f coindcx_fu_ltp_ws_redis
python coindcx_fu_ltp_ws_redis.py

# Restart Bybit monitor
pkill -f "python -m src.main"
cd bybitspotpy && python -m src.main

# Clear old data from Redis
redis-cli DEL bybit_spot:BTC
redis-cli DEL coindcx_futures:BTC

# Check WebSocket connections
netstat -an | grep -E "(stream.bybit.com|coindcx.com)"
```

---

### **7. "Permission denied" / "File access errors"**

**Symptoms:**
- Cannot write to log files
- Cannot execute scripts
- File permission errors

**Solutions:**

```bash
# Fix script permissions
chmod +x crypto_monitor_launcher.py
chmod +x bybitspotpy/auto_restart.sh

# Fix directory permissions
chmod -R 755 funding_profit_inr/
chmod 644 *.json *.env

# Check file ownership
ls -la crypto_monitor_launcher.py
chown $USER:$USER crypto_monitor_launcher.py

# Fix log file permissions
touch crypto_monitor_launcher.log
chmod 644 crypto_monitor_launcher.log
```

---

### **8. "High CPU usage" / "Performance issues"**

**Symptoms:**
- High CPU usage (>10% per process)
- System slowdown
- Memory leaks

**Diagnosis:**
```bash
# Monitor resource usage
top -p $(pgrep -f crypto_monitor)
htop  # If available

# Check memory usage over time
ps aux --sort=-%mem | grep python

# Monitor network connections
netstat -an | grep -E "(6379|443|80)" | wc -l
```

**Solutions:**

```bash
# Reduce logging verbosity
# Edit bybitspotpy/.env
LOG_LEVEL=warning  # Instead of info or debug

# Increase update intervals
# Edit coindcx-symbol-config.json
{
  "settings": {
    "health_check_interval": 60,  // Instead of 5
    "reconnect_delay": 10         // Instead of 5
  }
}

# Limit symbols being monitored
# Edit configurations to monitor fewer cryptocurrencies

# Restart processes to clear memory leaks
pkill -f crypto_monitor_launcher
python crypto_monitor_launcher.py
```

---

## 🛠️ Advanced Troubleshooting

### **Debug Mode Setup**

Create `debug_monitor.py`:
```python
#!/usr/bin/env python3
import logging
import sys

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Test each component
def test_redis():
    import redis
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✅ Redis: OK")
        return True
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False

def test_coindcx_api():
    import requests
    try:
        response = requests.get(
            "https://public.coindcx.com/market_data/v3/current_prices/futures/rt",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CoinDCX API: {len(data.get('prices', {}))} symbols")
            return True
        else:
            print(f"❌ CoinDCX API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ CoinDCX API: {e}")
        return False

def test_bybit_websocket():
    import asyncio
    import websockets

    async def test_ws():
        try:
            uri = "wss://stream.bybit.com/v5/public/spot"
            async with websockets.connect(uri) as websocket:
                print("✅ Bybit WebSocket: Connected")
                return True
        except Exception as e:
            print(f"❌ Bybit WebSocket: {e}")
            return False

    return asyncio.run(test_ws())

if __name__ == "__main__":
    print("🔍 Debug Mode - Testing Components")
    print("=" * 50)

    results = [
        test_redis(),
        test_coindcx_api(),
        test_bybit_websocket()
    ]

    if all(results):
        print("✅ All components working")
    else:
        print("❌ Some components failed")
        sys.exit(1)
```

Run debug script:
```bash
python debug_monitor.py
```

### **Network Troubleshooting**

```bash
# Monitor network traffic
sudo tcpdump -i any host stream.bybit.com
sudo tcpdump -i any host api.coindcx.com

# Check routing
traceroute stream.bybit.com
mtr stream.bybit.com  # If available

# Test with curl
curl -v wss://stream.bybit.com/v5/public/spot

# Check DNS resolution time
dig stream.bybit.com
nslookup -debug stream.bybit.com
```

### **Database Troubleshooting**

```bash
# Check Redis memory usage
redis-cli INFO memory

# Monitor Redis commands
redis-cli MONITOR

# Check Redis slowlog
redis-cli SLOWLOG GET 10

# Analyze Redis keyspace
redis-cli INFO keyspace

# Check Redis configuration
redis-cli CONFIG GET "*memory*"
redis-cli CONFIG GET "*timeout*"
```

### **Log Analysis**

```bash
# Extract error patterns
grep -i "error\|exception\|failed\|timeout" crypto_monitor_launcher.log

# Count error types
grep -i "error" crypto_monitor_launcher.log | sort | uniq -c

# Monitor logs in real-time
tail -f crypto_monitor_launcher.log | grep -i --color=always "error\|warning"

# Analyze connection patterns
grep "Connected\|Disconnected" crypto_monitor_launcher.log | tail -20
```

## 🔧 Emergency Recovery Procedures

### **Complete System Reset**

```bash
# 1. Stop all processes
pkill -f crypto_monitor_launcher
pkill -f coindcx_fu
pkill -f "python -m src.main"

# 2. Clear Redis data
redis-cli FLUSHDB

# 3. Reset log files
rm crypto_monitor_launcher.log
touch crypto_monitor_launcher.log

# 4. Restart system
python crypto_monitor_launcher.py
```

### **Backup Recovery**

```bash
# Restore configuration from backup
tar -xzf config_backup_YYYYMMDD.tar.gz

# Restart with restored config
python crypto_monitor_launcher.py
```

### **Factory Reset**

```bash
# Reset to default configuration
git checkout HEAD -- coindcx-symbol-config.json
git checkout HEAD -- bybitspotpy/.env
git checkout HEAD -- bybitspotpy/config/coins.json

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Start fresh
python crypto_monitor_launcher.py
```

## 📞 Getting Help

### **Collect Debug Information**

```bash
# Create debug report
cat > debug_report.txt << EOF
=== System Information ===
Date: $(date)
OS: $(uname -a)
Python: $(python --version)
Redis: $(redis-server --version)

=== Process Status ===
$(ps aux | grep -E "(coindcx|bybit|python)" | grep -v grep)

=== Redis Status ===
$(redis-cli ping)
$(redis-cli INFO server | head -5)

=== Network Connectivity ===
$(ping -c 3 google.com)
$(curl -I https://stream.bybit.com)

=== Recent Errors ===
$(tail -50 crypto_monitor_launcher.log | grep -i error)

=== Configuration ===
$(cat coindcx-symbol-config.json)
EOF

echo "Debug report saved to debug_report.txt"
```

### **Support Checklist**

Before contacting support:

- [ ] Run the debug script
- [ ] Check system requirements
- [ ] Review recent log files
- [ ] Test individual components
- [ ] Verify configuration files
- [ ] Document error messages
- [ ] Note when the issue started
- [ ] List any recent changes

### **Common Error Messages**

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `Connection refused` | Redis not running | `redis-server` |
| `Module not found` | Missing dependencies | `pip install -r requirements.txt` |
| `Timeout error` | Network/API issues | Check internet, increase timeouts |
| `Permission denied` | File permissions | `chmod +x script.py` |
| `JSON decode error` | Malformed config | Validate JSON syntax |
| `WebSocket closed` | Connection lost | Wait for auto-reconnect |

---

**🔧 Remember: Most issues are configuration or network related. Start with the basics!**