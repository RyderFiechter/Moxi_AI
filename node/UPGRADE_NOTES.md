# Upgrade Notes: Simulator → Real Node

This document describes the upgrade from the lightweight simulator to a real storage node.

## What Changed

### 1. Real System Statistics
- **Before**: Simulated random storage values
- **After**: Real disk stats using `psutil`
  - Total storage from actual filesystem
  - Free storage from actual available space
  - Used storage calculated from real values

### 2. HTTP API
- **Before**: No API, only console output
- **After**: FastAPI-based REST API with endpoints:
  - `GET /status` - Node status JSON
  - `POST /ping` - Update ping timestamp
  - `GET /health` - Health check
  - `GET /docs` - Interactive API docs
  - `POST /register` - Stub for future registry

### 3. Real Uptime Tracking
- **Before**: Simulated uptime
- **After**: Real process uptime since node start
  - Formatted as "2m 30s" or "1h 15m 30s"
  - Accurate to the second

### 4. Configuration
- **Before**: Command-line arguments only
- **After**: JSON config file (`config.json`) with:
  - Port customization
  - Host binding
  - Ping interval
  - Identity file path

### 5. Dependencies
- **Before**: Standard library only
- **After**: Added:
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server
  - `psutil` - System stats

## File Changes

### `node.py`
- Removed simulated storage values
- Added `psutil` for real disk stats
- Updated methods to use real system values
- Added `format_uptime()` for human-readable uptime
- Simplified `_ping_loop()` to log status instead of network pings

### `main.py`
- Completely rewritten
- Now launches FastAPI server
- Loads config from JSON
- Starts node with background ping task
- Runs server and node concurrently

### `node_api.py` (NEW)
- FastAPI application
- REST endpoints for monitoring
- Global node instance management

### `config.json` (NEW)
- Configuration file for port, host, ping interval

### `requirements.txt` (NEW)
- Python dependencies list

## Migration Guide

### For Existing Simulator Users

If you were using the old simulator:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the new node:**
   ```bash
   python main.py
   ```

3. **Access the API:**
   - Visit `http://localhost:8000/status` for JSON status
   - Visit `http://localhost:8000/docs` for API docs

### Old Simulator Files

The old `main.py` that ran multiple simulated nodes is replaced. If you need the multi-node simulator, you can:
- Keep a backup of the old version
- Use `network.py` with the new node (with modifications)

## New Features

### Real Storage Reporting
The node now reports actual disk space:
- Windows: Uses `C:\` drive
- Linux/Mac: Uses root filesystem `/`
- Falls back to defaults if psutil fails

### HTTP Monitoring
External services can now:
- Query node status via HTTP
- Monitor node health
- Trigger pings programmatically
- Integrate with monitoring systems

### Persistent Identity
Node identity (wallet address) is saved to `node_identity.json` and persists between runs.

## API Usage Examples

### Get Status
```bash
curl http://localhost:8000/status
```

### Send Ping
```bash
curl -X POST http://localhost:8000/ping
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Next Steps

The node is now ready for:
1. **Network Registry Integration**: Implement `/register` endpoint
2. **Blockchain Connection**: Add staking and rewards
3. **File Operations**: Store and retrieve file chunks
4. **Proof of Storage**: Implement actual verification
5. **Monitoring Integration**: Connect to Prometheus/Grafana

## Backward Compatibility

The old simulator is not compatible with this version. If you need the multi-node simulator:
- Keep a separate copy of the old code
- Or modify `network.py` to work with the new real nodes

