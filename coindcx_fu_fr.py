import requests
import time
import redis
from datetime import datetime
from typing import Dict, Optional, Any


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
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Redis connected successfully!")
        return redis_client
    except redis.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Redis connection failed - running without Redis storage")
        return None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Redis setup error: {e}")
        return None


def get_coindcx_funding_rate(symbol: str) -> Dict[str, Optional[float]]:
    """
    Fetch the current and estimated funding rates for a CoinDCX futures symbol.
    
    Args:
        symbol (str): The futures trading pair symbol in CoinDCX format.
                     Common formats include:
                     - "B-BTC_USDT", "B-ETH_USDT" (Binance-like perpetuals)
                     - "F-BTC_USDT", "F-ETH_USDT" (Futures contracts)
                     - "BM-BTC_USD", "BM-ETH_USD" (USD margined)
                     Symbol should be in uppercase format with proper prefix.
    
    Returns:
        dict: A dictionary containing:
            - "current_funding": Current funding rate (float or None if not available)
            - "estimated_funding": Estimated next funding rate (float or None if not available)
            - "error": Error message if request fails (str or None if successful)
    
    Raises:
        None: All exceptions are caught and returned in the error field
    
    Example:
        >>> result = get_coindcx_funding_rate("B-BTC_USDT")
        >>> if result.get("error"):
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     print(f"Current funding: {result['current_funding']}")
        ...     print(f"Estimated funding: {result['estimated_funding']}")
    """
    
    # API endpoint for CoinDCX futures market data
    api_url = "https://public.coindcx.com/market_data/v3/current_prices/futures/rt"
    
    # Initialize return dictionary
    result = {
        "current_funding": None,
        "estimated_funding": None,
        "error": None
    }
    
    try:
        # Make GET request to the API
        response = requests.get(api_url, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            result["error"] = f"API request failed with status code: {response.status_code}"
            return result
        
        # Parse JSON response
        data = response.json()
        
        # Check if the response has the expected structure
        if not isinstance(data, dict) or "prices" not in data:
            result["error"] = "Unexpected API response format"
            return result
        
        prices_data = data.get("prices", {})
        
        # Convert symbol to uppercase to ensure consistency
        symbol = symbol.upper()
        
        # Check if the symbol exists in the response
        if symbol not in prices_data:
            result["error"] = f"Symbol '{symbol}' not found in CoinDCX futures market"
            return result
        
        # Extract funding rates for the specified symbol
        symbol_data = prices_data[symbol]
        
        # Get current funding rate (fr)
        if "fr" in symbol_data:
            try:
                result["current_funding"] = float(symbol_data["fr"])
            except (ValueError, TypeError):
                result["current_funding"] = None
        
        # Get estimated funding rate (efr)
        if "efr" in symbol_data:
            try:
                result["estimated_funding"] = float(symbol_data["efr"])
            except (ValueError, TypeError):
                result["estimated_funding"] = None
        
        return result
        
    except requests.exceptions.Timeout:
        result["error"] = "Request timeout - API took too long to respond"
        return result
    
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection error - unable to reach CoinDCX API"
        return result
    
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request failed: {str(e)}"
        return result
    
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        return result


def get_all_coindcx_funding_rates() -> Dict[str, Any]:
    """
    Fetch funding rates for all available CoinDCX futures symbols.
    
    Returns:
        dict: A dictionary containing:
            - "symbols": Dict with symbol as key and funding rates as value
            - "error": Error message if request fails (str or None if successful)
            - "total_symbols": Number of symbols retrieved
    
    Example:
        >>> result = get_all_coindcx_funding_rates()
        >>> if result.get("error"):
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     print(f"Total symbols: {result['total_symbols']}")
        ...     for symbol, rates in result['symbols'].items():
        ...         print(f"{symbol}: Current={rates['current_funding']}, Estimated={rates['estimated_funding']}")
    """
    
    # API endpoint for CoinDCX futures market data
    api_url = "https://public.coindcx.com/market_data/v3/current_prices/futures/rt"
    
    # Initialize return dictionary
    result = {
        "symbols": {},
        "error": None,
        "total_symbols": 0
    }
    
    try:
        # Make GET request to the API
        response = requests.get(api_url, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            result["error"] = f"API request failed with status code: {response.status_code}"
            return result
        
        # Parse JSON response
        data = response.json()
        
        # Check if the response has the expected structure
        if not isinstance(data, dict) or "prices" not in data:
            result["error"] = "Unexpected API response format"
            return result
        
        prices_data = data.get("prices", {})
        
        # Process each symbol
        for symbol, symbol_data in prices_data.items():
            funding_info = {
                "current_funding": None,
                "estimated_funding": None
            }
            
            # Get current funding rate (fr)
            if "fr" in symbol_data:
                try:
                    funding_info["current_funding"] = float(symbol_data["fr"])
                except (ValueError, TypeError):
                    pass
            
            # Get estimated funding rate (efr)
            if "efr" in symbol_data:
                try:
                    funding_info["estimated_funding"] = float(symbol_data["efr"])
                except (ValueError, TypeError):
                    pass
            
            result["symbols"][symbol] = funding_info
        
        result["total_symbols"] = len(result["symbols"])
        return result
        
    except requests.exceptions.Timeout:
        result["error"] = "Request timeout - API took too long to respond"
        return result
    
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection error - unable to reach CoinDCX API"
        return result
    
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request failed: {str(e)}"
        return result
    
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        return result


def format_funding_rate(rate: Optional[float]) -> str:
    """
    Format funding rate for display (converts to percentage).

    Args:
        rate: Funding rate as a decimal value

    Returns:
        str: Formatted funding rate as percentage or "N/A" if None
    """
    if rate is None:
        return "N/A"
    return f"{rate * 100:.4f}%"


def save_funding_rates_to_redis(redis_client: redis.Redis, funding_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Save funding rates to Redis using the same hash schema as LTP data.

    Args:
        redis_client: Redis client instance
        funding_data: Result from get_all_coindcx_funding_rates()

    Returns:
        dict: Statistics about saved data {"saved": count, "errors": count}
    """
    if not redis_client or funding_data.get("error"):
        return {"saved": 0, "errors": 0}

    saved_count = 0
    error_count = 0
    current_time = datetime.now()

    for symbol, rates in funding_data.get("symbols", {}).items():
        try:
            # Extract coin name from symbol (B-DOGE_USDT -> DOGE)
            coin_name = symbol.replace('B-', '').replace('F-', '').replace('BM-', '').split('_')[0]

            # Redis hash key: coindcx_futures:{COIN} (same as LTP schema)
            redis_hash_key = f"coindcx_futures:{coin_name}"

            # Prepare funding rate fields to add to existing hash
            funding_fields = {}

            if rates["current_funding"] is not None:
                funding_fields["current_funding_rate"] = str(rates["current_funding"])

            if rates["estimated_funding"] is not None:
                funding_fields["estimated_funding_rate"] = str(rates["estimated_funding"])

            # Always update funding timestamp
            funding_fields["funding_timestamp"] = current_time.isoformat()

            # Update hash with funding rate fields (preserves existing LTP fields)
            if funding_fields:
                redis_client.hset(redis_hash_key, mapping=funding_fields)

                # Set TTL of 1 hour (same as LTP data)
                redis_client.expire(redis_hash_key, 3600)

                saved_count += 1

        except Exception as e:
            error_count += 1
            print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️ Redis save error for {symbol}: {e}")

    return {"saved": saved_count, "errors": error_count}


def display_funding_rates(result: Dict[str, Any], fetch_count: int, redis_client: Optional[redis.Redis] = None) -> None:
    """
    Display funding rates in a formatted table and save to Redis.

    Args:
        result: Result from get_all_coindcx_funding_rates()
        fetch_count: Number of fetch cycles completed
        redis_client: Redis client instance for storage
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*80}")
    print(f"🔄 Fetch #{fetch_count} - {timestamp}")
    print(f"{'='*80}")

    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        return

    print(f"✅ Success! Found {result['total_symbols']} symbols\n")

    # Save to Redis if available
    redis_stats = {"saved": 0, "errors": 0}
    if redis_client:
        redis_stats = save_funding_rates_to_redis(redis_client, result)
        print(f"💾 Redis: Saved {redis_stats['saved']} symbols" +
              (f", {redis_stats['errors']} errors" if redis_stats['errors'] > 0 else ""))

    print(f"{'Symbol':<15} | {'Current Rate':>12} | {'Estimated Rate':>12}")
    print(f"{'-'*15} | {'-'*12} | {'-'*12}")

    # Sort symbols alphabetically for better readability
    sorted_symbols = sorted(result["symbols"].items())

    for symbol, rates in sorted_symbols:
        current_rate = format_funding_rate(rates["current_funding"])
        estimated_rate = format_funding_rate(rates["estimated_funding"])
        print(f"{symbol:<15} | {current_rate:>12} | {estimated_rate:>12}")

    print(f"\nTotal symbols processed: {result['total_symbols']}")
    next_time = datetime.now().replace(second=0, microsecond=0)
    next_time = next_time.replace(minute=(next_time.minute + 30) % 60)
    if next_time.minute < datetime.now().minute:
        next_time = next_time.replace(hour=next_time.hour + 1)
    print(f"Next fetch in 30 minutes at: {next_time.strftime('%H:%M:%S')}")


def run_continuous_monitoring():
    """
    Run continuous funding rate monitoring every 30 minutes with Redis storage.
    """
    print("🚀 Starting CoinDCX Futures Funding Rate Monitor")
    print("📅 Fetching all symbols every 30 minutes")
    print("💾 Storing in Redis using same schema as LTP data")
    print("⏹️  Press Ctrl+C to stop monitoring")
    print("=" * 80)

    # Setup Redis connection
    redis_client = setup_redis_connection()

    fetch_count = 0
    success_count = 0
    error_count = 0
    total_redis_saves = 0

    try:
        while True:
            fetch_count += 1

            # Fetch funding rates for all symbols
            result = get_all_coindcx_funding_rates()

            # Track success/error counts
            if result.get("error"):
                error_count += 1
            else:
                success_count += 1

            # Display results and save to Redis
            display_funding_rates(result, fetch_count, redis_client)

            # Update Redis statistics
            if redis_client and not result.get("error"):
                total_redis_saves += result.get("total_symbols", 0)

            # Show statistics
            redis_status = f", {total_redis_saves} Redis saves" if redis_client else ", Redis: disabled"
            print(f"\n📊 Statistics: {success_count} successful fetches, {error_count} errors{redis_status}")

            # Wait for 30 minutes (1800 seconds)
            next_fetch_time = datetime.now().replace(second=0, microsecond=0)
            next_fetch_time = next_fetch_time.replace(minute=(next_fetch_time.minute + 30) % 60)
            if next_fetch_time.minute < datetime.now().minute:
                next_fetch_time = next_fetch_time.replace(hour=next_fetch_time.hour + 1)

            print(f"⏰ Next fetch scheduled for: {next_fetch_time.strftime('%H:%M:%S')}")
            print("💤 Sleeping for 30 minutes... (Press Ctrl+C to stop)")

            time.sleep(30 * 60)  # 30 minutes in seconds

    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitoring stopped by user")
        print(f"📊 Final statistics:")
        print(f"   • Total fetches: {fetch_count}")
        print(f"   • Successful: {success_count}")
        print(f"   • Errors: {error_count}")
        if redis_client:
            print(f"   • Redis saves: {total_redis_saves}")
        print("👋 Goodbye!")


if __name__ == "__main__":
    run_continuous_monitoring()