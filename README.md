# CoinDCX Futures Trading & Monitoring Suite

A comprehensive Python-based trading suite for CoinDCX futures markets with **real-time price monitoring**, **Redis data storage**, and automated trading capabilities.

## 🚀 Features

### Real-Time Price Monitoring with Redis Storage (`coindcx_fu_ltp_ws_redis.py`)
- **WebSocket-based live price feeds** for futures markets
- **Redis database integration** for real-time LTP storage
- **Automatic reconnection** with intelligent retry logic
- **Multi-symbol monitoring** with support for both USDT and INR pairs
- **Instant data persistence** - prices saved to Redis immediately on arrival
- **Connection health monitoring** with status indicators
- **Structured data format** with ticker, price, and timestamp
- **Automatic data cleanup** with configurable TTL (Time To Live)

### Trading Engine (`SF_INR_Trading_Engine.py`)
- **Spot-Futures arbitrage** trading framework
- **Multi-exchange support** for spot and futures
- **Risk management** with spread monitoring
- **Position sizing** based on USD quantities
- **Trade monitoring** with profit/loss tracking

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- CoinDCX account with API access
- Active internet connection for WebSocket feeds
- **Redis server** for data storage (local or remote)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/funding_profit_inr.git
   cd funding_profit_inr
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API credentials**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` file and add your CoinDCX API credentials:
   ```
   COINDCX_API_KEY=your_actual_api_key
   COINDCX_API_SECRET=your_actual_api_secret
   ```

4. **Get CoinDCX API Credentials**
   - Visit [CoinDCX API Management](https://coindcx.com/trade/api)
   - Create a new API key with futures trading permissions
   - Copy the API key and secret to your `.env` file

5. **Install and Setup Redis**

   **Option A: Local Redis Installation**
   ```bash
   # macOS (using Homebrew)
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt update
   sudo apt install redis-server
   sudo systemctl start redis-server

   # Windows (using WSL or Docker)
   docker run -d -p 6379:6379 redis:latest
   ```

   **Option B: Redis Cloud/Remote**
   - Update Redis connection settings in `coindcx_fu_ltp_ws_redis.py`
   - Modify the `redis.Redis()` configuration with your remote details

## 🔧 Usage

### Real-Time Price Monitoring with Redis Storage

**1. Start Redis server** (if not running):
```bash
redis-server
```

**2. Run the WebSocket price monitor**:
```bash
python coindcx_fu_ltp_ws_redis.py
```

**3. Sample Console Output:**
```
[14:30:25] ✅ Redis connected successfully!
[14:30:26] ✅ WebSocket connected successfully!
[14:30:26] Subscribed to B-BTC_USDT
[14:30:26] Subscribed to B-ETH_USDT
[14:30:26] Subscribed to B-SOL_USDT

Monitoring 5 futures tokens...
LTP data is being saved to Redis in real-time. Minimal console output. Press Ctrl+C to stop.

[14:31:25] 🟢 Connected - 5/5 symbols active - Data saving to Redis
```

**4. Check stored data in Redis**:
```bash
# Connect to Redis CLI
redis-cli

# List all futures data keys
127.0.0.1:6379> keys coindcx_futures:*
1) "coindcx_futures:BTC"
2) "coindcx_futures:ETH"
3) "coindcx_futures:SOL"
4) "coindcx_futures:BNB"
5) "coindcx_futures:DOGE"

# Get specific coin's complete data
127.0.0.1:6379> hgetall coindcx_futures:BTC
1) "ltp"
2) "43245.50"
3) "timestamp"
4) "2024-09-29T14:30:25.123456"
5) "original_symbol"
6) "B-BTC_USDT"

# Get only the price for a specific coin
127.0.0.1:6379> hget coindcx_futures:ETH ltp
"2587.32"
```

### Customizing Monitored Symbols

Edit the `coins_to_monitor` list in `coindcx_fu_ltp_ws_redis.py`:

```python
coins_to_monitor = [
    'B-BTC_USDT',    # Bitcoin futures
    'B-ETH_USDT',    # Ethereum futures
    'B-SOL_USDT',    # Solana futures
    'B-BNB_USDT',    # Binance Coin futures
    'B-DOGE_USDT',   # Dogecoin futures
    # Add more symbols as needed
]
```

### Trading Engine

The trading engine provides a framework for automated trading strategies:

```python
from SF_INR_Trading_Engine import main

# Execute a trading strategy
main(
    symbol="BTC_USDT",
    spot_exchange="coinbase",
    futures_exchange="coindcx",
    quantity_usd=1000,
    take_profit=0.02  # 2% profit target
)
```

## 📊 Supported Markets

### Futures Symbols Format
- **USDT pairs**: `B-{COIN}_USDT` (e.g., `B-BTC_USDT`)
- **INR pairs**: `B-{COIN}_INR` (e.g., `B-BTC_INR`)

### Popular Symbols
- `B-BTC_USDT` - Bitcoin
- `B-ETH_USDT` - Ethereum
- `B-SOL_USDT` - Solana
- `B-BNB_USDT` - Binance Coin
- `B-DOGE_USDT` - Dogecoin
- `B-ADA_USDT` - Cardano
- `B-DOT_USDT` - Polkadot

## 💾 Redis Data Structure

### Data Storage Format
The application stores Last Traded Price (LTP) data in Redis using hash structures:

**Redis Hash Key Pattern**: `coindcx_futures:{COIN}`
- Example: `coindcx_futures:BTC`, `coindcx_futures:ETH`, `coindcx_futures:SOL`

**Hash Fields Structure**:
| Field | Description | Example |
|-------|-------------|---------|
| `ltp` | Latest traded price | `43245.50` |
| `timestamp` | ISO formatted timestamp | `2024-09-29T14:30:25.123456` |
| `original_symbol` | Full CoinDCX symbol | `B-BTC_USDT` |

### Key Features
- **Real-time updates**: Data saved instantly when price changes occur
- **Hash structure**: Efficient field-based storage for multiple data points
- **ISO timestamps**: Precise timing for each price update
- **Original symbol tracking**: Preserves full CoinDCX symbol format
- **Auto-cleanup**: 1-hour TTL (Time To Live) prevents memory buildup
- **High-performance**: Redis hash operations provide optimal performance

### Redis Commands for Data Access

**List all active coins**:
```bash
redis-cli keys "coindcx_futures:*"
```

**Get all data for specific coin**:
```bash
redis-cli hgetall "coindcx_futures:BTC"
```

**Get only LTP for specific coin**:
```bash
redis-cli hget "coindcx_futures:ETH" "ltp"
```

**Get timestamp for specific coin**:
```bash
redis-cli hget "coindcx_futures:BTC" "timestamp"
```

**Monitor real-time updates**:
```bash
redis-cli monitor
```

**Check key expiration time**:
```bash
redis-cli ttl "coindcx_futures:BTC"
```

### Integration Examples

**Python - Read from Redis**:
```python
import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Get latest BTC data
btc_data = r.hgetall('coindcx_futures:BTC')
print(f"BTC Price: ${btc_data['ltp']} at {btc_data['timestamp']}")
print(f"Original Symbol: {btc_data['original_symbol']}")

# Get only LTP for ETH
eth_price = r.hget('coindcx_futures:ETH', 'ltp')
print(f"ETH Price: ${eth_price}")

# Get all active coins and their prices
for key in r.keys('coindcx_futures:*'):
    coin = key.split(':')[1]  # Extract coin name (BTC, ETH, etc.)
    price = r.hget(key, 'ltp')
    timestamp = r.hget(key, 'timestamp')
    print(f"{coin}: ${price} ({timestamp})")
```

**Node.js - Read from Redis**:
```javascript
const redis = require('redis');
const client = redis.createClient();

// Get latest ETH data
const ethData = await client.hGetAll('coindcx_futures:ETH');
console.log(`ETH Price: $${ethData.ltp} at ${ethData.timestamp}`);

// Get only BTC price
const btcPrice = await client.hGet('coindcx_futures:BTC', 'ltp');
console.log(`BTC Price: $${btcPrice}`);
```

## 🔐 Security Features

- **Environment-based configuration** - API keys stored in `.env` file
- **Gitignore protection** - Sensitive files excluded from version control
- **Example configuration** - Template provided for easy setup
- **Error handling** - Comprehensive exception management

## 🛠️ Architecture

### WebSocket Client (`coindcx-futures/`)
- Real-time WebSocket connection to CoinDCX
- Event-driven architecture with callbacks
- Automatic subscription management
- Connection health monitoring

### Price Monitor with Redis Integration (`coindcx_fu_ltp_ws_redis.py`)
- Main monitoring application with database storage
- Real-time data persistence to Redis
- WebSocket event handling and price processing
- Connection health monitoring for both WebSocket and Redis
- Graceful error handling and automatic reconnection
- Structured JSON data format for easy integration

### Trading Framework (`SF_INR_Trading_Engine.py`)
- Modular trading system
- Integration with multiple components:
  - `sf_order_router` - Order management
  - `sf_get_prices` - Price fetching
  - `sf_monitoring` - Trade monitoring

## 🔄 Connection Management

The WebSocket client includes robust connection management:

- **Automatic reconnection** on connection loss
- **Health monitoring** with data timeout detection
- **Graceful degradation** when connection fails
- **Status indicators** for connection state
- **Retry logic** with exponential backoff

## 📈 Monitoring Features

- **Real-time price updates** every 10 seconds
- **Connection status indicators** (🟢 Connected / 🔴 Disconnected)
- **Last data timestamp** tracking
- **Formatted price display** with currency symbols
- **Multi-decimal precision** based on price ranges

## 🛠️ Troubleshooting

### Redis Connection Issues

**Problem**: `Redis connection failed - running without Redis storage`
**Solutions**:
1. **Check if Redis is running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Start Redis server**:
   ```bash
   # macOS
   brew services start redis

   # Linux
   sudo systemctl start redis-server

   # Manual start
   redis-server
   ```

3. **Check Redis configuration**:
   - Verify host/port settings in the Python script
   - Default: `localhost:6379`
   - Check if Redis is bound to correct interface

**Problem**: `ModuleNotFoundError: No module named 'redis'`
**Solution**:
```bash
pip install redis>=4.5.0
```

**Problem**: Redis data not persisting
**Solutions**:
1. **Check TTL settings**: Keys expire after 1 hour by default
2. **Verify Redis persistence**: Check `redis.conf` for save settings
3. **Monitor Redis memory**: Use `redis-cli info memory`

### WebSocket Connection Issues

**Problem**: WebSocket connection fails
**Solutions**:
1. Check internet connection
2. Verify CoinDCX API credentials in `.env` file
3. Check if API has futures trading permissions

**Problem**: No price updates received
**Solutions**:
1. Verify symbol names match CoinDCX format (`B-{COIN}_USDT`)
2. Check if symbols are actively traded
3. Monitor WebSocket connection status

### Performance Optimization

**High Memory Usage**:
- Reduce number of monitored symbols
- Adjust Redis TTL settings
- Monitor with: `redis-cli info memory`

**Slow Redis Operations**:
- Use Redis pipelining for bulk operations
- Consider Redis clustering for high load
- Monitor with: `redis-cli --latency`

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Redis server not running | Start Redis server |
| `Authentication failed` | Wrong Redis password | Check Redis auth settings |
| `READONLY` | Redis in slave mode | Connect to master Redis instance |
| `OOM` | Redis out of memory | Increase memory or reduce TTL |

## 🚨 Important Notes

⚠️ **Security Warning**: Never commit your `.env` file to version control. It contains sensitive API credentials.

⚠️ **Trading Risk**: This software is for educational and development purposes. Always test with small amounts and understand the risks involved in cryptocurrency trading.

⚠️ **API Limits**: Be aware of CoinDCX API rate limits and adjust your usage accordingly.

⚠️ **Redis Security**: In production, secure Redis with authentication and network restrictions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/funding_profit_inr/issues) page
2. Create a new issue with detailed information
3. Include error logs and system information

## 🔗 Related Links

- [CoinDCX Futures API Documentation](https://docs.coindcx.com/)
- [CoinDCX API Management](https://coindcx.com/trade/api)
- [WebSocket Documentation](https://docs.coindcx.com/websocket)

---

**Disclaimer**: This software is provided "as is" without warranty. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this software.