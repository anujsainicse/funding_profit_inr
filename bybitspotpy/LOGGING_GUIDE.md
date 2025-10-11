# Bybit Spot Monitor - Logging and Debugging Guide

## Overview

The Bybit Spot Price Monitor now includes comprehensive logging and health monitoring to diagnose connection issues and track system behavior.

## Log Location

All logs are stored in JSON format:
```
/Users/anujsainicse/claude/funding_profit_inr_ltp/bybitspotpy/logs/bybit_spot.log
```

**Log Rotation:**
- Maximum file size: 10 MB
- Backup files: 5 (keeps last 5 rotations)
- Older logs are automatically archived with `.1`, `.2`, etc. suffixes

## Features

### 1. Comprehensive Event Logging

Every significant event is logged with structured JSON data:

- **Connection Events**: WebSocket connect, disconnect, reconnect attempts
- **Message Processing**: Total messages received, processing errors
- **Redis Operations**: Connection status, write failures
- **Health Checks**: Periodic connection health status (every 30 seconds)

### 2. Health Monitoring

The monitor includes automatic health checking:

- **Check Interval**: Every 30 seconds
- **Timeout Threshold**: 60 seconds without messages triggers reconnection
- **Metrics Tracked**:
  - Time since last message
  - Total messages processed
  - Number of reconnections
  - WebSocket connection status

### 3. Automatic Reconnection

If the connection gets stuck (no messages for 60 seconds):
1. Health monitor detects the issue
2. Logs error with detailed diagnostics
3. Forces WebSocket closure
4. Main loop automatically reconnects
5. All tracked in logs

## Viewing Logs

### Real-time Monitoring

```bash
# Follow logs in real-time
tail -f /Users/anujsainicse/claude/funding_profit_inr_ltp/bybitspotpy/logs/bybit_spot.log

# Pretty print JSON logs
tail -f logs/bybit_spot.log | python -m json.tool
```

### Checking for Errors

```bash
# View all errors
grep '"level": "error"' logs/bybit_spot.log | tail -20

# View all warnings
grep '"level": "warning"' logs/bybit_spot.log | tail -20

# Check health status
grep "health" logs/bybit_spot.log | tail -10
```

### Connection Issues

```bash
# Check reconnection events
grep "reconnect" logs/bybit_spot.log

# Check WebSocket connection logs
grep "WebSocket" logs/bybit_spot.log | tail -20

# Check for stuck connections
grep "stuck" logs/bybit_spot.log
```

### Redis Issues

```bash
# Check Redis connection
grep "Redis" logs/bybit_spot.log | tail -10

# Check Redis write failures
grep "Failed to write to Redis" logs/bybit_spot.log
```

## Log Entry Structure

Each log entry is a JSON object with these fields:

```json
{
  "event": "Description of what happened",
  "logger": "src.bybit_client",
  "level": "info|warning|error",
  "timestamp": "2025-10-10T13:22:46.742621Z",
  "additional_context": "varies by event"
}
```

### Common Log Events

#### Startup
```json
{"event": "Bybit client initialized", "coins": [...], "ws_url": "..."}
{"event": "Connected to Redis successfully", "db": 0}
{"event": "Health monitor started", "timeout_threshold": 60}
```

#### Connection Health
```json
{"event": "Connection health check",
 "seconds_since_last_message": 0.15,
 "total_messages": 1534,
 "reconnects": 1}
```

#### Stuck Connection (Error)
```json
{"event": "Connection appears stuck - no messages received",
 "seconds_since_last_message": 65.5,
 "threshold": 60,
 "total_messages": 1200,
 "reconnects": 2}
```

#### Reconnection
```json
{"event": "WebSocket connection closed",
 "code": 1006,
 "reason": "Connection lost",
 "reconnecting": true}
```

#### Message Stats (every 100 messages)
```json
{"event": "Message processing stats",
 "total_messages": 500,
 "reconnects": 1}
```

## Troubleshooting Guide

### Problem: Connection keeps getting stuck

**Check logs for:**
```bash
grep "stuck" logs/bybit_spot.log
grep "timeout_threshold" logs/bybit_spot.log
```

**What to look for:**
- `seconds_since_last_message` value when it gets stuck
- Pattern of when it happens (time of day, after X messages, etc.)
- Any errors before the connection stalls

### Problem: Frequent reconnections

**Check logs for:**
```bash
grep "reconnect_count" logs/bybit_spot.log | tail -20
```

**What to look for:**
- Connection close codes and reasons
- Network-related errors
- Pattern in reconnection timing

### Problem: Redis write failures

**Check logs for:**
```bash
grep "Failed to write to Redis" logs/bybit_spot.log
```

**What to look for:**
- Error messages from Redis
- Connection status before failure
- Which coins are affected

### Problem: No price updates

**Check logs for:**
```bash
# Verify messages are being received
grep "Message processing stats" logs/bybit_spot.log | tail -5

# Check last health status
grep "Connection health check" logs/bybit_spot.log | tail -1

# Look for subscription issues
grep "Subscription" logs/bybit_spot.log
```

## Configuration

You can adjust health monitoring parameters in `src/bybit_client.py`:

```python
self.ping_interval = 20        # WebSocket ping interval (seconds)
self.timeout_threshold = 60    # Reconnect if no messages (seconds)
```

Lower values = more aggressive reconnection
Higher values = more tolerant of slow periods

## Log Analysis Tools

### Count events by type
```bash
cat logs/bybit_spot.log | jq -r '.event' | sort | uniq -c | sort -nr
```

### Get reconnection timeline
```bash
cat logs/bybit_spot.log | jq 'select(.reconnect_count != null) | {timestamp, event, reconnect_count}'
```

### Check message rate
```bash
cat logs/bybit_spot.log | jq 'select(.total_messages != null) | {timestamp, total_messages, reconnects}'
```

### Find all errors with timestamps
```bash
cat logs/bybit_spot.log | jq 'select(.level == "error") | {timestamp, event, error}'
```

## Monitoring in Production

For production monitoring, consider:

1. **Set up log aggregation** (e.g., ELK stack, Datadog)
2. **Create alerts** for:
   - Reconnection count > threshold
   - Errors in logs
   - Health check failures
   - Message rate drops

3. **Monitor metrics**:
   - Messages per minute
   - Reconnection frequency
   - Time between health checks
   - Error rate

## Support

If you encounter issues:

1. Check the logs for errors
2. Look for patterns (timing, frequency)
3. Verify network connectivity
4. Check Redis availability
5. Review Bybit API status

For persistent issues, share:
- Relevant log excerpts
- Pattern description
- System environment details
