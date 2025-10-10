# Quick Reference — Common Commands

## Local Development

### Start/Stop Services
```powershell
# Start all services
.\scripts\dev_up.ps1

# Stop all services
.\scripts\dev_down.ps1

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Database Operations
```powershell
# Initialize database
python scripts\init_db.py

# Generate sample data
python scripts\sample_data_generator.py --users 1000 --items 500 --events 10000

# Connect to PostgreSQL
docker-compose exec postgres psql -U admin -d recommendations

# Backup database
docker-compose exec postgres pg_dump -U admin recommendations > backup.sql

# Restore database
docker-compose exec -T postgres psql -U admin -d recommendations < backup.sql
```

### API Server
```powershell
# Start API (development mode with auto-reload)
uvicorn src.api.main:app --reload --port 8000

# Start API (production mode)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/recommend/user_123?k=10
curl -X POST http://localhost:8000/events -H "Content-Type: application/json" -d '{\"user_id\":\"user_123\",\"content_id\":\"content_456\",\"event_type\":\"view\"}'
```

### Model Training
```powershell
# Train retrieval model
python -m src.models.train_retrieval --epochs 10 --batch-size 256

# Train ranking model
python -m src.models.train_ranking --n-estimators 100 --max-depth 6

# Build Milvus index
python scripts\build_milvus_index.py
```

### Testing
```powershell
# Run all tests
pytest

# Run unit tests only
pytest tests/unit -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_api.py -v
```

### Code Quality
```powershell
# Format code
black src/ scripts/ tests/
isort src/ scripts/ tests/

# Lint code
flake8 src/ scripts/ tests/ --max-line-length=100

# Type check
mypy src/ --ignore-missing-imports
```

## Docker Commands

### Container Management
```powershell
# View running containers
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f mlflow

# Restart a service
docker-compose restart postgres

# Execute command in container
docker-compose exec postgres psql -U admin
docker-compose exec redis redis-cli
```

### Cleanup
```powershell
# Remove stopped containers
docker-compose rm

# Remove all unused images
docker system prune -a

# Remove all volumes
docker volume prune
```

## Monitoring

### Prometheus Queries
```
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Grafana
```
# Access Grafana
http://localhost:3000
Username: admin
Password: admin
```

### MLflow
```
# Access MLflow
http://localhost:5000

# List models via CLI
mlflow models list

# Promote model to production
mlflow models update-model-version --name retrieval_model --version 1 --stage Production
```

## Kubernetes (Future)

### Deploy to K8s
```bash
# Apply manifests
kubectl apply -f infra/kubernetes/base/

# Check deployments
kubectl get deployments -n production
kubectl get pods -n production

# View logs
kubectl logs -f deployment/fastapi-gateway -n production

# Rollout restart
kubectl rollout restart deployment/fastapi-gateway -n production

# Scale deployment
kubectl scale deployment/fastapi-gateway --replicas=5 -n production
```

### Helm (Future)
```bash
# Install chart
helm install learning-rec infra/helm/learning-recommender -n production

# Upgrade
helm upgrade learning-rec infra/helm/learning-recommender -n production

# Rollback
helm rollback learning-rec -n production
```

## Troubleshooting

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Docker Space Issues
```powershell
# Check disk usage
docker system df

# Clean up
docker system prune --volumes
```

### Database Connection Refused
```powershell
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

## Useful URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| API Docs | http://localhost:8000/docs | - |
| MLflow | http://localhost:5000 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Prefect | http://localhost:4200 | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |

## Environment Variables

See `.env.example` for all available variables. Key ones:

```
DATABASE_URL=postgresql://admin:localdev@localhost:5432/recommendations
REDIS_URL=redis://localhost:6379/0
MLFLOW_TRACKING_URI=http://localhost:5000
MILVUS_HOST=localhost
MILVUS_PORT=19530
EMBEDDING_DIM=128
TOP_K_RETRIEVAL=100
TOP_K_RANKING=10
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Commit with conventional commits
git commit -m "feat: add user embedding cache"
git commit -m "fix: correct Milvus connection timeout"

# Push and create PR
git push origin feature/my-feature
```

---

**For full documentation, see**:
- README.md (overview)
- ARCHITECTURE.md (system design)
- RUNBOOK.md (operations)
- MAINTENANCE.md (procedures)
- IMPLEMENTATION_STATUS.md (roadmap)
