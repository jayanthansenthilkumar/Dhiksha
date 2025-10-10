# 🚀 Quick Start - No Docker Required

Follow these simple steps to run the system locally without Docker:

## Prerequisites

- Python 3.11+ installed
- PowerShell or Command Prompt

## Step 1: Install Minimal Dependencies

```powershell
# Install only the core dependencies needed for local testing
pip install fastapi uvicorn pydantic
```

That's it! No PostgreSQL, no Redis, no ML libraries needed for basic testing.

## Step 2: Run the Local Server

```powershell
# From the project root directory
python run_local.py
```

You should see:
```
================================================================================
🚀 AI Learning Recommender - Local Mode
================================================================================
✅ API running at: http://localhost:8000
✅ Frontend at: http://localhost:8000/frontend/index.html
✅ API Docs at: http://localhost:8000/docs
✅ Mock Users: 100
✅ Mock Content: 500
================================================================================
```

## Step 3: Open the Frontend

Open your browser and go to:
```
http://localhost:8000/frontend/index.html
```

## What Works in Local Mode?

✅ **Frontend UI** - Full interactive demo
✅ **Recommendations API** - Returns mock recommendations
✅ **Event Logging** - Stores events in memory
✅ **Health Checks** - API status monitoring
✅ **API Documentation** - Interactive Swagger docs at `/docs`

## What's Different from Full Stack?

- **No Database**: Uses in-memory mock data instead of PostgreSQL
- **No ML Models**: Returns randomized recommendations instead of real predictions
- **No Vector Search**: Mock similarity instead of Milvus ANN
- **No Caching**: No Redis layer
- **No Message Queue**: No Kafka event streaming

## Testing the API

### Get Recommendations
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/recommend/user_123?k=10" -Method GET
```

### Log an Event
```powershell
# PowerShell
$body = @{
    user_id = "user_123"
    content_id = "content_456"
    event_type = "view"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/events" -Method POST -Body $body -ContentType "application/json"
```

### Check Health
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
```

## Next Steps

Once you've tested the local setup, you can:

1. **Add Full Dependencies**: Install `requirements.txt` for ML models
2. **Start Docker Stack**: Run `docker-compose up -d` for full infrastructure
3. **Train Models**: Use `scripts/train_models.py`
4. **Deploy to Cloud**: Follow the K8s deployment guide

## Troubleshooting

### Port 8000 already in use
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change the port in run_local.py (last line)
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Frontend not loading
Make sure you're running from the project root directory where the `frontend/` folder exists.

### Python not found
```powershell
# Check Python installation
python --version

# If not found, download from python.org
```

## Features Available

### Frontend Features
- ✅ User ID input
- ✅ Configurable number of recommendations
- ✅ Real-time API status indicator
- ✅ Recommendation cards with scores
- ✅ Quick-action buttons (View, Like, Complete)
- ✅ Event logging form
- ✅ System statistics dashboard
- ✅ Responsive design (mobile-friendly)

### API Features
- ✅ GET `/` - Root endpoint
- ✅ GET `/health` - Health check
- ✅ GET `/recommend/{user_id}` - Get recommendations
- ✅ POST `/events` - Log user events
- ✅ GET `/stats` - System statistics
- ✅ GET `/docs` - Interactive API documentation

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

---

**Ready for the full stack?** See `START_HERE.md` for Docker-based setup with real ML models!
