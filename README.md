# AI-Powered Learning Recommendation System

**Production-grade personalized learning recommendation engine with real-time serving, model training pipelines, and full observability.**

[![CI/CD](https://github.com/yourorg/learning-recommender/workflows/CI/badge.svg)](https://github.com/yourorg/learning-recommender/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Mission

Deliver sub-200ms P95 personalized recommendations that increase learner engagement (CTR, time-on-content) over popularity baselines, with full reproducibility, observability, and GitOps-ready deployment.

## 📊 Success Metrics

- **Engagement Lift**: +15% CTR vs. popularity baseline
- **Latency**: P95 < 200ms (service-side)
- **Model Quality**: Precision@10 > 0.25, NDCG@10 > 0.40
- **Uptime**: 99.9% availability SLO

---

## 🏗️ Architecture at a Glance

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│ FastAPI      │─────▶│  BentoML    │
│   (SPA)     │      │  Gateway     │      │  Model      │
└─────────────┘      │ (Auth/Orch.) │      │  Server     │
                     └──────┬───────┘      └──────┬──────┘
                            │                     │
                     ┌──────▼───────┐      ┌──────▼──────┐
                     │  PostgreSQL  │      │   Milvus    │
                     │  (Metadata)  │      │   (ANN)     │
                     └──────────────┘      └─────────────┘
                            
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Kafka     │─────▶│   Prefect    │─────▶│   MLflow    │
│  (Events)   │      │  (ETL/Train) │      │  (Registry) │
└─────────────┘      └──────────────┘      └─────────────┘
```

**Components:**
- **Retrieval**: Two-tower dense embeddings (TensorFlow Recommenders)
- **Ranking**: XGBoost re-ranker on top-K candidates
- **Serving**: BentoML model server + FastAPI orchestration layer
- **Storage**: PostgreSQL (metadata), Milvus (vectors), S3/MinIO (events/models)
- **Orchestration**: Prefect (ETL/training), Kubernetes (deployment)
- **Observability**: Prometheus + Grafana + OpenTelemetry

---

## 🚀 Quick Start (Local Dev in 30 Minutes)

### Prerequisites

- **Docker** 20.10+ with docker-compose
- **Python** 3.11+
- **Make** (optional, for convenience commands)

### 1. Clone & Environment Setup

```bash
git clone https://github.com/yourorg/learning-recommender.git
cd learning-recommender

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Start Local Infrastructure

```bash
# Brings up: Postgres, Kafka, MinIO, Milvus, Redis, MLflow
./scripts/dev_up.sh

# Wait ~30 seconds for all services to be healthy
docker-compose ps
```

### 3. Initialize Database & Generate Sample Data

```bash
# Run migrations
python scripts/init_db.py

# Generate sample dataset (1000 users, 500 items, 10K events)
python scripts/sample_data_generator.py --users 1000 --items 500 --events 10000 --seed 42

# Upload to object store
python scripts/upload_events_to_storage.py
```

### 4. Train Models

```bash
# Train retrieval model (two-tower embeddings)
python -m src.models.train_retrieval --epochs 10 --batch-size 256

# Build ANN index
python scripts/build_milvus_index.py

# Train ranking model
python -m src.models.train_ranking --epochs 20

# Models are logged to MLflow (http://localhost:5000)
```

### 5. Start API Server

```bash
# Start FastAPI gateway
uvicorn src.api.main:app --reload --port 8000

# In another terminal, start BentoML model server
bentoml serve src/bentoml_service.py:svc --reload
```

### 6. Test Recommendations

```bash
# Get recommendations for user
curl http://localhost:8000/recommend/user_123?k=10

# Post an event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "content_id": "content_456",
    "event_type": "view",
    "value": 1.0,
    "ts": "2025-10-10T12:00:00Z"
  }'
```

### 7. View Dashboards

- **MLflow**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API Docs**: http://localhost:8000/docs

### 8. Run Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (requires running services)
pytest tests/integration -v

# Load tests
k6 run tests/load/recommend_load_test.js
```

### 9. Cleanup

```bash
./scripts/dev_down.sh
```

---

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/          # CI/CD pipelines
│       ├── ci.yml          # Lint, test, build
│       └── cd.yml          # Deploy to staging/prod
├── docs/
│   ├── ARCHITECTURE.md     # System design & diagrams
│   ├── RUNBOOK.md          # Incident response & operations
│   ├── MAINTENANCE.md      # Retrain schedules & SLAs
│   └── API.md              # OpenAPI spec & examples
├── infra/
│   ├── terraform/          # IaC for cloud resources
│   │   ├── aws/            # EKS, RDS, S3, VPC
│   │   └── gcp/            # GKE, CloudSQL, GCS
│   ├── kubernetes/         # K8s manifests
│   │   ├── base/           # Kustomize base
│   │   └── overlays/       # staging, production
│   └── helm/               # Helm charts
│       └── learning-recommender/
├── src/
│   ├── api/                # FastAPI gateway
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── middleware/     # Auth, logging, CORS
│   │   └── schemas.py      # Pydantic models
│   ├── models/
│   │   ├── retrieval/      # Two-tower TFRS model
│   │   ├── ranking/        # XGBoost ranker
│   │   ├── train_retrieval.py
│   │   └── train_ranking.py
│   ├── data/
│   │   ├── db/             # SQLAlchemy models
│   │   ├── schemas.py      # Data schemas
│   │   └── feature_engineering.py
│   ├── pipelines/          # Prefect flows
│   │   ├── ingestion.py
│   │   ├── feature_pipeline.py
│   │   └── training_pipeline.py
│   ├── serving/
│   │   ├── bentoml_service.py
│   │   └── model_loader.py
│   ├── search/
│   │   ├── milvus_client.py
│   │   └── faiss_index.py  # Fallback
│   ├── monitoring/
│   │   ├── metrics.py      # Prometheus metrics
│   │   ├── tracing.py      # OpenTelemetry
│   │   └── drift_detector.py
│   └── utils/
│       ├── auth.py         # JWT validation
│       ├── secrets.py      # Secrets manager
│       └── config.py       # Settings management
├── scripts/
│   ├── dev_up.sh
│   ├── dev_down.sh
│   ├── init_db.py
│   ├── sample_data_generator.py
│   ├── build_milvus_index.py
│   └── upload_events_to_storage.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
│       └── recommend_load_test.js
├── monitoring/
│   ├── grafana/
│   │   └── dashboards/
│   └── prometheus/
│       └── rules/
├── frontend/               # Minimal SPA demo
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml          # Black, isort, flake8 config
├── .pre-commit-config.yaml
├── CODEOWNERS
└── README.md
```

---

## 🔧 Configuration

Environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/recommendations

# Object Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=learning-events

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Auth
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# Feature Store
REDIS_URL=redis://localhost:6379/0

# Model Config
EMBEDDING_DIM=128
TOP_K_RETRIEVAL=100
TOP_K_RANKING=10
```

---

## 🧪 Testing Strategy

### Unit Tests
```bash
pytest tests/unit -v --cov=src --cov-report=html
```

### Integration Tests
```bash
# Requires docker-compose services running
pytest tests/integration -v -m "not slow"
```

### Load Tests
```bash
# Simulate 100 concurrent users
k6 run --vus 100 --duration 30s tests/load/recommend_load_test.js
```

**Pass Criteria:**
- Unit test coverage > 80%
- Integration tests pass with real services
- P95 latency < 200ms @ 100 concurrent users

---

## 🚢 Deployment

### Staging

```bash
# Build and push images
docker build -t your-registry/learning-rec-api:v1.0.0 -f Dockerfile .
docker push your-registry/learning-rec-api:v1.0.0

# Deploy via ArgoCD
kubectl apply -f infra/kubernetes/argocd/application-staging.yaml

# Or manual kubectl
kubectl apply -k infra/kubernetes/overlays/staging
```

### Production

```bash
# Terraform provision
cd infra/terraform/aws
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars

# Deploy with Helm
helm upgrade --install learning-rec infra/helm/learning-recommender \
  --namespace production \
  --values infra/helm/learning-recommender/values-prod.yaml

# Canary rollout (ArgoCD)
kubectl argo rollouts promote learning-rec-api -n production
```

---

## 📈 Observability

### Metrics (Prometheus)
- `recommend_request_duration_seconds` (histogram)
- `recommend_success_total` (counter)
- `model_score_mean` (gauge)
- `model_drift_score` (gauge)

### Dashboards (Grafana)
- **Service Health**: Latency, error rate, throughput
- **Model Performance**: Score distribution, precision/recall trends
- **Infrastructure**: CPU, memory, disk, network

### Alerts
- P95 latency > 300ms for 5 minutes
- Error rate > 2% for 10 minutes
- Model drift score > threshold

### Tracing (OpenTelemetry)
Distributed traces for recommendation request flow.

---

## 🔐 Security

- **Authentication**: JWT bearer tokens (RS256)
- **Authorization**: RBAC for admin endpoints (`/admin/*`)
- **Secrets**: AWS Secrets Manager / HashiCrypt Vault
- **TLS**: All endpoints enforce HTTPS in production
- **PII**: User IDs hashed; logs scrubbed
- **Data Retention**: 90-day event retention; opt-out enforcement

---

## 🔄 Model Lifecycle

### Training Cadence
- **Retrieval Model**: Weekly (Sunday 2 AM UTC)
- **Ranking Model**: Daily (2 AM UTC)
- **Index Rebuild**: Daily after ranking retrain

### Rollback Procedure
```bash
# List model versions
mlflow models list --name retrieval_model

# Promote previous version to production
mlflow models update-model-version \
  --name retrieval_model \
  --version 42 \
  --stage Production

# Redeploy
kubectl rollout restart deployment/bentoml-server -n production
```

### Experiment Tracking
All training runs logged to MLflow:
- Hyperparameters
- Metrics (precision@10, recall@10, NDCG@10)
- Artifacts (model weights, plots)
- Tags (experiment_id, git_commit)

---

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Deep dive into system design
- **[RUNBOOK.md](docs/RUNBOOK.md)**: Incident triage & troubleshooting
- **[MAINTENANCE.md](docs/MAINTENANCE.md)**: Retrain schedules, backups, DR
- **[API.md](docs/API.md)**: OpenAPI spec & usage examples

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Run pre-commit hooks: `pre-commit install && pre-commit run --all-files`
3. Write tests: `pytest tests/unit/test_your_feature.py`
4. Commit: `git commit -m "feat: add amazing feature"`
5. Push & open PR: `git push origin feature/amazing-feature`

See [CODEOWNERS](CODEOWNERS) for review assignments.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙌 Acknowledgments

Built with reverence for legacy workflows and a forward-thinking approach to modern ML systems. Iterate fast, ship small, scale with confidence.

**Tech Stack Love**:
- TensorFlow Recommenders, PyTorch, XGBoost
- FastAPI, BentoML, Prefect
- Kubernetes, ArgoCD, Terraform
- Prometheus, Grafana, OpenTelemetry
- PostgreSQL, Milvus, Redis, Kafka

---

**Questions?** Open an issue or reach out to the platform team.

**First deployment?** Read the [30-minute onboarding guide](docs/ONBOARDING.md).
