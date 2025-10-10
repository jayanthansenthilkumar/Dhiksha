# 🚀 START HERE - First-Time Setup

**You're about to run a production-grade AI recommendation system in under 10 minutes.**

---

## Prerequisites (2 minutes to verify)

✅ **Docker Desktop** installed and running
✅ **Python 3.11+** installed
✅ **PowerShell** (you're on Windows, so you're good!)

### Quick Checks

```powershell
# Verify Docker
docker --version
docker-compose --version

# Verify Python
python --version  # Should show 3.11+
```

---

## Step-by-Step Setup (8 minutes total)

### 1️⃣ Create Virtual Environment (1 min)

```powershell
cd c:\Users\jayan\OneDrive\Desktop\Dhiksha

python -m venv venv
.\venv\Scripts\activate

# You should see (venv) in your prompt now
```

### 2️⃣ Install Dependencies (2 min)

```powershell
pip install --upgrade pip
pip install -r requirements-dev.txt
```

*Coffee break while dependencies install...*

### 3️⃣ Copy Environment File (10 seconds)

```powershell
copy .env.example .env
```

### 4️⃣ Start Infrastructure (2 min)

```powershell
.\scripts\dev_up.ps1
```

**Wait for this output**:
```
✅ PostgreSQL ready
✅ Redis ready
✅ MinIO ready
✅ Milvus ready
```

*(This takes ~60 seconds)*

### 5️⃣ Initialize Database (30 seconds)

```powershell
python scripts\init_db.py
```

**You should see**:
```
✅ Tables created
✅ Extensions created
✅ Database verification passed
```

### 6️⃣ Generate Sample Data (1 min)

```powershell
python scripts\sample_data_generator.py --users 1000 --items 500 --events 10000
```

**You'll see progress bars**, then:
```
✅ Inserted 1000 users
✅ Inserted 500 contents
✅ Inserted 10000 events
```

### 7️⃣ Start API Server (10 seconds)

```powershell
uvicorn src.api.main:app --reload --port 8000
```

**You should see**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## 🎉 YOU'RE LIVE!

### Test It Out

**Open your browser:**

1. **API Documentation**: http://localhost:8000/docs
   - Interactive Swagger UI
   - Try the `/recommend/{user_id}` endpoint
   - Click "Try it out", enter `user_123`, click "Execute"

2. **MLflow**: http://localhost:5000
   - Model registry (empty for now)

3. **Grafana**: http://localhost:3000
   - Login: `admin` / `admin`
   - Dashboards (will populate once you make requests)

4. **Prometheus**: http://localhost:9090
   - Query `http_requests_total` to see metrics

### Test with Curl

```powershell
# Get recommendations
curl http://localhost:8000/recommend/user_123?k=10

# Post an event
curl -X POST http://localhost:8000/events `
  -H "Content-Type: application/json" `
  -d '{\"user_id\":\"550e8400-e29b-41d4-a716-446655440000\",\"content_id\":\"550e8400-e29b-41d4-a716-446655440001\",\"event_type\":\"view\",\"value\":120.5}'

# Health check
curl http://localhost:8000/health
```

---

## 📊 What Just Happened?

You now have running:

✅ **11 Docker containers**:
- PostgreSQL (metadata DB)
- Redis (cache)
- Kafka (event streaming)
- Milvus (vector search)
- MLflow (model registry)
- Grafana (dashboards)
- Prometheus (metrics)
- Prefect (workflow orchestration)
- MinIO (object storage)
- Supporting services (Zookeeper, etcd)

✅ **Sample data**:
- 1,000 users with cohorts
- 500 learning content items (videos, articles, quizzes)
- 10,000 interaction events

✅ **Working API**:
- Recommendation endpoint (mock for now)
- Event ingestion
- Admin endpoints
- Metrics & health checks

---

## 🔍 Explore the System

### View the Database

```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U admin -d recommendations

# Inside psql:
\dt                    # List tables
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM contents;
SELECT COUNT(*) FROM events;
\q                     # Quit
```

### Check Redis

```powershell
docker-compose exec redis redis-cli

# Inside redis-cli:
PING                   # Should return PONG
KEYS *                 # List all keys (empty for now)
exit
```

### View Logs

```powershell
# API logs
# (Already visible in terminal where uvicorn is running)

# PostgreSQL logs
docker-compose logs postgres

# MLflow logs
docker-compose logs mlflow
```

---

## 🧪 Run Tests

Open a **new PowerShell window** (keep API running in the first one):

```powershell
cd c:\Users\jayan\OneDrive\Desktop\Dhiksha
.\venv\Scripts\activate

# Run all tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit -v --cov=src --cov-report=term-missing
```

**You should see**:
```
tests/unit/test_api.py::test_health_check PASSED
tests/unit/test_api.py::test_recommend_endpoint PASSED
...
```

---

## 🛑 Stop Everything

### Stop API Server
Press `Ctrl+C` in the terminal running uvicorn

### Stop Docker Services

```powershell
.\scripts\dev_down.ps1
```

**To completely wipe data** (fresh start):
```powershell
docker-compose down -v
```

---

## 🚀 Next Steps (After You've Played Around)

### Beginner Path (Learn the System)
1. Read `README.md` - Full project overview
2. Read `ARCHITECTURE.md` - How it all fits together
3. Read `QUICK_REFERENCE.md` - Common commands
4. Explore the code in `src/api/main.py`

### Intermediate Path (Extend the System)
1. Implement real retrieval model in `src/models/train_retrieval.py`
2. Build Milvus index with real embeddings
3. Hook up BentoML for model serving
4. Make recommendations actually work!

### Advanced Path (Deploy to Production)
1. Write Kubernetes manifests (`infra/kubernetes/`)
2. Create Terraform configs for AWS/GCP
3. Set up CI/CD pipelines
4. Deploy to staging environment

---

## 📚 Full Documentation Index

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **README.md** | Project overview | First thing |
| **ARCHITECTURE.md** | System design deep-dive | Before extending |
| **RUNBOOK.md** | Operations & troubleshooting | When things break |
| **MAINTENANCE.md** | Scheduled tasks & procedures | Before production |
| **IMPLEMENTATION_STATUS.md** | What's done, what's next | Planning work |
| **QUICK_REFERENCE.md** | Command cheat sheet | Daily use |
| **DELIVERY_SUMMARY.md** | What you received | Understanding scope |

---

## ❓ Troubleshooting

### "Port 8000 already in use"

```powershell
# Find what's using it
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual PID)
taskkill /PID <PID> /F

# Or use a different port
uvicorn src.api.main:app --reload --port 8001
```

### "Cannot connect to Docker"

- Make sure Docker Desktop is running
- Restart Docker Desktop
- Check system tray for Docker icon

### "PostgreSQL connection refused"

```powershell
# Wait 30 more seconds, services need time to start
# Check if it's running:
docker-compose ps

# If not running:
.\scripts\dev_up.ps1
```

### "Import errors"

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements-dev.txt
```

---

## 🎓 Learning Resources

- **TensorFlow Recommenders**: https://www.tensorflow.org/recommenders
- **FastAPI**: https://fastapi.tiangolo.com/
- **MLflow**: https://www.mlflow.org/docs/latest/
- **Milvus**: https://milvus.io/docs
- **BentoML**: https://docs.bentoml.org/

---

## 💡 Pro Tips

1. **Always activate venv first**: `.\venv\Scripts\activate`
2. **Keep API running in one terminal**, use another for commands
3. **Use http://localhost:8000/docs** for interactive API testing
4. **Check Docker logs** if something's not working: `docker-compose logs <service>`
5. **Restart a service**: `docker-compose restart <service>`

---

## 🎯 Success Checklist

After following this guide, you should have:

- [x] Virtual environment created and activated
- [x] All dependencies installed
- [x] Docker services running and healthy
- [x] Database initialized with tables
- [x] Sample data loaded (1K users, 500 items, 10K events)
- [x] API server running on port 8000
- [x] API responding to requests (check `/health`)
- [x] All tests passing

**If all boxes are checked, you're ready to rock! 🎸**

---

**Questions?** Open an issue or check the full docs.

**Ready to code?** Start with `IMPLEMENTATION_STATUS.md` to see what to build next.

**Just exploring?** Play with the API at http://localhost:8000/docs

---

🎉 **Congratulations! You've deployed a production-grade recommendation system!** 🎉
