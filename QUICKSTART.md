# 🚀 QUICK START GUIDE

## ⚡ Super Fast Setup (3 Steps!)

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Run the Application
```powershell
.\run.ps1
```
**OR** navigate to backend and run directly:
```powershell
cd backend
python app.py
```

### Step 3: Open Your Browser
- 📊 **Dashboard**: http://localhost:8000/static/dashboard.html
- 📚 **API Docs**: http://localhost:8000/docs


## 📁 Project Structure

```
Dhiksha/                    ← Your project root
│
├── backend/                ← FastAPI backend (1 file!)
│   └── app.py             ← Main application (everything in one file)
│
├── static/                 ← Frontend files
│   ├── dashboard.html     ← Admin dashboard
│   ├── dashboard.css      ← Dashboard styles
│   ├── dashboard.js       ← Dashboard logic
│   ├── index.html         ← Landing page
│   ├── styles.css         ← Landing page styles
│   └── app.js             ← Landing page logic
│
├── requirements.txt        ← Python dependencies (minimal - only 5!)
├── README.md              ← Full documentation
├── run.ps1                ← Windows run script
├── run.sh                 ← Linux/Mac run script
└── recommender.db         ← SQLite database (auto-created)
```

**Total: 2 directories, ~10 files. That's it!**

---

## ✨ What's Included

### Backend (1 Python file)
- ✅ FastAPI server
- ✅ SQLite database (auto-setup)
- ✅ 100 sample users
- ✅ 200 sample content items
- ✅ 5000 sample events
- ✅ ML recommendation algorithm
- ✅ Real-time WebSocket
- ✅ Analytics endpoints

### Frontend (HTML/CSS/JS)
- ✅ Interactive dashboard
- ✅ Real-time charts
- ✅ User management
- ✅ Content browser
- ✅ Live event stream
- ✅ Analytics visualizations

---

## 🎯 Test It Out

### 1. Get Recommendations
```bash
# Using browser: Open http://localhost:8000/docs
# Using curl:
curl http://localhost:8000/recommend/user_1?k=5

# Using Python:
import requests
r = requests.get("http://localhost:8000/recommend/user_1?k=10")
print(r.json())
```

### 2. Log an Event
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_1",
    "content_id": "content_5",
    "event_type": "view"
  }'
```

### 3. View Analytics
```bash
curl http://localhost:8000/analytics
```

---

## 🔧 Dependencies (Only 5!)

1. **fastapi** - Web framework
2. **uvicorn** - ASGI server
3. **pydantic** - Data validation
4. **python-multipart** - File uploads
5. **websockets** - Real-time updates

**No Docker, No PostgreSQL, No Redis, No Kafka, No ML libraries!**
Everything runs with just Python and SQLite!

---

## 💡 Key Features

| Feature | Technology | Description |
|---------|-----------|-------------|
| **Backend** | FastAPI | Fast, modern Python web framework |
| **Database** | SQLite | Built-in, no installation needed |
| **Frontend** | Vanilla JS | No framework, pure HTML/CSS/JS |
| **Real-time** | WebSocket | Live updates without polling |
| **ML** | Custom Algorithm | Hybrid collaborative + content-based |
| **Deployment** | Single File | Everything in `backend/app.py` |

---

## 🎓 How to Use

### For Testing
1. Run the app
2. Open dashboard at http://localhost:8000/static/dashboard.html
3. Try the "Recommendations" tab
4. Enter `user_1` and click "Generate Recommendations"

### For Development
1. Edit `backend/app.py` to modify API
2. Edit `static/*.html` to modify frontend
3. Changes are live (FastAPI auto-reloads)

### For Production
```bash
pip install gunicorn
cd backend
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 🐛 Troubleshooting

**Problem: Port 8000 already in use**
```python
# Edit backend/app.py, change port:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Problem: Module not found**
```bash
pip install -r requirements.txt
```

**Problem: Database locked**
```bash
# Close any SQLite browser, then:
rm recommender.db
python backend/app.py  # Will recreate
```

---

## 📚 Learn More

- Read `README.md` for full documentation
- Check `/docs` endpoint for API reference
- Explore `backend/app.py` to understand the code
- Review `CLEANUP_GUIDE.md` to see what was removed

---

**That's it! Enjoy your simplified recommendation system! 🎉**
