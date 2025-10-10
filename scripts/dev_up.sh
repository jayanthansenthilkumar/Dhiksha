#!/bin/bash

# dev_up.sh - Start local development environment
# Usage: ./scripts/dev_up.sh

set -e

echo "🚀 Starting AI-Powered Learning Recommendation System (Local Dev)"
echo "================================================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "✅ Prerequisites OK"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/raw data/processed data/models
mkdir -p logs
mkdir -p monitoring/prometheus monitoring/grafana/dashboards monitoring/grafana/provisioning

# Start services
echo "🐳 Starting Docker Compose services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy (this may take 30-60 seconds)..."
sleep 10

# Check Postgres
echo "  Checking PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U admin -d recommendations &> /dev/null; then
        echo "  ✅ PostgreSQL ready"
        break
    fi
    sleep 2
done

# Check Redis
echo "  Checking Redis..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        echo "  ✅ Redis ready"
        break
    fi
    sleep 2
done

# Check MinIO
echo "  Checking MinIO..."
for i in {1..30}; do
    if curl -s http://localhost:9000/minio/health/live &> /dev/null; then
        echo "  ✅ MinIO ready"
        break
    fi
    sleep 2
done

# Check Milvus
echo "  Checking Milvus..."
for i in {1..30}; do
    if curl -s http://localhost:9091/healthz &> /dev/null; then
        echo "  ✅ Milvus ready"
        break
    fi
    sleep 2
done

# Create MinIO buckets
echo "🪣 Creating MinIO buckets..."
docker-compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker-compose exec -T minio mc mb -p local/learning-events
docker-compose exec -T minio mc mb -p local/learning-features
docker-compose exec -T minio mc mb -p local/mlflow-artifacts
echo "  ✅ Buckets created"

# Create Kafka topics
echo "📨 Creating Kafka topics..."
sleep 5  # Give Kafka time to fully start
docker-compose exec -T kafka kafka-topics --create --if-not-exists \
    --bootstrap-server localhost:9092 \
    --topic user-events \
    --partitions 3 \
    --replication-factor 1 || true
echo "  ✅ Kafka topics created"

echo ""
echo "✅ All services are up and running!"
echo ""
echo "📊 Service URLs:"
echo "  - MLflow:       http://localhost:5000"
echo "  - Grafana:      http://localhost:3000 (admin/admin)"
echo "  - Prometheus:   http://localhost:9090"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Prefect:      http://localhost:4200"
echo ""
echo "🔌 Database Connections:"
echo "  - PostgreSQL:   postgresql://admin:localdev@localhost:5432/recommendations"
echo "  - Redis:        redis://localhost:6379/0"
echo "  - Milvus:       localhost:19530"
echo "  - Kafka:        localhost:9092"
echo ""
echo "📝 Next Steps:"
echo "  1. Initialize database:       python scripts/init_db.py"
echo "  2. Generate sample data:      python scripts/sample_data_generator.py"
echo "  3. Train models:              python -m src.models.train_retrieval"
echo "  4. Start API server:          uvicorn src.api.main:app --reload"
echo ""
echo "To stop all services, run: ./scripts/dev_down.sh"
