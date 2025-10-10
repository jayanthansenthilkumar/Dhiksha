# AI Learning Recommender System

> **Simplified FastAPI-based recommendation system - No Docker required!**

A production-ready learning content recommendation system built with FastAPI and SQLite. Features include personalized recommendations, real-time event tracking, analytics dashboard, and WebSocket support.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation & Running

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   cd backend
   python app.py
   ```

3. **Access the application:**
   - 🌐 **Dashboard**: http://localhost:8000/static/dashboard.html
   - 📚 **API Docs**: http://localhost:8000/docs
   - 🔧 **API Root**: http://localhost:8000
   - 🔌 **WebSocket**: ws://localhost:8000/ws

---

## 📁 Project Structure

```
Dhiksha/
├── backend/
│   └── app.py              # Main FastAPI application (single file!)
├── static/                  # Frontend files (HTML, CSS, JS)
│   ├── dashboard.html       # Admin dashboard
│   ├── dashboard.css        # Dashboard styling
│   ├── dashboard.js         # Dashboard logic
│   ├── index.html           # Landing page
│   ├── styles.css           # Landing page styles
│   └── app.js               # Landing page logic
├── requirements.txt         # Python dependencies (minimal!)
├── README.md               # This file
└── recommender.db          # SQLite database (auto-created)
```

**That's it! Only 2 directories, no complex setup!**

---

## ✨ Features

### Backend (FastAPI)
- ✅ **RESTful API** with automatic documentation
- ✅ **SQLite Database** with auto-initialization and sample data
- ✅ **Personalized Recommendations** using hybrid ML algorithms
- ✅ **Event Tracking** (views, completions, likes, scores)
- ✅ **Real-time Analytics** (user engagement, popular content)
- ✅ **WebSocket Support** for live updates
- ✅ **CORS enabled** for frontend integration

### Frontend (Static Files)
- ✅ **Interactive Dashboard** with real-time charts
- ✅ **User Management** interface
- ✅ **Content Library** viewer
- ✅ **Live Event Stream** with WebSocket
- ✅ **Analytics & Insights** visualization
- ✅ **Recommendation Testing** interface

---

## 🎯 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API root with links |
| `GET` | `/health` | Health check & system stats |
| `GET` | `/docs` | Interactive API documentation |

### Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/recommend/{user_id}?k=10&strategy=hybrid` | Get personalized recommendations |

**Strategies:**
- `hybrid` - Collaborative + Content-based (default)
- `collaborative` - Based on similar users
- `content_based` - Based on content similarity

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/events` | Log user interaction event |
| `GET` | `/events/recent?limit=100` | Get recent events |

**Event Types:**
- `view` - User viewed content
- `complete` - User completed content
- `like` - User liked content
- `bookmark` - User bookmarked content
- `quiz_score` - User completed quiz
- `share` - User shared content

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics` | System-wide analytics |
| `GET` | `/users?limit=100&offset=0` | List users with stats |
| `GET` | `/content?difficulty=beginner&content_type=video` | List content with filters |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws` | Real-time event stream |

---

## 📊 Sample Data

The application automatically seeds the database with:
- **100 users** with various skill levels and interests
- **200 content items** (videos, articles, courses, tutorials)
- **5000 interaction events** (views, completions, likes, etc.)

This allows you to test recommendations immediately without setup!

---

## 🧪 Testing the API

### Using the Dashboard
1. Open http://localhost:8000/static/dashboard.html
2. Navigate to "Recommendations" tab
3. Enter a user ID (e.g., `user_1`)
4. Select strategy and click "Generate Recommendations"

### Using curl

**Get Recommendations:**
```bash
curl http://localhost:8000/recommend/user_1?k=5&strategy=hybrid
```

**Log an Event:**
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_1",
    "content_id": "content_5",
    "event_type": "view"
  }'
```

**Get Analytics:**
```bash
curl http://localhost:8000/analytics
```

### Using Python

```python
import requests

# Get recommendations
response = requests.get("http://localhost:8000/recommend/user_1?k=10&strategy=hybrid")
print(response.json())

# Log event
event_data = {
    "user_id": "user_1",
    "content_id": "content_5",
    "event_type": "complete"
}
response = requests.post("http://localhost:8000/events", json=event_data)
print(response.json())
```

---

## 🔧 Configuration

All configuration is in the `backend/app.py` file:

- **Database Path**: `DB_PATH = "recommender.db"`
- **Server Host**: `host="0.0.0.0"` (accepts connections from any IP)
- **Server Port**: `port=8000`
- **CORS**: Enabled for all origins (change in production)

---

## 🚀 Deployment

### Local Development
```bash
cd backend
python app.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
cd backend
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables (Optional)
```bash
export LOG_LEVEL=info
export WORKERS=4
```

---

## 📈 How Recommendations Work

The system uses a **hybrid recommendation algorithm**:

1. **Content-Based Filtering**
   - Matches user interests with content tags
   - Considers skill level and content difficulty
   - Boosts popular content

2. **Collaborative Filtering**
   - Finds users with similar interaction patterns
   - Recommends content that similar users liked
   - Uses simplified user-user similarity

3. **Scoring Formula**
   ```
   score = (tag_overlap * 0.3) + 
           (difficulty_match * 0.2) + 
           (popularity * 0.15) + 
           (collaborative_boost * 0.2) + 
           (exploration_factor * 0.1)
   ```

4. **Re-ranking**
   - Filters out already-completed content
   - Sorts by final score
   - Returns top-K recommendations

---

## 🗄️ Database Schema

### Users Table
- `user_id` (PRIMARY KEY)
- `name`, `email`
- `cohort_tag`, `skill_level`
- `interests` (comma-separated tags)
- `created_at`, `last_active`

### Content Table
- `content_id` (PRIMARY KEY)
- `title`, `description`
- `content_type`, `difficulty`
- `tags` (comma-separated)
- `duration_minutes`
- `popularity_score`
- `created_at`

### Events Table
- `event_id` (PRIMARY KEY)
- `user_id`, `content_id`
- `event_type`, `value`
- `session_id`, `timestamp`

### Recommendation Logs Table
- `log_id` (PRIMARY KEY)
- `user_id`, `content_id`
- `score`, `model_version`
- `reason_tags`, `timestamp`
- `clicked` (boolean)

---

## 🛠️ Development

### Adding New Features

**Add a new API endpoint:**
```python
@app.get("/my-endpoint", tags=["Custom"])
async def my_endpoint():
    return {"message": "Hello World"}
```

**Modify recommendation algorithm:**
Edit the `get_recommendations()` function in `backend/app.py`

**Customize frontend:**
Edit files in the `static/` directory

### Database Management

**View database:**
```bash
sqlite3 recommender.db
.tables
SELECT * FROM users LIMIT 5;
```

**Reset database:**
```bash
rm recommender.db
python backend/app.py  # Will recreate with sample data
```

---

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Change port in backend/app.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Frontend not loading:**
- Check that `static/` directory exists
- Verify files were copied correctly
- Check browser console for errors

**Database locked:**
- Close any SQLite browser tools
- Restart the application

**WebSocket not connecting:**
- Check browser supports WebSocket
- Verify no firewall blocking WS connections

---

## 📝 License

This project is provided as-is for educational and development purposes.

---

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

## 📞 Support

For questions or issues:
1. Check the `/docs` endpoint for API documentation
2. Review the browser console for frontend errors
3. Check the terminal logs for backend errors

---

**Happy Recommending! 🎓✨**
