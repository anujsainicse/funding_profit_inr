# Quick Debugging Commands

## Check if Bybit monitor is running
```bash
ps aux | grep "python.*src.main" | grep -v grep
```

## Real-time log monitoring
```bash
cd /Users/anujsainicse/claude/funding_profit_inr_ltp/bybitspotpy
tail -f logs/bybit_spot.log
```

## Check for errors
```bash
grep '"level": "error"' logs/bybit_spot.log | tail -10
```

## Check health status
```bash
grep "Connection health check" logs/bybit_spot.log | tail -1
```

## Check for stuck connections
```bash
grep "stuck" logs/bybit_spot.log
```

## Check reconnections
```bash
grep "reconnect" logs/bybit_spot.log | tail -10
```

## Check message processing rate
```bash
grep "Message processing stats" logs/bybit_spot.log | tail -5
```

## View current prices in Redis
```bash
redis-cli hgetall bybit_spot:BTC
redis-cli hgetall bybit_spot:ETH
redis-cli hgetall bybit_spot:SOL
```

## Restart monitor
```bash
pkill -f "python.*src.main"
cd /Users/anujsainicse/claude/funding_profit_inr_ltp/bybitspotpy
python -m src.main
```

## What to look for when connection stalls:

1. **Last message time**: Check health logs for `seconds_since_last_message`
2. **Error logs**: Look for any errors before the stall
3. **Reconnection pattern**: Is it reconnecting automatically?
4. **Total messages**: Are messages still being processed?

## Typical healthy output:
```json
{"seconds_since_last_message": 0.15, "total_messages": 2571, "reconnects": 1, "event": "Connection health check"}
```

If `seconds_since_last_message` > 60, automatic reconnection will trigger.
