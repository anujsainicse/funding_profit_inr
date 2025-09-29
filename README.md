# CoinDCX Futures Trading & Monitoring Suite

A comprehensive Python-based trading suite for CoinDCX futures markets with real-time price monitoring and automated trading capabilities.

## 🚀 Features

### Real-Time Price Monitoring (`coindcx_fu_ltp_ws_redis.py`)
- **WebSocket-based live price feeds** for futures markets
- **Automatic reconnection** with intelligent retry logic
- **Multi-symbol monitoring** with support for both USDT and INR pairs
- **Real-time price updates** every 10 seconds
- **Connection health monitoring** with status indicators
- **Formatted price display** with appropriate decimal precision

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

## 🔧 Usage

### Real-Time Price Monitoring

Run the WebSocket price monitor:

```bash
python coindcx_fu_ltp_ws_redis.py
```

**Sample Output:**
```
==================================================
FUTURES LTP 🟢 - 14:30:25
Status: Connected (Live)
==================================================
B-BTC_USDT     : $43,245.50
B-ETH_USDT     : $2,587.32
B-SOL_USDT     : $98.45
B-BNB_USDT     : $312.67
B-DOGE_USDT    : $0.0823
==================================================
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

### Price Monitor (`coindcx_fu_ltp_ws_redis.py`)
- Main monitoring application
- Price formatting and display
- Real-time updates with connection status
- Graceful error handling and reconnection

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

## 🚨 Important Notes

⚠️ **Security Warning**: Never commit your `.env` file to version control. It contains sensitive API credentials.

⚠️ **Trading Risk**: This software is for educational and development purposes. Always test with small amounts and understand the risks involved in cryptocurrency trading.

⚠️ **API Limits**: Be aware of CoinDCX API rate limits and adjust your usage accordingly.

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