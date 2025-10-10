# Maintenance Playbook — AI-Powered Learning Recommendation System

**Version**: 1.0  
**Audience**: Platform engineers, ML engineers, SREs  
**Review Cadence**: Quarterly

---

## 1. Routine Maintenance Schedule

### 1.1 Daily Tasks (Automated)

| Task                     | Time (UTC) | Owner     | Command/Job                          |
|--------------------------|------------|-----------|--------------------------------------|
| Ranking model retrain    | 02:00      | CronJob   | `train-ranking-model`                |
| Milvus index rebuild     | 03:00      | CronJob   | `build-milvus-index`                 |
| Database backup          | 04:00      | AWS RDS   | Automated snapshot                   |
| Event data archival      | 05:00      | CronJob   | `archive-old-events`                 |
| Metrics export to S3     | 06:00      | CronJob   | `export-prometheus-metrics`          |

**Monitoring:**
- Check CronJob completion: `kubectl get jobs -n production --sort-by=.metadata.creationTimestamp | tail -10`
- Alerts sent to Slack `#platform-ops` on failure

---

### 1.2 Weekly Tasks

**Sunday 02:00 UTC — Retrieval Model Retrain**

```bash
# Automated via CronJob: train-retrieval-model
# Manual trigger if needed:
kubectl create job --from=cronjob/train-retrieval-model train-retrieval-$(date +%Y%m%d) -n production

# Monitor progress:
kubectl logs -f job/train-retrieval-$(date +%Y%m%d) -n production

# Validate metrics in MLflow:
# https://mlflow.learning-rec.com → Experiments → retrieval_training
```

**Expected Duration**: 2-3 hours  
**Success Criteria**:
- Job completes without errors
- NDCG@10 > 0.35 on validation set
- New model version tagged in MLflow registry

**Rollback if**:
- Metrics degrade > 10% from previous version
- Validation errors spike

---

**Monday 08:00 UTC — Database Maintenance**

```bash
# Connect to PostgreSQL pod
kubectl exec -it postgres-pod -n production -- psql -U admin -d recommendations

# Vacuum and analyze
VACUUM (VERBOSE, ANALYZE);

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Reindex if fragmentation > 30%
REINDEX TABLE events;
```

**Expected Duration**: 30 minutes  
**Impact**: Minimal (non-blocking VACUUM)

---

### 1.3 Monthly Tasks

**First Sunday of Month — Partition Management**

```bash
# Drop old event partitions (> 90 days)
# Example: October 2025 → Drop July 2025 partition

kubectl exec -it postgres-pod -n production -- psql -U admin -d recommendations << EOF
DROP TABLE IF EXISTS events_2025_07;
ALTER TABLE events DETACH PARTITION events_2025_07;
EOF

# Create new partition for next month (November 2025)
kubectl exec -it postgres-pod -n production -- psql -U admin -d recommendations << EOF
CREATE TABLE events_2025_11 PARTITION OF events
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
EOF
```

**Security Patch Review**

```bash
# Check for CVEs in dependencies
pip list --outdated
pip-audit

# Update non-breaking patches
pip install --upgrade <package>

# Rebuild Docker images
docker build -t learning-rec-api:v1.2.1 .
docker push learning-rec-api:v1.2.1

# Deploy to staging first
kubectl set image deployment/fastapi-gateway fastapi=learning-rec-api:v1.2.1 -n staging
# Monitor for 24 hours, then promote to production
```

---

### 1.4 Quarterly Tasks

**Model Performance Audit**

1. **Compare Model Versions**:
   - Pull metrics from MLflow for last 90 days
   - Plot precision@10, recall@10, NDCG@10 trends
   - Identify regressions

2. **A/B Test Analysis** (if running):
   - Compare engagement metrics: CTR, time-on-content, completion rate
   - Statistical significance test (t-test, p < 0.05)

3. **Cold Start Evaluation**:
   - Measure coverage for new users (< 7 days old)
   - Assess diversity of recommendations (Gini coefficient)

4. **Bias & Fairness Check**:
   - Slice metrics by cohort (e.g., premium vs. free users)
   - Ensure no cohort has degraded performance > 15%

**Infrastructure Review**

- Review autoscaling thresholds (HPA settings)
- Analyze cost reports (AWS Cost Explorer)
- Right-size instance types if over/under-provisioned
- Review secrets rotation (JWT keys, DB passwords)

**Documentation Update**

- Update README with any process changes
- Review and update RUNBOOK for new incident patterns
- Archive old post-mortems to `docs/archive/`

---

## 2. Data Retention & Archival

### 2.1 Event Data

**Retention Policy**:
- **Hot storage (PostgreSQL)**: 30 days
- **Warm storage (S3 Parquet)**: 90 days
- **Cold storage (S3 Glacier)**: 1 year
- **Purge**: After 1 year (or user opt-out)

**Archival Process** (Automated Daily):

```python
# scripts/archive_old_events.py
import boto3
from datetime import datetime, timedelta

cutoff_date = datetime.now() - timedelta(days=90)
s3 = boto3.client('s3')

# Move Parquet files to Glacier
response = s3.list_objects_v2(Bucket='learning-events', Prefix='events/')
for obj in response['Contents']:
    if obj['LastModified'] < cutoff_date:
        s3.copy_object(
            Bucket='learning-events',
            CopySource={'Bucket': 'learning-events', 'Key': obj['Key']},
            Key=obj['Key'],
            StorageClass='GLACIER'
        )
```

**Manual Retrieval from Glacier** (3-5 hours):

```bash
aws s3api restore-object \
  --bucket learning-events \
  --key events/year=2025/month=07/day=15/events.parquet \
  --restore-request Days=1,GlacierJobParameters={Tier=Standard}
```

---

### 2.2 Model Artifacts

**Retention Policy**:
- **MLflow Registry**: All versions retained indefinitely
- **BentoML Archives**: Last 10 versions per model
- **S3 Model Checkpoints**: Last 5 versions

**Cleanup Script** (Manual, Monthly):

```bash
# List old BentoML versions
bentoml list

# Delete old versions (keep last 10)
bentoml delete retrieval_model:v1.0.0
bentoml delete ranking_model:v2.3.0
```

---

### 2.3 Logs & Metrics

**Retention Policy**:
- **Application Logs (CloudWatch/ELK)**: 30 days
- **Prometheus Metrics**: 90 days (then aggregated to 1-hour resolution, kept 1 year)
- **Distributed Traces (Jaeger/Tempo)**: 7 days

**Prometheus Long-Term Storage**:

```yaml
# prometheus.yml
remote_write:
  - url: "https://thanos.company.com/api/v1/receive"
    queue_config:
      capacity: 10000
      max_samples_per_send: 5000
```

---

## 3. Backup & Disaster Recovery

### 3.1 Database Backups

**Automated (AWS RDS)**:
- **Frequency**: Daily at 04:00 UTC
- **Retention**: 30 days
- **Cross-Region Replication**: Enabled (us-west-2)

**Manual Snapshot** (Before Major Migration):

```bash
aws rds create-db-snapshot \
  --db-instance-identifier learning-rec-prod \
  --db-snapshot-identifier learning-rec-pre-migration-$(date +%Y%m%d)
```

**Restore Procedure**:

```bash
# Step 1: Create new instance from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier learning-rec-restored \
  --db-snapshot-identifier rds:learning-rec-prod-2025-10-10-04-00

# Step 2: Update DNS/config to point to new instance
kubectl edit configmap app-config -n production
# Update: DATABASE_URL=postgresql://...learning-rec-restored...

# Step 3: Restart API pods
kubectl rollout restart deployment/fastapi-gateway -n production

# Step 4: Validate data integrity
python scripts/validate_db.py
```

**RPO (Recovery Point Objective)**: 24 hours  
**RTO (Recovery Time Objective)**: 2 hours

---

### 3.2 Model Registry Backup

**MLflow Backend (PostgreSQL)**: Same as main DB backup

**Model Artifacts (S3)**:
- **Versioning**: Enabled on `learning-models` bucket
- **Cross-Region Replication**: Enabled to `us-west-2`

**Restore**:

```bash
# List versions
aws s3api list-object-versions --bucket learning-models --prefix models/retrieval_model/

# Restore specific version
aws s3api copy-object \
  --bucket learning-models \
  --copy-source learning-models/models/retrieval_model/v42/model.pkl?versionId=abc123 \
  --key models/retrieval_model/v42/model.pkl
```

---

### 3.3 Configuration Backup

**Kubernetes Manifests**:
- Stored in Git: `infra/kubernetes/`
- Auto-synced via ArgoCD
- Rollback: Revert Git commit + ArgoCD sync

**Secrets (External)**:
- AWS Secrets Manager: Automated backups
- Manual export (encrypted):

```bash
aws secretsmanager get-secret-value --secret-id prod/learning-rec/jwt-key > jwt-key-backup.json
gpg --encrypt --recipient admin@company.com jwt-key-backup.json
```

---

## 4. Model Retraining Workflow

### 4.1 Standard Retraining (Automated)

**Trigger**: CronJob schedule (daily/weekly)

**Steps**:
1. **Data Pull**: Load events from last 30 days (Parquet from S3)
2. **Feature Engineering**: Run Prefect flow `build_features`
3. **Train Model**: Execute `train_retrieval.py` or `train_ranking.py`
4. **Evaluate**: Compute metrics on holdout set
5. **Log to MLflow**: Save model, metrics, hyperparameters
6. **Promote to Staging**: If metrics pass threshold
7. **Manual Approval**: SRE/ML engineer promotes to Production
8. **Deploy**: ArgoCD triggers rollout of new BentoML service

**Metrics Thresholds for Auto-Promotion to Staging**:
- Retrieval: NDCG@10 > 0.35
- Ranking: Precision@10 > 0.25
- No critical errors during training

---

### 4.2 Emergency Retraining (Manual)

**When**: Data drift detected, major content catalog update, performance drop

```bash
# Step 1: Trigger training job
kubectl create job --from=cronjob/train-ranking-model emergency-train-$(date +%s) -n production

# Step 2: Monitor
kubectl logs -f job/emergency-train-<id> -n production

# Step 3: Validate in MLflow UI
# https://mlflow.learning-rec.com

# Step 4: Promote to Production (if validated)
mlflow models update-model-version \
  --name ranking_model \
  --version <new_version> \
  --stage Production

# Step 5: Restart model server
kubectl rollout restart deployment/bentoml-server -n production
kubectl rollout status deployment/bentoml-server -n production

# Step 6: Monitor metrics in Grafana for 1 hour
# Rollback if engagement drops or errors spike
```

---

### 4.3 Model Versioning Strategy

**Naming Convention**:
- `retrieval_model:v<major>.<minor>.<patch>`
  - Major: Architecture change (e.g., embedding dim 128→256)
  - Minor: Training data or hyperparameter change
  - Patch: Bug fix, no retraining

**Example**:
- `v1.0.0`: Initial two-tower model
- `v1.1.0`: Added user cohort feature
- `v1.1.1`: Fixed embedding normalization bug
- `v2.0.0`: Switched to three-tower (user, item, context)

**MLflow Stages**:
- `None`: Experimental, not validated
- `Staging`: Passed offline metrics, ready for A/B test
- `Production`: Serving live traffic
- `Archived`: Old version, kept for rollback

---

## 5. Index Maintenance (Milvus)

### 5.1 Daily Index Rebuild

**Automated via CronJob** (`build-milvus-index`):

```python
# scripts/build_milvus_index.py
from pymilvus import connections, Collection, utility
import mlflow

# Load item embeddings from retrieval model
model = mlflow.tensorflow.load_model("models:/retrieval_model/Production")
item_embeddings = model.item_model.predict(all_items)

# Connect to Milvus
connections.connect(host=MILVUS_HOST, port=19530)

# Drop old collection (if exists)
if utility.has_collection("content_embeddings"):
    utility.drop_collection("content_embeddings")

# Create collection
from pymilvus import FieldSchema, CollectionSchema, DataType
fields = [
    FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128)
]
schema = CollectionSchema(fields)
collection = Collection("content_embeddings", schema)

# Insert data
collection.insert([content_ids, item_embeddings])

# Build index
collection.create_index("embedding", {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}})
collection.load()
```

**Duration**: 10-15 minutes (for 10K items)  
**Downtime**: None (old collection active until new one loaded)

---

### 5.2 Incremental Updates (Hourly)

For new content added during the day:

```python
# Fetch new items (created in last hour)
new_items = db.query(Content).filter(Content.created_at > last_update).all()

# Generate embeddings
new_embeddings = model.item_model.predict(new_items)

# Insert into Milvus
collection.insert([new_item_ids, new_embeddings])
collection.flush()  # Persist
```

**Note**: No index rebuild needed; IVF_FLAT supports incremental insert.

---

## 6. Security & Compliance

### 6.1 Secrets Rotation

**JWT Signing Key**: Rotate every 90 days

```bash
# Generate new key
openssl rand -base64 32 > new-jwt-secret.txt

# Update in Secrets Manager
aws secretsmanager update-secret \
  --secret-id prod/learning-rec/jwt-key \
  --secret-string file://new-jwt-secret.txt

# Restart API (picks up new secret)
kubectl rollout restart deployment/fastapi-gateway -n production

# Old tokens valid until expiry (1 hour); new tokens use new key
```

**Database Password**: Rotate every 6 months (coordinated outage window)

---

### 6.2 PII & GDPR Compliance

**User Opt-Out**:

```sql
-- Mark user for deletion
UPDATE users SET deleted_at = NOW() WHERE user_id = '<user_uuid>';

-- Purge events (soft delete)
UPDATE events SET deleted = TRUE WHERE user_id = '<user_uuid>';

-- Exclude from training data (filter in ETL)
SELECT * FROM events WHERE deleted = FALSE;
```

**Data Export** (User request):

```bash
# Export user data
python scripts/export_user_data.py --user-id <uuid> --output user_data.json

# Package includes: profile, events, recommendations history
```

**Audit Log**:
- All admin actions logged to CloudTrail / ELK
- Retention: 1 year

---

## 7. Capacity Planning

### 7.1 Current Capacity (as of 2025-10-10)

| Resource            | Current | Max Safe | Scale Trigger          |
|---------------------|---------|----------|------------------------|
| API Pods            | 4       | 20       | CPU > 70% sustained    |
| Model Server Pods   | 2       | 10       | Request queue > 50     |
| PostgreSQL (RDS)    | 100 GB  | 500 GB   | > 80% disk usage       |
| Milvus (items)      | 10K     | 1M       | Query latency > 50ms   |
| Redis (cache)       | 2 GB    | 16 GB    | Eviction rate > 10/sec |

### 7.2 Growth Projections

**Assumptions**:
- User growth: 20% QoQ
- Events/user: 50/day (steady)

**6-Month Forecast (April 2026)**:
- Users: 1,000 → 2,500
- Events/day: 50K → 125K
- Recommendations/day: 10K → 25K

**Scaling Actions Needed**:
- Increase RDS storage to 200 GB (Q1 2026)
- Add 2 more API pods (autoscale max → 25)
- Upgrade Milvus to distributed mode if items > 100K

---

## 8. Deprecation & Sunsetting

### 8.1 Feature Deprecation Process

1. **Announce**: 90-day notice to stakeholders
2. **Mark Deprecated**: Add warnings in API responses
3. **Monitor Usage**: Track calls to deprecated endpoints
4. **Remove**: After usage < 1% for 30 days
5. **Document**: Update API docs and CHANGELOG

**Example**:
```json
{
  "deprecated": true,
  "message": "This endpoint will be removed on 2026-01-15. Use /v2/recommend instead.",
  "sunset_date": "2026-01-15"
}
```

---

### 8.2 Model Sunsetting

**Archive old models**:
```bash
# Archive in MLflow (move from Production → Archived)
mlflow models update-model-version \
  --name retrieval_model \
  --version 10 \
  --stage Archived

# Delete from BentoML (if > 6 months old and no active references)
bentoml delete retrieval_model:v1.0.0
```

---

## 9. Contacts & Ownership

| Area                  | Owner                 | Backup                |
|-----------------------|-----------------------|-----------------------|
| Model Training        | Bob (ML Engineer)     | Alice (Platform Lead) |
| Infrastructure        | Carol (SRE)           | Dave (DevOps)         |
| Database              | Eve (DBA)             | Carol (SRE)           |
| Security              | Frank (SecOps)        | Alice (Platform Lead) |

**Slack Channels**:
- `#platform-ops`: Day-to-day operations
- `#ml-engineering`: Model experiments, metrics
- `#incidents`: Active incident coordination

---

## 10. Changelog

| Date       | Change                                  | Author |
|------------|-----------------------------------------|--------|
| 2025-10-10 | Initial version                         | Alice  |
| 2025-10-15 | Added Milvus incremental update process | Bob    |

---

**Last Review**: 2025-10-10  
**Next Review**: 2026-01-10
