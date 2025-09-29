"""
Pure WebSocket LTP Monitor for Futures - Updates every 10 seconds
Supports both USDT and INR pairs
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import redis
import logging

# Add coindcx-futures directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'coindcx-futures'))

from coindcx_futures import CoinDCXFutures


async def monitor_futures_ltp(coins):
    """Monitor futures LTP using WebSocket with automatic reconnection and Redis storage"""
    client = CoinDCXFutures()

    # Redis connection setup
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
    except redis.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Redis connection failed - running without Redis storage")
        redis_client = None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Redis setup error: {e}")
        redis_client = None

    # Dictionary to store latest prices - initialize with 0 for all coins
    latest_prices = {coin: 0 for coin in coins}
    
    # Connection state tracking
    is_connected = False
    last_data_time = datetime.now()
    reconnect_attempts = 0
    max_reconnect_attempts = 10
    reconnect_delay = 5  # seconds
    
    # Helper function to format price with appropriate decimals
    def format_price(price, currency_symbol):
        """Format price with appropriate decimal places based on value"""
        if price < 0.01:
            return f"{currency_symbol}{price:.6f}"  # 6 decimals for very small prices
        elif price < 1:
            return f"{currency_symbol}{price:.4f}"  # 4 decimals for prices under $1
        elif price < 100:
            return f"{currency_symbol}{price:.3f}"  # 3 decimals for prices under $100
        else:
            return f"{currency_symbol}{price:,.2f}"  # 2 decimals for larger prices
    
    async def connect_and_subscribe():
        """Connect to WebSocket and subscribe to channels"""
        nonlocal is_connected, last_data_time, reconnect_attempts
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Connecting to WebSocket...")
            await client.connect_websocket()
            is_connected = True
            reconnect_attempts = 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WebSocket connected successfully!")
            
            # Single callback to handle trade data (which includes price)
            async def on_trade_update(data):
                nonlocal last_data_time
                try:
                    current_time = datetime.now()
                    last_data_time = current_time  # Update last data time

                    if isinstance(data, dict) and 'data' in data:
                        trade_data = json.loads(data['data']) if isinstance(data['data'], str) else data['data']

                        # Get symbol and price from trade data
                        if 's' in trade_data and 'p' in trade_data:
                            symbol = trade_data['s']
                            price = float(trade_data['p'])

                            # Update the price for this symbol
                            if symbol in latest_prices:
                                latest_prices[symbol] = price

                                # Save to Redis in real-time (Option A) - Hash Schema
                                if redis_client:
                                    try:
                                        # Extract coin name from symbol (B-ETH_USDT -> ETH)
                                        coin_name = symbol.replace('B-', '').split('_')[0]

                                        # Redis hash key: coindcx_futures:{COIN}
                                        redis_hash_key = f"coindcx_futures:{coin_name}"

                                        # Hash fields: ltp, timestamp, original_symbol
                                        redis_client.hset(redis_hash_key, mapping={
                                            "ltp": str(price),
                                            "timestamp": current_time.isoformat(),
                                            "original_symbol": symbol
                                        })

                                        # Optional: Set TTL (Time To Live) of 1 hour for auto-cleanup
                                        redis_client.expire(redis_hash_key, 3600)

                                    except Exception as redis_error:
                                        print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️ Redis save error: {redis_error}")

                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Error processing data: {e}")
            
            # Register callback for trades (trades include price info)
            client.on_new_trade(on_trade_update)
            
            # Subscribe to trade updates for each token (trades include LTP)
            for token in coins:
                try:
                    await client.subscribe_trades(token)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Subscribed to {token}")
                    await asyncio.sleep(0.1)  # Small delay between subscriptions
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Failed to subscribe to {token}: {e}")
            
            return True
            
        except Exception as e:
            is_connected = False
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Connection failed: {e}")
            # Clean up on failure
            try:
                if client.sio:
                    await client.disconnect_websocket()
            except:
                pass
            return False
    
    # Initial connection
    await connect_and_subscribe()
    
    print(f"\nMonitoring {len(coins)} futures tokens...")
    print("LTP data is being saved to Redis in real-time. Minimal console output. Press Ctrl+C to stop.\n")
    
    # Display loop with connection monitoring
    check_interval = 10  # seconds
    data_timeout = 60  # seconds - if no data for this long, consider connection dead
    
    while True:
        await asyncio.sleep(check_interval)
        
        # Check connection health
        time_since_last_data = (datetime.now() - last_data_time).total_seconds()
        
        # If no data for too long, consider connection dead
        if is_connected and time_since_last_data > data_timeout:
            is_connected = False
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No data received for {int(time_since_last_data)} seconds. Connection might be dead.")
        
        # Attempt reconnection if disconnected
        if not is_connected:
            if reconnect_attempts < max_reconnect_attempts:
                reconnect_attempts += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Attempting reconnection ({reconnect_attempts}/{max_reconnect_attempts})...")
                
                # Try to disconnect cleanly first
                try:
                    if client.sio and client.ws_connected:
                        await client.disconnect_websocket()
                        client.ws_connected = False
                        client.sio = None  # Reset the socket.io client
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Cleanup error: {e}")
                
                # Wait before reconnecting
                await asyncio.sleep(reconnect_delay)
                
                # Create fresh client for reconnection
                client = CoinDCXFutures()
                
                # Attempt to reconnect
                success = await connect_and_subscribe()
                
                if not success:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting {reconnect_delay} seconds before next attempt...")
                else:
                    last_data_time = datetime.now()  # Reset timeout
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Max reconnection attempts reached. Please restart the program.")
                break
        
        # Display prices (COMMENTED OUT - Data now saved to Redis)
        # print(f"\n{'='*50}")
        # status_icon = "🟢" if is_connected else "🔴"
        # print(f"FUTURES LTP {status_icon} - {datetime.now().strftime('%H:%M:%S')}")
        #
        # if not is_connected:
        #     print(f"Status: DISCONNECTED - Reconnecting...")
        # elif time_since_last_data > 30:
        #     print(f"Status: Connected (No data for {int(time_since_last_data)}s)")
        # else:
        #     print(f"Status: Connected (Live)")
        #
        # print(f"{'='*50}")
        #
        # for token in coins:
        #     price = latest_prices.get(token, 0)
        #     if price > 0:
        #         # Display with appropriate currency symbol and decimals
        #         if '_INR' in token:
        #             formatted = format_price(price, '₹')
        #         else:
        #             formatted = format_price(price, '$')
        #         print(f"{token:<15} : {formatted}")
        #     else:
        #         print(f"{token:<15} : Waiting...")
        #
        # print(f"{'='*50}")

        # Status update (keeping minimal logging)
        status_icon = "🟢" if is_connected else "🔴"
        if not is_connected:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} DISCONNECTED - Reconnecting...")
        elif time_since_last_data > 30:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} Connected (No data for {int(time_since_last_data)}s)")
        else:
            # Only print status every 60 seconds when connected and receiving data
            if int(time_since_last_data) % 60 == 0:
                active_symbols = sum(1 for price in latest_prices.values() if price > 0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} Connected - {active_symbols}/{len(coins)} symbols active - Data saving to Redis")


# Example usage
if __name__ == "__main__":
    # Specify the futures coins to monitor
    coins_to_monitor = [
        'B-BTC_USDT',
        'B-ETH_USDT', 
        'B-SOL_USDT',
        'B-BNB_USDT',
        'B-DOGE_USDT'
        
    ]
    
  
    
    try:
        asyncio.run(monitor_futures_ltp(coins_to_monitor))
    except KeyboardInterrupt:
        print("\n\nStopped.")