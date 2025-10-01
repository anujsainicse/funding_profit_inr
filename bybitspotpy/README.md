# Bybit Spot Price Bot - Python Version

A production-ready Python application that fetches real-time cryptocurrency spot prices from Bybit exchange and stores them in Redis.

## Features

- 🚀 Real-time WebSocket connection to Bybit spot market
- 💾 Redis storage for price data with hash structure
- 🔄 Automatic reconnection with exponential backoff
- 📝 Dynamic configuration with hot-reload support
- 📊 Structured logging with structured logs
- 🛡️ Comprehensive error handling
- ⚡ Graceful shutdown handling

## Prerequisites

- Python >= 3.8
- Redis server
- pip or poetry

## Installation

1. Navigate to the Python bot directory:
```bash
cd /Users/xtz/claude/bybitspotpy
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from example:
```bash
cp .env.example .env
```

5. Configure your environment variables in `.env`:
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

# Reconnection Configuration
RECONNECT_INTERVAL_MS=5000
RECONNECT_MAX_ATTEMPTS=10
```

## Configuration

### Adding/Removing Coins

Edit the `config/coins.json` file to add or remove cryptocurrency pairs:

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

**Note:** 
- All coins must be USDT spot trading pairs
- Changes are automatically detected and applied without restart
- Invalid symbols are filtered out with warnings

## Usage

### Starting the Application

```bash
python -m src.main
```

### Alternative ways to run:

```bash
# Direct execution
python src/main.py

# With specific Python version
python3.8 -m src.main

# With auto-restart
./auto_restart.sh
```

### Console Output

The application displays real-time prices in the format:
```
BTC|67250.50|2024-09-09T15:30:25.123Z
ETH|2580.75|2024-09-09T15:30:25.456Z
SOL|142.30|2024-09-09T15:30:25.789Z
```

## Redis Data Structure

### Key Patterns

1. **Hash Format**: `bybit_spot:{COIN}`
   - Example: `bybit_spot:BTC`
   - Fields: 
     - `ltp`: Latest trading price
     - `timestamp`: ISO 8601 timestamp
     - `original_symbol`: Full symbol (e.g., "BTCUSDT")

### Querying Redis Data

Get latest price data:
```bash
redis-cli HGETALL bybit_spot:BTC
```

Get just the price:
```bash
redis-cli HGET bybit_spot:BTC ltp
```

Get multiple coins:
```bash
redis-cli EVAL "return redis.call('HGETALL', 'bybit_spot:BTC')" 0
redis-cli EVAL "return redis.call('HGETALL', 'bybit_spot:ETH')" 0
```

## Project Structure

```
bybitspotpy/
├── src/
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Main application entry point
│   ├── websocket_client.py # Bybit WebSocket client
│   ├── redis_manager.py   # Redis connection manager
│   └── utils.py           # Utility functions and logger
├── config/
│   └── coins.json         # Configurable coin list
├── requirements.txt       # Python dependencies
├── auto_restart.sh        # Auto-restart script
├── .env.example           # Environment variables template
├── .env                   # Environment variables (create from .env.example)
├── .gitignore            # Git ignore file
└── README.md             # Documentation
```

## Python Dependencies

- `websockets` - WebSocket client library
- `redis` - Redis database client
- `python-dotenv` - Environment variable management
- `watchdog` - File system monitoring
- `structlog` - Structured logging

## Architecture

### Components

1. **WebSocket Client** (`websocket_client.py`)
   - Manages Bybit WebSocket connection
   - Handles subscriptions and message parsing
   - Implements reconnection logic with exponential backoff
   - Maintains ping-pong heartbeat

2. **Redis Manager** (`redis_manager.py`)
   - Handles Redis connection and operations
   - Stores latest price data with hash structure (`bybit_spot:{COIN}`)
   - Async Redis operations with connection pooling

3. **Configuration Watcher**
   - Monitors `coins.json` for changes
   - Hot-reloads configuration without restart
   - Validates coin symbols before subscribing

## Error Handling

- **WebSocket Disconnections**: Automatic reconnection with exponential backoff
- **Redis Connection Failures**: Graceful degradation with logging
- **Invalid Data**: Validation and filtering with detailed logging
- **Configuration Errors**: Validation with fallback to last known good config
- **System Signals**: Graceful shutdown on SIGINT, SIGTERM

## Logging

The application uses structured logging with `structlog`:

- **Levels**: error, warn, info, debug
- **Format**: JSON structured logs with timestamps
- **Configuration**: Set `LOG_LEVEL` in `.env`

## Performance Considerations

- **Async Architecture**: Full async/await support for concurrent operations
- **Connection Pooling**: Redis connection pooling for efficiency
- **Memory Management**: Efficient JSON parsing and data handling
- **Graceful Shutdown**: Proper cleanup of resources

## Running in Production

### Using Auto-Restart Script

```bash
./auto_restart.sh
```

This script automatically restarts the bot if it crashes.

### Using systemd (Linux)

Create a service file `/etc/systemd/system/bybit-spot-bot.service`:
```ini
[Unit]
Description=Bybit Spot Price Bot (Python)
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bybitspotpy
ExecStart=/path/to/bybitspotpy/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bybit-spot-bot
sudo systemctl start bybit-spot-bot
```

### Using Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "src.main"]
```

## Troubleshooting

### WebSocket Connection Issues

1. Check network connectivity to Bybit servers
2. Verify WebSocket URL in `.env` (should be spot endpoint)
3. Check logs for specific error messages
4. Ensure firewall allows WebSocket connections

### Redis Connection Issues

1. Verify Redis server is running:
   ```bash
   redis-cli ping
   ```
2. Check Redis configuration in `.env`
3. Verify Redis authentication if password is set
4. Check Redis memory usage and available space

### Python Environment Issues

1. Ensure Python >= 3.8 is installed
2. Verify virtual environment is activated
3. Check all dependencies are installed:
   ```bash
   pip list
   ```
4. Verify import paths are correct

### Missing Price Updates

1. Check if coins are correctly listed in `config/coins.json`
2. Verify coin symbols are valid USDT spot pairs
3. Check WebSocket subscription status via logs
4. Review logs for subscription errors

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when available)
pytest
```

### Code Style

The project follows Python best practices:
- Type hints for better code documentation
- Async/await for concurrent operations
- Structured logging for production monitoring
- Error handling with proper exception types

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Differences from Futures Version

- **Market Type**: Spot market instead of futures
- **WebSocket URL**: `wss://stream.bybit.com/v5/public/spot` instead of linear
- **Redis Keys**: `bybit_spot:{COIN}` instead of `bybit_futures:{COIN}`
- **Coin Validation**: Spot USDT pairs instead of perpetual futures

## Security Considerations

- Never commit `.env` file with sensitive credentials
- Use strong Redis passwords in production
- Consider TLS for Redis connections in production
- Regularly update dependencies for security patches
- Use virtual environments to isolate dependencies

## License

MIT

## Support

For issues, questions, or contributions, please open an issue in the repository.