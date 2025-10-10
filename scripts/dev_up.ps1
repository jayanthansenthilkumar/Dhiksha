# dev_up.ps1 - Start local development environment (Windows)
# Usage: .\scripts\dev_up.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting AI-Powered Learning Recommendation System (Local Dev)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose not found. Please install docker-compose." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites OK" -ForegroundColor Green
Write-Host ""

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path data\raw, data\processed, data\models | Out-Null
New-Item -ItemType Directory -Force -Path logs | Out-Null
New-Item -ItemType Directory -Force -Path monitoring\prometheus, monitoring\grafana\dashboards, monitoring\grafana\provisioning | Out-Null

# Start services
Write-Host "🐳 Starting Docker Compose services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy (this may take 30-60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check Postgres
Write-Host "  Checking PostgreSQL..." -ForegroundColor Gray
for ($i = 1; $i -le 30; $i++) {
    try {
        docker-compose exec -T postgres pg_isready -U admin -d recommendations 2>&1 | Out-Null
        Write-Host "  ✅ PostgreSQL ready" -ForegroundColor Green
        break
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

# Check Redis
Write-Host "  Checking Redis..." -ForegroundColor Gray
for ($i = 1; $i -le 30; $i++) {
    try {
        docker-compose exec -T redis redis-cli ping 2>&1 | Out-Null
        Write-Host "  ✅ Redis ready" -ForegroundColor Green
        break
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

# Check MinIO
Write-Host "  Checking MinIO..." -ForegroundColor Gray
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ MinIO ready" -ForegroundColor Green
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

# Check Milvus
Write-Host "  Checking Milvus..." -ForegroundColor Gray
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9091/healthz" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ Milvus ready" -ForegroundColor Green
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

# Create MinIO buckets
Write-Host "🪣 Creating MinIO buckets..." -ForegroundColor Yellow
docker-compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>&1 | Out-Null
docker-compose exec -T minio mc mb -p local/learning-events 2>&1 | Out-Null
docker-compose exec -T minio mc mb -p local/learning-features 2>&1 | Out-Null
docker-compose exec -T minio mc mb -p local/mlflow-artifacts 2>&1 | Out-Null
Write-Host "  ✅ Buckets created" -ForegroundColor Green

# Create Kafka topics
Write-Host "📨 Creating Kafka topics..." -ForegroundColor Yellow
Start-Sleep -Seconds 5  # Give Kafka time to fully start
docker-compose exec -T kafka kafka-topics --create --if-not-exists `
    --bootstrap-server localhost:9092 `
    --topic user-events `
    --partitions 3 `
    --replication-factor 1 2>&1 | Out-Null
Write-Host "  ✅ Kafka topics created" -ForegroundColor Green

Write-Host ""
Write-Host "✅ All services are up and running!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Service URLs:" -ForegroundColor Cyan
Write-Host "  - MLflow:        http://localhost:5000"
Write-Host "  - Grafana:       http://localhost:3000 (admin/admin)"
Write-Host "  - Prometheus:    http://localhost:9090"
Write-Host "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
Write-Host "  - Prefect:       http://localhost:4200"
Write-Host ""
Write-Host "🔌 Database Connections:" -ForegroundColor Cyan
Write-Host "  - PostgreSQL:    postgresql://admin:localdev@localhost:5432/recommendations"
Write-Host "  - Redis:         redis://localhost:6379/0"
Write-Host "  - Milvus:        localhost:19530"
Write-Host "  - Kafka:         localhost:9092"
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Initialize database:       python scripts\init_db.py"
Write-Host "  2. Generate sample data:      python scripts\sample_data_generator.py"
Write-Host "  3. Train models:              python -m src.models.train_retrieval"
Write-Host "  4. Start API server:          uvicorn src.api.main:app --reload"
Write-Host ""
Write-Host "To stop all services, run: .\scripts\dev_down.ps1" -ForegroundColor Yellow
