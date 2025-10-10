# System Architecture — AI-Powered Learning Recommendation System

**Version**: 1.0  
**Last Updated**: 2025-10-10  
**Audience**: Engineering team, SREs, new hires

---

## 1. Overview

This document describes the architecture of the AI-Powered Learning Recommendation System, a production-grade service that delivers personalized content recommendations with sub-200ms latency.

### 1.1 Design Principles

- **Modularity**: Each component (retrieval, ranking, serving) is independently deployable
- **Reproducibility**: All training is versioned and tracked in MLflow
- **Observability**: Full instrumentation with metrics, logs, traces
- **Scalability**: Horizontal scaling for stateless components
- **Privacy-first**: PII hashing, GDPR-compliant opt-outs

---

## 2. System Context Diagram

```
┌────────────────────────────────────────────────────────────┐
│                   External Systems                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  Client  │  │ Learning │  │  Admin   │                │
│  │   App    │  │  Portal  │  │  Panel   │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
└───────┼────────────┼─────────────┼──────────────────────┘
        │            │             │
        ▼            ▼             ▼
┌────────────────────────────────────────────────────────────┐
│                  API Gateway Layer                         │
│  ┌────────────────────────────────────────────────────┐   │
│  │            FastAPI Gateway (with Auth)             │   │
│  │  /recommend  /events  /admin/train  /admin/reindex│   │
│  └───────┬────────────┬───────────────┬───────────────┘   │
└──────────┼────────────┼───────────────┼────────────────────┘
           │            │               │
    ┌──────▼──────┐  ┌──▼────────┐  ┌──▼───────────┐
    │   BentoML   │  │ PostgreSQL│  │   Prefect    │
    │   Model     │  │ Metadata  │  │ Orchestrator │
    │   Server    │  │    DB     │  │  (Jobs)      │
    └──────┬──────┘  └───────────┘  └──────────────┘
           │
    ┌──────▼──────────────────────┐
    │  Milvus (Vector Search)      │
    │  FAISS (Fallback/Local)      │
    └──────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    Data Layer                              │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐      │
│  │  Kafka  │  │ MinIO/  │  │ Redis  │  │  MLflow  │      │
│  │ (Events)│  │   S3    │  │(Cache) │  │(Registry)│      │
│  └─────────┘  └─────────┘  └────────┘  └──────────┘      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              Observability & Operations                    │
│  ┌──────────┐  ┌─────────┐  ┌─────────────────────┐      │
│  │Prometheus│  │ Grafana │  │ OpenTelemetry       │      │
│  │ (Metrics)│  │(Dashbrd)│  │ (Distributed Trace) │      │
│  └──────────┘  └─────────┘  └─────────────────────┘      │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 FastAPI Gateway

**Responsibilities:**
- Request authentication (JWT)
- Request routing and orchestration
- Rate limiting
- Response formatting
- Logging & metrics emission

**Key Endpoints:**
```
GET  /recommend/{user_id}?k=10
POST /events
POST /admin/train          (auth: admin)
POST /admin/reindex        (auth: admin)
GET  /health
GET  /metrics
```

**Tech Stack:**
- FastAPI 0.104+
- Pydantic for validation
- Prometheus client for metrics
- OpenTelemetry for tracing

**Horizontal Scaling:**
- Stateless; can run N replicas behind load balancer
- Target: 4 replicas in production

---

### 3.2 BentoML Model Server

**Responsibilities:**
- Load serialized models (retrieval + ranking)
- Execute inference
- Handle model versioning via MLflow registry

**Model Loading:**
```python
# Retrieval: two-tower embeddings
retrieval_model = mlflow.tensorflow.load_model("models:/retrieval_model/Production")

# Ranking: XGBoost
ranking_model = mlflow.xgboost.load_model("models:/ranking_model/Production")
```

**Inference Flow:**
1. Receive user_id + context from gateway
2. Generate user embedding (retrieval model)
3. Query Milvus for top-K similar items (K=100)
4. Re-rank candidates with ranking model
5. Return top-N (N=10)

**Scaling:**
- GPU optional for retrieval model (CPU sufficient for XGBoost)
- Autoscale based on request queue depth

---

### 3.3 Retrieval Model (Two-Tower)

**Architecture:**
```
User Tower                     Item Tower
─────────────                  ─────────────
user_id                        content_id
user_cohort                    tags[]
recent_content_ids[5]          difficulty
    │                              │
    ▼                              ▼
[Embedding Layer]              [Embedding Layer]
    │                              │
    ▼                              ▼
[Dense 256]                    [Dense 256]
    │                              │
    ▼                              ▼
[Dense 128] ◀───────────────────▶ [Dense 128]
    │                              │
    └──────────── L2 ──────────────┘
              Contrastive Loss
```

**Inputs:**
- User: `user_id`, `cohort_tag`, `recent_content_ids` (last 5)
- Item: `content_id`, `tags`, `difficulty`, `content_age_days`

**Output:**
- 128-dimensional embeddings for users and items

**Training:**
- Framework: TensorFlow Recommenders (TFRS)
- Loss: Sampled softmax with in-batch negatives
- Batch size: 256
- Optimizer: Adam (lr=0.001)
- Epochs: 10-20
- Data: All user-item interactions (views, completes, likes)

**Evaluation Metrics:**
- Precision@10, Recall@10, NDCG@10 on holdout set

---

### 3.4 Ranking Model

**Architecture:**
```
Input Features (per candidate):
- user_embedding[128]
- item_embedding[128]
- recency_hours
- item_popularity_score
- time_of_day_hour
- session_position
- user_item_affinity (dot product)
    │
    ▼
[XGBoost Gradient Boosting]
 - 100 estimators
 - max_depth=6
 - learning_rate=0.1
    │
    ▼
relevance_score (0-1)
```

**Training:**
- Positives: viewed items with engagement (complete=1, view=0.5)
- Negatives: random sampling from non-interacted items
- 5-fold cross-validation
- Early stopping on validation AUC

**Feature Engineering:**
- User/item embeddings from retrieval model (frozen)
- Derived features: recency, popularity percentile, time features
- Cached in Redis for low-latency lookup

---

### 3.5 Vector Search (Milvus)

**Collection Schema:**
```python
{
  "name": "content_embeddings",
  "fields": [
    {"name": "content_id", "type": "VARCHAR", "max_length": 64, "is_primary": True},
    {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 128},
    {"name": "created_at", "type": "INT64"}  # Unix timestamp
  ],
  "index": {
    "type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128}
  }
}
```

**Index Build Process:**
1. Export item embeddings from retrieval model
2. Batch insert into Milvus (chunk size: 1000)
3. Build IVF_FLAT index (nlist=128 for ~10K items)
4. Load index to memory

**Query:**
```python
results = milvus_client.search(
    collection_name="content_embeddings",
    data=[user_embedding],
    limit=100,
    param={"nprobe": 10}
)
```

**Update Cadence:**
- Full rebuild: Daily (2 AM UTC)
- Incremental: New content added hourly

**Fallback:**
- FAISS in-memory index for local dev / small-scale

---

### 3.6 Data Storage

#### PostgreSQL (Metadata)

**Tables:**

```sql
-- Users
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    cohort_tag TEXT,
    last_active_at TIMESTAMP
);

-- Contents
CREATE TABLE contents (
    content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    type VARCHAR(20) CHECK (type IN ('video', 'article', 'quiz')),
    tags TEXT[],
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Events (hot; partitioned by month)
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    content_id UUID NOT NULL REFERENCES contents(content_id),
    event_type VARCHAR(20) CHECK (event_type IN ('view', 'complete', 'like', 'quiz_score')),
    value FLOAT,
    ts TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (ts);

CREATE INDEX idx_events_user_ts ON events(user_id, ts DESC);
CREATE INDEX idx_events_content_ts ON events(content_id, ts DESC);
```

#### Object Storage (S3/MinIO)

**Buckets:**
- `learning-events`: Raw event Parquet files (partitioned by date: `events/year=2025/month=10/day=10/`)
- `learning-models`: Exported model artifacts (before MLflow)
- `learning-features`: Offline feature snapshots (Parquet)

**Retention:**
- Raw events: 90 days
- Aggregated features: 1 year
- Model artifacts: Indefinite (MLflow manages)

#### Redis (Online Feature Cache)

**Keys:**
```
user:{user_id}:recent_items    # List[content_id], TTL=1h
user:{user_id}:embedding       # bytes (128 floats), TTL=24h
item:{content_id}:popularity   # float, TTL=6h
```

---

### 3.7 ETL & Training Pipelines (Prefect)

**Flow 1: Event Ingestion**
```python
@flow(name="ingest_events")
def ingest_events():
    events = consume_kafka_topic("user-events")
    df = to_dataframe(events)
    write_parquet(df, f"s3://learning-events/date={today()}/")
    upsert_to_postgres(df)  # Hot events table
```

**Flow 2: Feature Engineering**
```python
@flow(name="build_features")
def build_features():
    raw = read_parquet("s3://learning-events/date=*/")
    features = engineer_features(raw)  # Aggregations, windows
    write_parquet(features, "s3://learning-features/")
    cache_to_redis(features)  # Online features
```

**Flow 3: Model Training**
```python
@flow(name="train_retrieval_model")
def train_retrieval():
    train_data, val_data = load_splits()
    model = TwoTowerModel(embedding_dim=128)
    model.fit(train_data, epochs=10)
    metrics = evaluate(model, val_data)
    mlflow.log_metrics(metrics)
    mlflow.tensorflow.log_model(model, "retrieval_model")
    register_model_version("retrieval_model", stage="Staging")
```

**Schedule:**
- `ingest_events`: Every 5 minutes
- `build_features`: Hourly
- `train_retrieval`: Weekly (Sunday 2 AM)
- `train_ranking`: Daily (2 AM)

---

## 4. Request Flow Sequence Diagrams

### 4.1 Recommendation Request

```
Client              FastAPI         BentoML         Milvus        Redis       Postgres
  │                   │               │               │             │             │
  ├─GET /recommend──▶│               │               │             │             │
  │                   ├─validate JWT─┤               │             │             │
  │                   ├─fetch user───┼───────────────┼─────────────┼────────────▶│
  │                   │◀──user_data──┼───────────────┼─────────────┼─────────────┤
  │                   ├─get cached───┼───────────────┼─────────────▶│             │
  │                   │ recent_items │               │             │             │
  │                   │◀─items───────┼───────────────┼─────────────┤             │
  │                   ├─infer────────▶│               │             │             │
  │                   │ user_emb     │──embed_user──▶│             │             │
  │                   │               │◀─embedding────┤             │             │
  │                   │               │──search ANN──▶│             │             │
  │                   │               │◀─top_100──────┤             │             │
  │                   │               │──rank─────────┤             │             │
  │                   │               │◀─top_10───────┤             │             │
  │                   │◀─results──────┤               │             │             │
  │                   ├─format & log─┤               │             │             │
  │◀──recommendations─┤               │               │             │             │
```

**Latency Budget:**
- Auth & validation: 5ms
- DB lookup: 10ms
- Redis cache: 5ms
- Model inference: 80ms (retrieval 50ms + ranking 30ms)
- Milvus ANN: 30ms
- Total target: ~130ms (buffer to 200ms P95)

---

### 4.2 Event Ingestion

```
Client          FastAPI      Kafka       Prefect     S3/MinIO    Postgres
  │               │            │           │            │           │
  ├─POST /events─▶│            │           │            │           │
  │               ├─validate───┤           │            │           │
  │               ├─publish────▶│           │            │           │
  │◀─202 Accepted─┤            │           │            │           │
  │               │            │           │            │           │
  │               │            ├─consume───▶│           │           │
  │               │            │           ├─batch─────▶│           │
  │               │            │           │ (Parquet)  │           │
  │               │            │           ├─upsert─────┼──────────▶│
  │               │            │           │            │           │
```

**Notes:**
- Asynchronous: API returns 202 immediately
- Kafka retention: 7 days
- Parquet partitioned by date for efficient scans

---

### 4.3 Model Training & Deployment

```
Scheduler    Prefect      S3       MLflow     BentoML    ArgoCD     K8s
   │           │          │          │           │          │         │
   ├─trigger──▶│          │          │           │          │         │
   │          ├─load data─▶│          │           │          │         │
   │          │◀─Parquet───┤          │           │          │         │
   │          ├─train model┤          │           │          │         │
   │          ├─evaluate───┤          │           │          │         │
   │          ├─log metrics┼─────────▶│           │          │         │
   │          ├─log model──┼─────────▶│ (register)│          │         │
   │          ├─promote────┼─────────▶│ Staging→Prod│        │         │
   │          ├─build Bento┼──────────┼──────────▶│          │         │
   │          ├─push image─┼──────────┼───────────┼─────────▶│         │
   │          │            │          │           │         ├─sync────▶│
   │          │            │          │           │         │ (rollout)│
   │          │            │          │           │         │◀─ready───┤
```

**Approval Gate:**
- Staging deploy: Automatic
- Production deploy: Manual approval in ArgoCD UI

---

## 5. Data Flow

### 5.1 Training Data Pipeline

```
Events (Kafka)
   │
   ▼
[Raw Parquet on S3]
   │
   ▼
[Feature Engineering (Prefect)]
   │
   ├─▶ User aggregates: total_views, avg_completion_rate, favorite_tags
   ├─▶ Item aggregates: popularity_score, recent_engagement
   └─▶ Interaction matrix (user × item)
   │
   ▼
[Feature Store (Parquet + Redis)]
   │
   ▼
[Model Training (Prefect → TensorFlow/XGBoost)]
   │
   ▼
[MLflow Model Registry]
   │
   ▼
[BentoML Service + Milvus Index]
```

### 5.2 Serving Data Flow

```
User Request
   │
   ▼
[FastAPI: user_id + context]
   │
   ├─▶ Postgres: Fetch user metadata
   ├─▶ Redis: Fetch cached recent_items, user_embedding
   │
   ▼
[BentoML: Generate user_embedding if not cached]
   │
   ▼
[Milvus: ANN search for top-K items]
   │
   ▼
[BentoML: Re-rank with ranking model]
   │
   ▼
[FastAPI: Format response, emit metrics]
   │
   ▼
Client Response
```

---

## 6. Deployment Architecture (Kubernetes)

### 6.1 Cluster Layout

```
Namespace: production
├── Deployments
│   ├── fastapi-gateway (4 replicas, HPA: 4-20)
│   ├── bentoml-server (2 replicas, HPA: 2-10)
│   ├── prefect-agent (1 replica)
│   ├── mlflow-server (1 replica)
│   └── milvus (StatefulSet, 1 replica)
├── Services
│   ├── fastapi-gateway (LoadBalancer)
│   ├── bentoml-server (ClusterIP)
│   ├── postgres (ClusterIP → RDS endpoint)
│   ├── redis (ClusterIP → ElastiCache endpoint)
│   └── kafka (ClusterIP → MSK endpoint)
├── Ingress
│   └── nginx-ingress (TLS, rate limit)
├── ConfigMaps
│   ├── app-config
│   └── model-config
└── Secrets
    ├── db-credentials
    ├── jwt-secret
    └── s3-credentials

Namespace: monitoring
├── Prometheus (StatefulSet)
├── Grafana (Deployment)
└── OpenTelemetry Collector (DaemonSet)
```

### 6.2 Autoscaling

**HPA (Horizontal Pod Autoscaler):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-gateway
  minReplicas: 4
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
Client
  │
  ├─1. Request with JWT in Authorization header
  │    "Authorization: Bearer <jwt_token>"
  ▼
FastAPI Middleware (auth.py)
  │
  ├─2. Validate JWT signature (RS256)
  │    - Check expiry
  │    - Verify issuer
  ▼
  ├─3. Extract user_id & roles from claims
  │
  ├─4. Check RBAC for endpoint
  │    - /recommend/* → authenticated users
  │    - /admin/* → role=admin
  ▼
Route Handler
```

**JWT Payload:**
```json
{
  "sub": "user_12345",
  "exp": 1728594000,
  "iat": 1728507600,
  "roles": ["user"],
  "cohort": "premium"
}
```

### 7.2 Secrets Management

**AWS Secrets Manager (Production):**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

db_creds = get_secret('prod/learning-rec/db')
jwt_secret = get_secret('prod/learning-rec/jwt-key')
```

**Local Dev (Environment Variables):**
```bash
export DATABASE_URL="postgresql://..."
export JWT_SECRET_KEY="local-dev-key"
```

### 7.3 PII Handling

- **User IDs**: Hashed before storage in logs/analytics
- **Events**: No free-text fields allowed
- **Opt-out**: Soft-delete flag in `users` table; excluded from training

---

## 8. Disaster Recovery & High Availability

### 8.1 Database

- **RDS Multi-AZ**: Automatic failover
- **Backups**: Automated daily snapshots (retention: 30 days)
- **Point-in-time recovery**: Up to 35 days

### 8.2 Model Registry

- **MLflow Backend**: PostgreSQL (same as metadata DB)
- **Artifacts**: S3 with versioning enabled
- **Replication**: Cross-region replication for S3 bucket

### 8.3 Rollback Procedures

**Bad Model Deployment:**
```bash
# Step 1: Identify last known good version
mlflow models list --name retrieval_model

# Step 2: Promote to Production
mlflow models update-model-version \
  --name retrieval_model \
  --version 42 \
  --stage Production

# Step 3: Restart model server
kubectl rollout restart deployment/bentoml-server -n production
kubectl rollout status deployment/bentoml-server -n production

# Step 4: Verify metrics
curl http://localhost:8000/recommend/test_user_123?k=10
```

**Database Corruption:**
```bash
# Restore from latest snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier learning-rec-restored \
  --db-snapshot-identifier rds:learning-rec-2025-10-10

# Update DNS/endpoints
# Run data consistency checks
```

---

## 9. Performance & Scalability

### 9.1 Latency Breakdown (Target)

| Component            | Target (ms) | P95 (ms) |
|----------------------|-------------|----------|
| Auth validation      | 5           | 10       |
| DB metadata fetch    | 10          | 20       |
| Redis cache          | 5           | 10       |
| Retrieval model      | 50          | 80       |
| Milvus ANN search    | 30          | 50       |
| Ranking model        | 30          | 40       |
| Response formatting  | 5           | 10       |
| **Total**            | **135**     | **200**  |

### 9.2 Throughput

- **Concurrent Users**: 1,000+
- **Requests/sec**: 500 (peak), 200 (sustained)
- **Daily Events**: 1M+

### 9.3 Scaling Strategy

**Vertical:**
- BentoML pods: 4 CPU, 8GB RAM (CPU-optimized for XGBoost)
- FastAPI pods: 2 CPU, 4GB RAM

**Horizontal:**
- Stateless services: HPA on CPU + custom metrics (request rate)
- Milvus: Single instance initially; shard when > 1M items

**Data:**
- Partition PostgreSQL events table by month
- Archive old events to S3 Glacier after 90 days

---

## 10. Technology Stack Summary

| Layer               | Technology                    | Justification                          |
|---------------------|-------------------------------|----------------------------------------|
| API Gateway         | FastAPI                       | Async, type-safe, OpenAPI auto-gen    |
| Model Serving       | BentoML                       | Model packaging, multi-framework       |
| Retrieval Model     | TensorFlow Recommenders (TFRS)| Purpose-built for two-tower RecSys     |
| Ranking Model       | XGBoost                       | Fast inference, interpretable          |
| Vector Search       | Milvus                        | Production ANN, horizontal scaling     |
| Metadata DB         | PostgreSQL                    | ACID, mature, partitioning support     |
| Object Storage      | S3 / MinIO                    | Durable, cheap, Parquet-optimized      |
| Feature Cache       | Redis                         | Sub-ms latency, simple KV              |
| Event Stream        | Kafka                         | Durable, scalable, replay capability   |
| Orchestration       | Prefect                       | Python-native, modern UI, easy debug   |
| ML Lifecycle        | MLflow                        | Model registry, experiment tracking    |
| Container Runtime   | Docker + Kubernetes           | Industry standard, ecosystem           |
| CI/CD               | GitHub Actions + ArgoCD       | GitOps, auditable, declarative         |
| Monitoring          | Prometheus + Grafana          | De facto standard, rich ecosystem      |
| Tracing             | OpenTelemetry                 | Vendor-neutral, distributed tracing    |
| IaC                 | Terraform                     | Multi-cloud, state management          |

---

## 11. Future Enhancements (Roadmap)

### Phase 2 (Q1 2026)
- **Online Learning**: Real-time model updates with streaming data
- **Multi-Armed Bandits**: Exploration/exploitation for cold-start
- **A/B Testing Framework**: Statistical rigor for model experiments

### Phase 3 (Q2 2026)
- **Personalized Embeddings**: User-specific fine-tuning
- **Multi-Objective Ranking**: Balance engagement, diversity, novelty
- **Graph Neural Networks**: Leverage content co-occurrence graph

### Phase 4 (Q3 2026)
- **Cross-Platform Recommendations**: Mobile app, email, push
- **LLM Integration**: Natural language explanations for recommendations
- **Federated Learning**: Privacy-preserving training on user devices

---

## 12. References

- [TensorFlow Recommenders Docs](https://www.tensorflow.org/recommenders)
- [Milvus Architecture](https://milvus.io/docs/architecture_overview.md)
- [BentoML Serving Guide](https://docs.bentoml.org/)
- [Prefect Orchestration](https://docs.prefect.io/)
- [MLflow Model Registry](https://www.mlflow.org/docs/latest/model-registry.html)

---

**Maintained by**: Platform Engineering Team  
**Review Cadence**: Quarterly  
**Change Log**: See `docs/CHANGELOG.md`
