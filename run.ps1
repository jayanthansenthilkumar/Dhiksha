# Run the AI Learning Recommender System

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 79 -ForegroundColor Cyan
Write-Host "🚀 Starting AI Learning Recommender System" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 79 -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow

$requirementsMet = $true
try {
    python -c "import fastapi, uvicorn, pydantic" 2>&1 | Out-Null
    Write-Host "✅ All dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Dependencies not found. Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 79 -ForegroundColor Cyan
Write-Host "🎯 Application will be available at:" -ForegroundColor Green
Write-Host "   📊 Dashboard: http://localhost:8000/static/dashboard.html" -ForegroundColor Cyan
Write-Host "   📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   🔧 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 79 -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Change to backend directory and run
Set-Location backend
python app.py
