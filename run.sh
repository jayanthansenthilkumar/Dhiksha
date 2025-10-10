#!/bin/bash
# Run the AI Learning Recommender System (Unix/Mac/Linux)

echo "================================================================================"
echo "🚀 Starting AI Learning Recommender System"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found! Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Python found: $PYTHON_VERSION"

# Check if dependencies are installed
echo ""
echo "📦 Checking dependencies..."

if python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "✅ All dependencies installed"
else
    echo "⚠️  Dependencies not found. Installing..."
    pip3 install -r requirements.txt
fi

echo ""
echo "================================================================================"
echo "🎯 Application will be available at:"
echo "   📊 Dashboard: http://localhost:8000/static/dashboard.html"
echo "   📚 API Docs: http://localhost:8000/docs"
echo "   🔧 Health Check: http://localhost:8000/health"
echo "================================================================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Change to backend directory and run
cd backend
python3 app.py
