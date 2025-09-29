#!/usr/bin/env python3
"""
fetchLTP.py - Retrieve LTP and funding rate data for CoinDCX futures from Redis

Usage:
    python fetchLTP.py BTC                    # Single ticker
    python fetchLTP.py BTC ETH DOGE          # Multiple tickers
    python fetchLTP.py                       # Interactive mode
"""

import redis
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List


def setup_redis_connection() -> Optional[redis.Redis]:
    """
    Setup Redis connection with error handling.

    Returns:
        redis.Redis: Redis client instance or None if connection fails
    """
    try:
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test Redis connection
        redis_client.ping()
        return redis_client
    except redis.ConnectionError:
        print("❌ Redis connection failed - make sure Redis server is running")
        return None
    except Exception as e:
        print(f"❌ Redis setup error: {e}")
        return None


def format_percentage(value: Optional[str]) -> Optional[float]:
    """
    Convert string funding rate to percentage.

    Args:
        value: String representation of funding rate

    Returns:
        float: Funding rate as percentage or None
    """
    if not value:
        return None
    try:
        return float(value) * 100
    except (ValueError, TypeError):
        return None


def format_timestamp(timestamp_str: Optional[str]) -> Optional[str]:
    """
    Format ISO timestamp string to readable format.

    Args:
        timestamp_str: ISO timestamp string

    Returns:
        str: Formatted timestamp or None
    """
    if not timestamp_str:
        return None
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def calculate_age_minutes(timestamp_str: Optional[str]) -> Optional[float]:
    """
    Calculate age of data in minutes.

    Args:
        timestamp_str: ISO timestamp string

    Returns:
        float: Age in minutes or None
    """
    if not timestamp_str:
        return None
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        age = datetime.now() - dt
        return round(age.total_seconds() / 60, 1)
    except (ValueError, TypeError):
        return None


def fetch_ticker_data(ticker: str, redis_client: Optional[redis.Redis] = None) -> Optional[List]:
    """
    Fetch all available data for a given ticker from Redis.

    Args:
        ticker: Ticker symbol (e.g., "BTC", "ETH", "DOGE")
        redis_client: Redis client instance (optional, will create if None)

    Returns:
        List or None: List with ticker data in the following order:
        [
            ticker,                    # 0: Ticker symbol (str)
            ltp,                       # 1: Last Traded Price (float)
            original_symbol,           # 2: Original symbol (str)
            current_funding_rate,      # 3: Current funding rate % (float)
            estimated_funding_rate,    # 4: Estimated funding rate % (float)
            ltp_timestamp,             # 5: LTP timestamp (str)
            funding_timestamp,         # 6: Funding timestamp (str)
            ltp_age_minutes,           # 7: LTP age in minutes (float)
            funding_age_minutes        # 8: Funding age in minutes (float)
        ]
        Returns None if ticker not found or error occurs.
    """
    # Setup Redis connection if not provided
    if redis_client is None:
        redis_client = setup_redis_connection()

    if redis_client is None:
        return None  # Return None if Redis connection failed

    ticker = ticker.upper()
    redis_key = f"coindcx_futures:{ticker}"

    try:
        # Get all hash fields for the ticker
        raw_data = redis_client.hgetall(redis_key)

        if not raw_data:
            return None  # Return None if ticker not found

        # Process and format the data
        processed_data = {
            "ltp": None,
            "ltp_timestamp": None,
            "original_symbol": None,
            "current_funding_rate": None,
            "estimated_funding_rate": None,
            "funding_timestamp": None,
            "ltp_age_minutes": None,
            "funding_age_minutes": None
        }

        # Process LTP data
        if "ltp" in raw_data:
            try:
                processed_data["ltp"] = float(raw_data["ltp"])
            except (ValueError, TypeError):
                pass

        if "timestamp" in raw_data:
            processed_data["ltp_timestamp"] = format_timestamp(raw_data["timestamp"])
            processed_data["ltp_age_minutes"] = calculate_age_minutes(raw_data["timestamp"])

        if "original_symbol" in raw_data:
            processed_data["original_symbol"] = raw_data["original_symbol"]

        # Process funding rate data
        if "current_funding_rate" in raw_data:
            processed_data["current_funding_rate"] = format_percentage(raw_data["current_funding_rate"])

        if "estimated_funding_rate" in raw_data:
            processed_data["estimated_funding_rate"] = format_percentage(raw_data["estimated_funding_rate"])

        if "funding_timestamp" in raw_data:
            processed_data["funding_timestamp"] = format_timestamp(raw_data["funding_timestamp"])
            processed_data["funding_age_minutes"] = calculate_age_minutes(raw_data["funding_timestamp"])

        # Return as list: [ticker, ltp, original_symbol, current_funding_rate, estimated_funding_rate, ltp_timestamp, funding_timestamp]
        return [
            ticker,                                           # 0: Ticker symbol
            processed_data["ltp"],                           # 1: Last Traded Price
            processed_data["original_symbol"],               # 2: Original symbol
            processed_data["current_funding_rate"],          # 3: Current funding rate (%)
            processed_data["estimated_funding_rate"],        # 4: Estimated funding rate (%)
            processed_data["ltp_timestamp"],                 # 5: LTP timestamp
            processed_data["funding_timestamp"],             # 6: Funding timestamp
            processed_data["ltp_age_minutes"],               # 7: LTP age in minutes
            processed_data["funding_age_minutes"]            # 8: Funding age in minutes
        ]

    except Exception as e:
        return None  # Return None on error


def list_available_tickers(redis_client: Optional[redis.Redis] = None) -> Dict[str, Any]:
    """
    List all available tickers in Redis.

    Args:
        redis_client: Redis client instance (optional)

    Returns:
        dict: List of available tickers and count
    """
    if redis_client is None:
        redis_client = setup_redis_connection()

    if redis_client is None:
        return {
            "tickers": [],
            "count": 0,
            "error": "Redis connection failed"
        }

    try:
        keys = redis_client.keys("coindcx_futures:*")
        tickers = [key.split(":")[-1] for key in keys]
        tickers.sort()

        return {
            "tickers": tickers,
            "count": len(tickers),
            "error": None
        }

    except Exception as e:
        return {
            "tickers": [],
            "count": 0,
            "error": f"Error listing tickers: {str(e)}"
        }


def fetch_multiple_tickers(tickers: List[str], redis_client: Optional[redis.Redis] = None) -> Dict[str, Optional[List]]:
    """
    Fetch data for multiple tickers.

    Args:
        tickers: List of ticker symbols
        redis_client: Redis client instance (optional)

    Returns:
        dict: Results for all tickers (ticker -> list or None)
    """
    if redis_client is None:
        redis_client = setup_redis_connection()

    results = {}
    for ticker in tickers:
        results[ticker.upper()] = fetch_ticker_data(ticker, redis_client)

    return results


def print_ticker_data(result: Optional[List], detailed: bool = True) -> None:
    """
    Pretty print ticker data.

    Args:
        result: List from fetch_ticker_data() or None
        detailed: Whether to show detailed information
    """
    if result is None:
        print(f"❌ Ticker not found or error occurred")
        return

    # Extract data from list
    ticker = result[0]
    ltp = result[1]
    original_symbol = result[2]
    current_funding_rate = result[3]
    estimated_funding_rate = result[4]
    ltp_timestamp = result[5]
    funding_timestamp = result[6]
    ltp_age_minutes = result[7]
    funding_age_minutes = result[8]

    print(f"\n📊 {ticker} Data:")
    print("=" * 40)

    # LTP Information
    if ltp is not None:
        print(f"💰 Last Traded Price: ${ltp:,.2f}")
        if ltp_timestamp and detailed:
            print(f"   📅 Updated: {ltp_timestamp}")
            if ltp_age_minutes is not None:
                print(f"   ⏰ Age: {ltp_age_minutes} minutes ago")
    else:
        print("💰 Last Traded Price: Not available")

    # Funding Rate Information
    if current_funding_rate is not None:
        print(f"📈 Current Funding Rate: {current_funding_rate:.4f}%")
    else:
        print("📈 Current Funding Rate: Not available")

    if estimated_funding_rate is not None:
        print(f"🔮 Next Funding Rate: {estimated_funding_rate:.4f}%")
    else:
        print("🔮 Next Funding Rate: Not available")

    if funding_timestamp and detailed:
        print(f"   📅 Funding Updated: {funding_timestamp}")
        if funding_age_minutes is not None:
            print(f"   ⏰ Age: {funding_age_minutes} minutes ago")

    # Symbol Information
    if original_symbol and detailed:
        print(f"🏷️  Original Symbol: {original_symbol}")


def interactive_mode(redis_client: redis.Redis) -> None:
    """
    Interactive mode for ticker lookup.

    Args:
        redis_client: Redis client instance
    """
    print("\n🔍 Interactive Mode - Enter ticker symbols to lookup")
    print("Commands: 'list' to show all tickers, 'quit' or 'exit' to quit")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nEnter ticker(s) [or command]: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if user_input.lower() == 'list':
                ticker_list = list_available_tickers(redis_client)
                if ticker_list["error"]:
                    print(f"❌ {ticker_list['error']}")
                else:
                    print(f"\n📋 Available Tickers ({ticker_list['count']}):")
                    # Print in columns
                    tickers = ticker_list["tickers"]
                    for i in range(0, len(tickers), 6):
                        row = tickers[i:i+6]
                        print("   " + "  ".join(f"{t:<8}" for t in row))
                continue

            # Handle multiple tickers
            tickers = [t.strip() for t in user_input.split()]

            if len(tickers) == 1:
                result = fetch_ticker_data(tickers[0], redis_client)
                print_ticker_data(result)
            else:
                results = fetch_multiple_tickers(tickers, redis_client)
                for result in results.values():
                    print_ticker_data(result, detailed=False)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main function for command-line interface."""

    # Setup Redis connection
    redis_client = setup_redis_connection()
    if redis_client is None:
        sys.exit(1)

    # Check command-line arguments
    if len(sys.argv) == 1:
        # No arguments - start interactive mode
        interactive_mode(redis_client)
    else:
        # Process command-line tickers
        tickers = sys.argv[1:]

        if len(tickers) == 1:
            # Single ticker - detailed view
            result = fetch_ticker_data(tickers[0], redis_client)
            print_ticker_data(result)
        else:
            # Multiple tickers - compact view
            print(f"📊 Fetching data for {len(tickers)} tickers...")
            results = fetch_multiple_tickers(tickers, redis_client)

            for result in results.values():
                print_ticker_data(result, detailed=False)


if __name__ == "__main__":
    main()