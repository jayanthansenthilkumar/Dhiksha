# 🎓 AI Learning Recommender - Full Featured Dashboard

> **Production-ready recommendation system with advanced analytics, real-time monitoring, and beautiful dashboard**

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Installation

```powershell
# 1. Install dependencies
pip install fastapi uvicorn pydantic

# 2. Run the full-featured application
python app_full.py
```

### Access the Dashboard

Once running, open your browser to:
- **🎨 Dashboard**: http://localhost:8000/static/dashboard.html
- **📖 API Docs**: http://localhost:8000/docs
- **🔌 WebSocket**: ws://localhost:8000/ws

## ✨ Features

### 📊 Dashboard Overview
- **Real-time Statistics**: Total users, content, events, and active users
- **Event Distribution Chart**: Visualize user activity patterns
- **Engagement Trends**: 7-day trend analysis
- **Popular Content**: Top-performing content ranked by interactions
- **Live Activity Feed**: Recent user actions in real-time

### 🎯 Recommendation Engine
- **Multiple Strategies**:
  - **Hybrid**: Combines collaborative filtering + content-based
  - **Collaborative Filtering**: User-user similarity
  - **Content-Based**: Item features and tags
- **Configurable Results**: 1-50 recommendations per request
- **Confidence Scores**: ML-powered scoring with explanations
- **Reason Tags**: Why each item was recommended

### 👥 User Management
- **User List**: Paginated view of all users
- **User Analytics**: Individual user insights
  - Total events
  - Content viewed/completed
  - Average quiz scores
  - Preferred topics
  - Activity trends
- **Search & Filter**: Find users quickly
- **Event History**: Per-user interaction tracking

### 📚 Content Library
- **Grid View**: Beautiful card-based layout
- **Filter by Type**: Videos, articles, courses, tutorials, quizzes, projects
- **Search**: Real-time content search
- **Metadata**: Difficulty, duration, popularity scores
- **Tags**: Topic categorization

### ⚡ Live Event Stream
- **Real-time WebSocket**: Live event updates
- **Event Types**: View, complete, like, quiz_score, bookmark, share
- **User Context**: See who did what, when
- **Auto-refresh**: New events appear automatically

### 📈 Advanced Analytics
- **Content Performance Matrix**: Interaction patterns
- **User Cohort Analysis**: Beginner/Intermediate/Advanced distribution
- **Recommendation Accuracy**: Multi-dimensional quality metrics
- **AI Insights**: Automated trend detection and recommendations
- **Date Range Filtering**: Custom time periods

### 🎨 UI/UX Features
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Professional transitions and effects
- **Modern Design**: Gradient cards, shadows, and clean typography
- **Keyboard Shortcuts**: Enhanced productivity
- **Auto-refresh**: Data updates every 30 seconds

## 🗄️ Database Schema

### Users Table
```sql
- user_id (PK)
- name
- email
- cohort_tag (beginner, intermediate, advanced)
- skill_level
- interests (comma-separated tags)
- created_at
- last_active
```

### Content Table
```sql
- content_id (PK)
- title
- description
- content_type (video, article, course, etc.)
- difficulty
- tags
- duration_minutes
- popularity_score
- created_at
```

### Events Table
```sql
- event_id (PK)
- user_id (FK)
- content_id (FK)
- event_type (view, complete, like, etc.)
- value (for quiz scores)
- session_id
- timestamp
```

### Recommendation Logs
```sql
- log_id (PK)
- user_id
- content_id
- score
- model_version
- reason_tags
- timestamp
- clicked (boolean)
```

## 🔌 API Endpoints

### System
- `GET /` - API information
- `GET /health` - Health check with database stats
- `GET /analytics` - System-wide analytics

### Recommendations
- `GET /recommend/{user_id}` - Get personalized recommendations
  - Query params: `k` (number of recs), `strategy` (hybrid/collaborative/content_based)

### Events
- `POST /events` - Log a user event
- `GET /events/recent` - Get recent events

### Users
- `GET /users` - List users (paginated)
- `GET /analytics/user/{user_id}` - User-specific analytics

### Content
- `GET /content` - List content items
  - Query params: `difficulty`, `content_type`, `limit`, `offset`

### WebSocket
- `WS /ws` - Real-time event stream

## 📊 Sample Data

The system automatically generates:
- **100 users** with varied profiles and interests
- **200 content items** across multiple types and difficulties
- **5,000 events** spanning the last 30 days

## 🧪 Testing the System

### 1. Test Recommendations

```powershell
# Get recommendations for user_1
Invoke-WebRequest -Uri "http://localhost:8000/recommend/user_1?k=10&strategy=hybrid"
```

### 2. Log an Event

```powershell
$body = @{
    user_id = "user_1"
    content_id = "content_5"
    event_type = "complete"
    value = 95
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/events" -Method POST -Body $body -ContentType "application/json"
```

### 3. Get User Analytics

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/analytics/user/user_1"
```

## 🎨 Dashboard Navigation

### Overview Tab
- System statistics at a glance
- Event distribution donut chart
- 7-day engagement line chart
- Top 10 popular content
- Recent activity feed (last 10 events)

### Recommendations Tab
- Test recommendation engine
- Select user, strategy, and count
- View results with scores and reasons
- Beautiful card-based layout

### Users Tab
- Paginated user table
- Search functionality
- View individual analytics
- Event count per user

### Content Tab
- Grid view of all content
- Filter by type
- Search by title/description
- Popularity indicators

### Events Tab
- Live event stream (WebSocket)
- Real-time updates
- Event type indicators
- User and content context

### Analytics Tab
- Content performance bar chart
- User cohort pie chart
- Recommendation accuracy radar chart
- AI-generated insights
- Date range filtering

## 🎯 Recommendation Algorithm

### Two-Stage Approach

**Stage 1: Candidate Generation**
1. Content-based filtering (tag overlap with user interests)
2. Collaborative filtering (similar user preferences)
3. Popularity boost
4. Recency factor

**Stage 2: Scoring**
- Interest alignment: 30% weight
- Difficulty matching: 20% weight
- Popularity: 15% weight
- Collaborative signals: 20% weight
- Recency: 10% weight
- Exploration noise: 5% weight

### Explanation Tags
- `recommended_for_you` - General recommendation
- `popular_with_similar_users` - Collaborative signal
- Specific topic tags matching user interests

## 🔧 Configuration

All settings are in-memory for the local version. For production:

- **Database**: SQLite (`recommender.db`)
- **Port**: 8000
- **Host**: 0.0.0.0 (all interfaces)
- **WebSocket**: Automatic reconnection
- **Auto-refresh**: 30 seconds

## 📱 Responsive Design

The dashboard is fully responsive:
- **Desktop**: Full sidebar, multi-column grids
- **Tablet**: Collapsible sidebar, 2-column grids
- **Mobile**: Hidden sidebar (toggle), single-column layout

## 🌙 Dark Mode

Click the moon/sun icon in the sidebar footer to toggle themes. Theme preference is saved in localStorage.

## 🚀 Performance

- **SQLite**: Fast local database
- **Indexed Queries**: All foreign keys and timestamps indexed
- **Batch Processing**: Events logged in bulk
- **Chart Caching**: Charts update only when data changes
- **WebSocket**: Efficient real-time updates

## 🔒 Security Notes

⚠️ **This is a development version**. For production deployment:
- Add authentication/authorization
- Implement rate limiting
- Add input validation
- Use HTTPS/WSS
- Configure CORS properly
- Add SQL injection protection
- Implement API keys

## 📦 File Structure

```
Dhiksha/
├── app_full.py              # Main application (full featured)
├── recommender.db           # SQLite database (auto-created)
├── frontend/
│   ├── dashboard.html       # Main dashboard
│   ├── dashboard.css        # Styles (light + dark mode)
│   ├── dashboard.js         # Frontend logic
│   ├── index.html          # Simple demo (original)
│   ├── app.js              # Simple demo JS
│   └── styles.css          # Simple demo CSS
└── DASHBOARD_GUIDE.md      # This file
```

## 🎓 Learning Path

### For Beginners
1. Start with the Overview tab to understand system metrics
2. Test recommendations in the Recommendations tab
3. Explore the Content Library
4. Watch the Live Event Stream

### For Advanced Users
1. Experiment with recommendation strategies
2. Analyze user cohorts in Analytics
3. Use the API directly (`/docs`)
4. Monitor WebSocket messages in browser DevTools

## 🐛 Troubleshooting

### Database is empty
```powershell
# Delete database and restart
Remove-Item recommender.db
python app_full.py
```

### WebSocket not connecting
- Check browser console for errors
- Ensure port 8000 is not blocked
- Try refreshing the page

### Charts not displaying
- Ensure Chart.js CDN is accessible
- Check browser console for errors
- Try hard refresh (Ctrl+Shift+R)

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

## 🔮 Future Enhancements

- [ ] User authentication (OAuth2/JWT)
- [ ] Real ML models (TensorFlow/PyTorch)
- [ ] A/B testing framework
- [ ] Export analytics to CSV/Excel
- [ ] Email notifications
- [ ] Content upload interface
- [ ] Batch recommendation jobs
- [ ] Multi-language support
- [ ] Mobile app (React Native)

## 📞 Support

For issues or questions:
1. Check the API docs at `/docs`
2. Inspect browser console for errors
3. Check Python console output
4. Review this guide

## 🎉 Enjoy!

You now have a **production-ready recommendation system** with:
✅ Beautiful dashboard
✅ Real-time analytics
✅ Multiple recommendation strategies
✅ Live event tracking
✅ Dark mode
✅ Responsive design
✅ WebSocket support
✅ SQLite persistence

**Happy recommending! 🚀**
