# LTP Fetch Documentation

## Overview

The `LTP_fetch.py` module provides a comprehensive solution to retrieve cryptocurrency data from both Bybit and CoinDCX exchanges. It fetches Last Traded Prices (LTP), timestamps, and funding rate information in a structured format, designed for seamless integration with other applications.

## Features

- **Multi-Symbol Support**: Fetch data for any cryptocurrency symbol
- **Comprehensive Data Retrieval**:
  - **Bybit**: LTP and timestamp
  - **CoinDCX**: LTP, timestamp, current funding rate, estimated funding rate, and funding timestamp
- **Dual Exchange Integration**: Retrieves data from both Bybit and CoinDCX simultaneously
- **Price Analysis**: Automatic calculation of price differences and percentages
- **Funding Rate Monitoring**: Access to current and estimated funding rates for CoinDCX
- **Batch Processing**: Handle multiple cryptocurrencies in a single call
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Import-Friendly**: Functions return structured data instead of printing, perfect for use in other modules

## Installation & Dependencies

### Prerequisites
- Python 3.6+
- Redis server running with crypto data
- `crypto_data_retriever.py` module in the same directory

### Required Python Packages
```bash
pip install redis
```

## Quick Start

### Basic Usage

```python
from LTP_fetch import get_crypto_ltp

# Get comprehensive ETH data
eth_data = get_crypto_ltp('ETH')

if eth_data['success']:
    # Bybit data
    bybit_ltp = eth_data['bybit_data']['ltp']
    bybit_timestamp = eth_data['bybit_data']['timestamp']

    # CoinDCX data
    coindcx_ltp = eth_data['coindcx_data']['ltp']
    coindcx_timestamp = eth_data['coindcx_data']['timestamp']
    current_funding = eth_data['coindcx_data']['current_funding_rate']
    estimated_funding = eth_data['coindcx_data']['estimated_funding_rate']
    funding_timestamp = eth_data['coindcx_data']['funding_timestamp']

    print(f"ETH - Bybit: {bybit_ltp} at {bybit_timestamp}")
    print(f"ETH - CoinDCX: {coindcx_ltp} at {coindcx_timestamp}")
    print(f"Current Funding Rate: {current_funding}")
else:
    print(f"Error: {eth_data['error']}")
```

## API Reference

### Core Functions

#### `get_crypto_ltp(symbol)`

Retrieves comprehensive cryptocurrency data for a single symbol including LTP, timestamps, and funding rates.

**Parameters:**
- `symbol` (str): Cryptocurrency symbol (e.g., 'ETH', 'BTC', 'SOL')

**Returns:**
```python
{
    'symbol': 'ETH',
    'timestamp': '2024-01-01T12:00:00.000000',
    'bybit_data': {
        'ltp': '2500.50',                    # Last Traded Price
        'timestamp': '2024-01-01T12:00:00'   # Price timestamp
    },
    'coindcx_data': {
        'ltp': '2498.30',                    # Last Traded Price
        'timestamp': '2024-01-01T12:00:05',  # Price timestamp
        'current_funding_rate': '0.0001',    # Current funding rate
        'estimated_funding_rate': '0.00015', # Estimated funding rate
        'funding_timestamp': '2024-01-01T12:00:00' # Funding timestamp
    },
    'success': True
}
```

**Error Response:**
```python
{
    'symbol': 'ETH',
    'success': False,
    'error': 'Error message here',
    'bybit_data': None,
    'coindcx_data': None
}
```

#### `get_crypto_ltp_formatted(symbol)`

Retrieves comprehensive cryptocurrency data with additional price analysis between exchanges.

**Parameters:**
- `symbol` (str): Cryptocurrency symbol

**Returns:**
Same as `get_crypto_ltp()` plus:
```python
{
    # ... all basic data (bybit_data, coindcx_data) ...
    'price_analysis': {
        'price_difference': 2.20,          # Absolute price difference
        'percentage_difference': 0.09,     # Percentage difference
        'higher_exchange': 'bybit',        # Which exchange has higher price
        'difference_amount': 2.20          # Amount of difference
    }
}
```

**Price Analysis Error Response:**
```python
{
    # ... basic data ...
    'price_analysis': {
        'error': 'Insufficient data for price analysis'
    }
}
```

#### `get_multiple_crypto_ltp(symbols)`

Retrieves comprehensive cryptocurrency data for multiple symbols.

**Parameters:**
- `symbols` (list): List of cryptocurrency symbols

**Returns:**
```python
{
    'BTC': {
        'symbol': 'BTC',
        'bybit_data': { 'ltp': '...', 'timestamp': '...' },
        'coindcx_data': {
            'ltp': '...',
            'timestamp': '...',
            'current_funding_rate': '...',
            'estimated_funding_rate': '...',
            'funding_timestamp': '...'
        },
        'success': True
    },
    'ETH': {
        'symbol': 'ETH',
        'bybit_data': { ... },
        'coindcx_data': { ... },
        'success': True
    }
}
```

#### `get_multiple_crypto_ltp_formatted(symbols)`

Retrieves comprehensive cryptocurrency data with price analysis for multiple symbols.

**Parameters:**
- `symbols` (list): List of cryptocurrency symbols

**Returns:**
Same structure as `get_multiple_crypto_ltp()` but each symbol includes price analysis.

### Display Functions (Optional)

#### `print_crypto_ltp(symbol)`

Prints comprehensive formatted cryptocurrency data to console, including all timestamps and funding rates. Use only for display purposes.

#### `print_multiple_crypto_ltp(symbols)`

Prints comprehensive formatted cryptocurrency data for multiple symbols to console.

## Usage Examples

### Example 1: Single Cryptocurrency with Comprehensive Data

```python
from LTP_fetch import get_crypto_ltp_formatted

# Get ETH data with analysis
data = get_crypto_ltp_formatted('ETH')

if data['success']:
    print(f"Symbol: {data['symbol']}")

    # Bybit data
    if data['bybit_data']:
        print(f"Bybit LTP: {data['bybit_data']['ltp']} USDT")
        print(f"Bybit Timestamp: {data['bybit_data']['timestamp']}")

    # CoinDCX comprehensive data
    if data['coindcx_data']:
        print(f"CoinDCX LTP: {data['coindcx_data']['ltp']} USDT")
        print(f"CoinDCX Timestamp: {data['coindcx_data']['timestamp']}")
        print(f"Current Funding Rate: {data['coindcx_data']['current_funding_rate']}")
        print(f"Estimated Funding Rate: {data['coindcx_data']['estimated_funding_rate']}")
        print(f"Funding Timestamp: {data['coindcx_data']['funding_timestamp']}")

    # Price analysis
    if 'error' not in data['price_analysis']:
        analysis = data['price_analysis']
        print(f"Price Difference: {analysis['price_difference']} USDT")
        print(f"Higher Exchange: {analysis['higher_exchange']}")
```

### Example 2: Multiple Cryptocurrencies with Full Data

```python
from LTP_fetch import get_multiple_crypto_ltp_formatted

symbols = ['BTC', 'ETH', 'SOL', 'BNB']
data = get_multiple_crypto_ltp_formatted(symbols)

for symbol, info in data.items():
    if info['success']:
        print(f"\n{symbol}:")

        # Bybit data
        if info['bybit_data']:
            print(f"  Bybit: {info['bybit_data']['ltp']} USDT at {info['bybit_data']['timestamp']}")

        # CoinDCX data
        if info['coindcx_data']:
            print(f"  CoinDCX: {info['coindcx_data']['ltp']} USDT at {info['coindcx_data']['timestamp']}")
            if info['coindcx_data']['current_funding_rate']:
                print(f"  Current Funding: {info['coindcx_data']['current_funding_rate']}")
            if info['coindcx_data']['estimated_funding_rate']:
                print(f"  Estimated Funding: {info['coindcx_data']['estimated_funding_rate']}")
    else:
        print(f"{symbol}: Error - {info['error']}")
```

### Example 3: Funding Rate Monitoring

```python
from LTP_fetch import get_crypto_ltp

def monitor_funding_rates(symbols):
    """Monitor funding rates for given symbols"""
    results = []

    for symbol in symbols:
        data = get_crypto_ltp(symbol)

        if data['success'] and data['coindcx_data']:
            coindcx = data['coindcx_data']
            if coindcx['current_funding_rate'] or coindcx['estimated_funding_rate']:
                results.append({
                    'symbol': symbol,
                    'ltp': coindcx['ltp'],
                    'current_funding': coindcx['current_funding_rate'],
                    'estimated_funding': coindcx['estimated_funding_rate'],
                    'funding_timestamp': coindcx['funding_timestamp']
                })

    return results

# Usage
symbols = ['BTC', 'ETH', 'SOL', 'BNB']
funding_data = monitor_funding_rates(symbols)

for item in funding_data:
    print(f"{item['symbol']}:")
    print(f"  LTP: {item['ltp']}")
    print(f"  Current Funding: {item['current_funding']}")
    print(f"  Estimated Funding: {item['estimated_funding']}")
    print(f"  Timestamp: {item['funding_timestamp']}\n")
```

### Example 4: Price Arbitrage Detection

```python
from LTP_fetch import get_multiple_crypto_ltp_formatted

def find_arbitrage_opportunities(symbols, min_percentage=1.0):
    """Find arbitrage opportunities above minimum percentage"""
    data = get_multiple_crypto_ltp_formatted(symbols)
    opportunities = []

    for symbol, info in data.items():
        if info['success'] and 'error' not in info['price_analysis']:
            analysis = info['price_analysis']
            if analysis['percentage_difference'] >= min_percentage:
                opportunities.append({
                    'symbol': symbol,
                    'percentage_diff': analysis['percentage_difference'],
                    'higher_exchange': analysis['higher_exchange'],
                    'difference': analysis['price_difference'],
                    'bybit_ltp': info['bybit_data']['ltp'],
                    'coindcx_ltp': info['coindcx_data']['ltp']
                })

    return opportunities

# Usage
symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE']
opportunities = find_arbitrage_opportunities(symbols, min_percentage=0.5)

for opp in opportunities:
    print(f"{opp['symbol']}: {opp['percentage_diff']}% difference")
    print(f"  Bybit: {opp['bybit_ltp']}, CoinDCX: {opp['coindcx_ltp']}")
```

### Example 5: Integration with Trading Bot

```python
from LTP_fetch import get_crypto_ltp
import time

class CryptoMonitor:
    def __init__(self, symbols, check_interval=30):
        self.symbols = symbols
        self.check_interval = check_interval
        self.last_data = {}

    def monitor(self):
        """Monitor price and funding rate changes"""
        while True:
            for symbol in self.symbols:
                data = get_crypto_ltp(symbol)

                if data['success']:
                    if symbol in self.last_data:
                        # Check for changes
                        self.check_changes(symbol, data)

                    self.last_data[symbol] = data

            time.sleep(self.check_interval)

    def check_changes(self, symbol, current_data):
        """Check for significant changes in price or funding rates"""
        last_data = self.last_data[symbol]

        # Check Bybit price changes
        if (current_data['bybit_data'] and last_data['bybit_data'] and
            current_data['bybit_data']['ltp'] != last_data['bybit_data']['ltp']):
            print(f"{symbol} Bybit price changed: "
                  f"{last_data['bybit_data']['ltp']} -> {current_data['bybit_data']['ltp']}")

        # Check CoinDCX price changes
        if (current_data['coindcx_data'] and last_data['coindcx_data'] and
            current_data['coindcx_data']['ltp'] != last_data['coindcx_data']['ltp']):
            print(f"{symbol} CoinDCX price changed: "
                  f"{last_data['coindcx_data']['ltp']} -> {current_data['coindcx_data']['ltp']}")

        # Check funding rate changes
        if (current_data['coindcx_data'] and last_data['coindcx_data'] and
            current_data['coindcx_data']['current_funding_rate'] !=
            last_data['coindcx_data']['current_funding_rate']):
            print(f"{symbol} funding rate changed: "
                  f"{last_data['coindcx_data']['current_funding_rate']} -> "
                  f"{current_data['coindcx_data']['current_funding_rate']}")

# Usage
monitor = CryptoMonitor(['BTC', 'ETH'])
# monitor.monitor()  # Uncomment to start monitoring
```

## Error Handling

The module provides comprehensive error handling:

### Common Error Types

1. **Redis Connection Error**: When Redis server is unavailable
2. **Symbol Not Found**: When cryptocurrency symbol doesn't exist in database
3. **Data Format Error**: When stored data format is unexpected
4. **Network Error**: When connection to exchanges fails

### Error Response Format

```python
{
    'symbol': 'INVALID',
    'success': False,
    'error': 'Detailed error message',
    'ltp_data': None
}
```

### Best Practices for Error Handling

```python
from LTP_fetch import get_crypto_ltp

def safe_get_price(symbol):
    """Safely get crypto price with error handling"""
    try:
        data = get_crypto_ltp(symbol)

        if data['success']:
            return data['ltp_data']
        else:
            print(f"Failed to get {symbol} data: {data['error']}")
            return None

    except Exception as e:
        print(f"Unexpected error getting {symbol} data: {e}")
        return None

# Usage
price_data = safe_get_price('ETH')
if price_data:
    print(f"ETH prices: {price_data}")
```

## Data Format Details

### Complete Data Structure

The module returns comprehensive data for both exchanges:

#### Bybit Data Structure
```python
'bybit_data': {
    'ltp': '2500.50',                    # Last Traded Price (string/numeric)
    'timestamp': '2024-01-01T12:00:00'   # Price timestamp (ISO format)
}
```

#### CoinDCX Data Structure
```python
'coindcx_data': {
    'ltp': '2498.30',                    # Last Traded Price (string/numeric)
    'timestamp': '2024-01-01T12:00:05',  # Price timestamp (ISO format)
    'current_funding_rate': '0.0001',    # Current funding rate (string/numeric)
    'estimated_funding_rate': '0.00015', # Estimated funding rate (string/numeric)
    'funding_timestamp': '2024-01-01T12:00:00' # Funding rate timestamp (ISO format)
}
```

**Note**: All price and funding rate values can be returned as strings, numbers, or complex objects depending on the source data format. Timestamps are typically in ISO format.

### Price Analysis Structure

```python
'price_analysis': {
    'price_difference': 2.20,          # Always numeric (float)
    'percentage_difference': 0.09,     # Always numeric (float)
    'higher_exchange': 'bybit',        # 'bybit', 'coindcx', or 'equal'
    'difference_amount': 2.20          # Same as price_difference
}
```

## Funding Rate Features

The module provides comprehensive funding rate monitoring capabilities for CoinDCX:

### Available Funding Rate Data

- **Current Funding Rate**: The currently active funding rate
- **Estimated Funding Rate**: Predicted next funding rate
- **Funding Timestamp**: When the funding rate was last updated

### Funding Rate Use Cases

1. **Arbitrage Opportunities**: Compare funding rates between exchanges
2. **Cost Calculation**: Calculate holding costs for positions
3. **Market Sentiment**: Analyze funding rate trends
4. **Risk Management**: Monitor funding rate changes for position sizing

### Example: Funding Rate Analysis

```python
from LTP_fetch import get_crypto_ltp

def analyze_funding_rates(symbols):
    """Analyze funding rates across symbols"""
    analysis = []

    for symbol in symbols:
        data = get_crypto_ltp(symbol)

        if data['success'] and data['coindcx_data']:
            coindcx = data['coindcx_data']
            if coindcx['current_funding_rate']:
                try:
                    current_rate = float(coindcx['current_funding_rate'])
                    estimated_rate = float(coindcx['estimated_funding_rate']) if coindcx['estimated_funding_rate'] else None

                    analysis.append({
                        'symbol': symbol,
                        'current_funding_rate': current_rate,
                        'estimated_funding_rate': estimated_rate,
                        'rate_trend': 'increasing' if estimated_rate and estimated_rate > current_rate else 'decreasing' if estimated_rate and estimated_rate < current_rate else 'stable'
                    })
                except (ValueError, TypeError):
                    pass

    return analysis

# Usage
symbols = ['BTC', 'ETH', 'SOL']
funding_analysis = analyze_funding_rates(symbols)

for item in funding_analysis:
    print(f"{item['symbol']}: {item['current_funding_rate']:.4f} ({item['rate_trend']})")
```

## Performance Considerations

- **Redis Connection**: Each function call creates a new Redis connection. For high-frequency usage, consider modifying to use connection pooling.
- **Batch Processing**: Use `get_multiple_crypto_ltp()` for multiple symbols to reduce overhead.
- **Caching**: Consider implementing caching for frequently accessed data.
- **Funding Rate Updates**: Funding rates typically update less frequently than prices, consider different refresh intervals.

## Troubleshooting

### Common Issues

1. **"Failed to connect to Redis"**
   - Ensure Redis server is running
   - Check Redis host/port configuration
   - Verify Redis database contains crypto data

2. **"No data available"**
   - Symbol might not be monitored by the data collectors
   - Check if symbol exists in Redis database
   - Verify data collectors are running

3. **"Could not calculate price difference"**
   - Price data might be in unexpected format
   - One or both exchanges might not have data for the symbol

4. **"Missing funding rate data"**
   - Funding rates might not be available for all symbols
   - CoinDCX data might not include funding information
   - Check if the symbol supports futures trading

5. **"Timestamp format issues"**
   - Timestamp formats might vary between exchanges
   - Some timestamps might be missing or invalid

### Debug Mode

To enable debug information, modify the Redis connection in `crypto_data_retriever.py`:

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration Examples

### Flask Web API

```python
from flask import Flask, jsonify
from LTP_fetch import get_crypto_ltp_formatted

app = Flask(__name__)

@app.route('/api/crypto/<symbol>')
def get_crypto_api(symbol):
    data = get_crypto_ltp_formatted(symbol)
    return jsonify(data)

@app.route('/api/crypto/multiple/<symbols>')
def get_multiple_crypto_api(symbols):
    symbol_list = symbols.split(',')
    data = get_multiple_crypto_ltp_formatted(symbol_list)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
```

### Telegram Bot Integration

```python
from LTP_fetch import get_crypto_ltp_formatted

def handle_price_command(symbol):
    """Handle /price <symbol> command"""
    data = get_crypto_ltp_formatted(symbol.upper())

    if data['success']:
        message = f"💰 {data['symbol']} Prices:\n"
        message += f"🟡 Bybit: {data['ltp_data']['bybit']} USDT\n"
        message += f"🔵 CoinDCX: {data['ltp_data']['coindcx']} USDT\n"

        if 'error' not in data['price_analysis']:
            analysis = data['price_analysis']
            message += f"\n📊 Analysis:\n"
            message += f"📈 Difference: {analysis['percentage_difference']}%\n"
            message += f"🏆 Higher: {analysis['higher_exchange'].title()}"

        return message
    else:
        return f"❌ Error getting {symbol} data: {data['error']}"
```

## License

This module is part of the crypto monitoring system. Please ensure you have proper authorization to access the Redis database containing cryptocurrency data.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify Redis connectivity
3. Ensure all dependencies are installed
4. Check that the crypto data collectors are running and populating Redis