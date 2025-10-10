# dev_down.ps1 - Stop local development environment (Windows)
# Usage: .\scripts\dev_down.ps1

$ErrorActionPreference = "Stop"

Write-Host "🛑 Stopping AI-Powered Learning Recommendation System (Local Dev)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Stop and remove containers
Write-Host "🐳 Stopping Docker Compose services..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "✅ All services stopped" -ForegroundColor Green
Write-Host ""
Write-Host "💾 Data volumes preserved. To remove all data:" -ForegroundColor Yellow
Write-Host "   docker-compose down -v"
Write-Host ""
Write-Host "To start services again, run: .\scripts\dev_up.ps1" -ForegroundColor Cyan
