# Runbook — AI-Powered Learning Recommendation System

**Version**: 1.0  
**Audience**: On-call engineers, SREs, DevOps  
**Emergency Contact**: platform-oncall@company.com

---

## 1. Service Overview

**Purpose**: Real-time personalized learning content recommendations  
**SLO**: 99.9% uptime, P95 latency < 200ms  
**Dependencies**: PostgreSQL (RDS), Milvus, Redis, S3, MLflow

---

## 2. Quick Health Checks

### 2.1 Check All Services

```bash
# K8s cluster health
kubectl get nodes
kubectl get pods -n production
kubectl get pods -n monitoring

# API health
curl https://api.learning-rec.com/health

# Expected: {"status": "healthy", "timestamp": "..."}
```

### 2.2 Key Metrics Dashboard

**Grafana**: https://grafana.learning-rec.com/d/service-health

**Critical Panels:**
- Request rate & latency (P50, P95, P99)
- Error rate (%)
- Model server status
- Database connection pool
- Milvus query latency

---

## 3. Common Incidents & Resolutions

### 3.1 🔥 High Latency (P95 > 300ms)

**Symptoms:**
- Grafana alert: "High recommendation latency"
- Users report slow page loads

**Diagnosis:**

```bash
# Check pod CPU/memory
kubectl top pods -n production

# Check API logs for slow requests
kubectl logs -n production -l app=fastapi-gateway --tail=100 | grep "duration_ms"

# Check database connections
kubectl exec -it <postgres-pod> -- psql -U admin -c "SELECT count(*) FROM pg_stat_activity;"

# Check Milvus performance
curl http://milvus:9091/metrics | grep query_latency
```

**Common Causes & Fixes:**

| Cause                     | Fix                                                  |
|---------------------------|------------------------------------------------------|
| High traffic spike        | Scale up: `kubectl scale deploy/fastapi-gateway --replicas=10` |
| Slow database queries     | Check slow query log; add indexes if needed          |
| Milvus index not loaded   | Restart Milvus: `kubectl rollout restart statefulset/milvus` |
| Model server cold start   | Pre-warm instances or increase min replicas          |
| Redis cache miss storm    | Check Redis memory; increase TTL for stable features |

**Escalation:**
If latency remains > 500ms for 10 minutes → Page platform lead

---

### 3.2 ⚠️ Elevated Error Rate (> 2%)

**Symptoms:**
- Grafana alert: "High error rate"
- HTTP 500 responses in logs

**Diagnosis:**

```bash
# Check error logs
kubectl logs -n production -l app=fastapi-gateway --tail=200 | grep ERROR

# Check exceptions in Sentry (if configured)
# https://sentry.io/learning-rec/production

# Check model server logs
kubectl logs -n production -l app=bentoml-server --tail=100
```

**Common Errors:**

**Error: `ConnectionError: Unable to connect to PostgreSQL`**
```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier learning-rec-prod

# Check network connectivity
kubectl exec -it <api-pod> -- nc -zv postgres.prod.svc.cluster.local 5432

# Fix: Restart API pods
kubectl rollout restart deployment/fastapi-gateway -n production
```

**Error: `ModelNotFoundError: retrieval_model/Production`**
```bash
# Check MLflow registry
mlflow models list --name retrieval_model

# Promote a known-good version
mlflow models update-model-version --name retrieval_model --version 42 --stage Production

# Restart model server
kubectl rollout restart deployment/bentoml-server -n production
```

**Error: `MilvusException: Collection not found`**
```bash
# Check Milvus collections
kubectl exec -it milvus-0 -n production -- python3 -c "
from pymilvus import connections, utility
connections.connect(host='localhost', port='19530')
print(utility.list_collections())
"

# Rebuild index if missing
kubectl create job --from=cronjob/build-milvus-index rebuild-index-manual -n production
```

---

### 3.3 🚨 Service Down (Health Check Failing)

**Symptoms:**
- `/health` returns 503 or times out
- Load balancer marks pods unhealthy

**Diagnosis:**

```bash
# Check pod status
kubectl get pods -n production -l app=fastapi-gateway

# Common states: CrashLoopBackOff, ImagePullBackOff, Pending

# Get pod events
kubectl describe pod <pod-name> -n production
```

**Fixes by State:**

**CrashLoopBackOff:**
```bash
# Check logs for startup errors
kubectl logs <pod-name> -n production --previous

# Common: Missing secrets, DB migration failure
# Fix: Check ConfigMap/Secrets, re-run migrations
kubectl exec -it <pod-name> -- python scripts/init_db.py
```

**ImagePullBackOff:**
```bash
# Check image exists
docker pull <image-name>

# Fix: Re-push image or update deployment with correct tag
kubectl set image deployment/fastapi-gateway fastapi=<correct-image> -n production
```

**Pending (Insufficient Resources):**
```bash
# Check node capacity
kubectl describe nodes | grep -A5 "Allocated resources"

# Fix: Scale down non-critical workloads or add nodes
kubectl scale deployment/non-critical-service --replicas=0 -n production
```

---

### 3.4 📉 Model Quality Degradation

**Symptoms:**
- Grafana alert: "Model drift detected"
- Engagement metrics drop (tracked externally)

**Diagnosis:**

```bash
# Check model metrics in MLflow
# https://mlflow.learning-rec.com

# Compare production vs. staging model performance
# Look at: precision@10, recall@10, NDCG@10

# Check data distribution
python scripts/check_drift.py --days 7
```

**Remediation:**

```bash
# Option 1: Rollback to previous model version
mlflow models update-model-version --name ranking_model --version 41 --stage Production
kubectl rollout restart deployment/bentoml-server -n production

# Option 2: Trigger immediate retrain
kubectl create job --from=cronjob/train-ranking-model train-ranking-manual -n production

# Monitor training progress
kubectl logs -f job/train-ranking-manual -n production
```

**Post-Incident:**
- Review training data quality
- Check for data pipeline failures
- Update model retraining schedule if needed

---

### 3.5 🗄️ Database Issues

**Symptoms:**
- Slow queries
- Connection pool exhausted
- Disk space alerts

**Diagnosis:**

```bash
# Check slow queries
kubectl exec -it postgres-pod -- psql -U admin -d recommendations -c "
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;
"

# Check connection count
kubectl exec -it postgres-pod -- psql -U admin -c "
SELECT count(*) FROM pg_stat_activity;
"

# Check disk usage (RDS)
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name FreeStorageSpace \
  --dimensions Name=DBInstanceIdentifier,Value=learning-rec-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

**Fixes:**

**Slow Query:**
```sql
-- Add index (example)
CREATE INDEX CONCURRENTLY idx_events_user_content ON events(user_id, content_id);
```

**Connection Pool Exhausted:**
```bash
# Increase max_connections (requires restart)
aws rds modify-db-parameter-group \
  --db-parameter-group-name learning-rec-params \
  --parameters "ParameterName=max_connections,ParameterValue=200,ApplyMethod=immediate"

# Or: Reduce API connection pool size
# Edit ConfigMap → DB_POOL_SIZE=10
kubectl edit configmap app-config -n production
kubectl rollout restart deployment/fastapi-gateway -n production
```

**Disk Full:**
```bash
# Clean old partitions (events table)
kubectl exec -it postgres-pod -- psql -U admin -d recommendations -c "
DROP TABLE events_2025_08;  -- Old partition
"

# Or: Increase RDS storage
aws rds modify-db-instance \
  --db-instance-identifier learning-rec-prod \
  --allocated-storage 500 \
  --apply-immediately
```

---

### 3.6 🔍 Milvus / Vector Search Issues

**Symptoms:**
- ANN search returns no results
- High Milvus query latency

**Diagnosis:**

```bash
# Check Milvus pod health
kubectl get pods -n production -l app=milvus

# Check collection status
kubectl exec -it milvus-0 -n production -- python3 << EOF
from pymilvus import connections, Collection
connections.connect(host='localhost', port='19530')
col = Collection('content_embeddings')
print(f"Entities: {col.num_entities}")
print(f"Index: {col.index()}")
EOF
```

**Fixes:**

**Index Not Loaded:**
```bash
# Load index to memory
kubectl exec -it milvus-0 -n production -- python3 << EOF
from pymilvus import connections, Collection
connections.connect(host='localhost', port='19530')
Collection('content_embeddings').load()
EOF
```

**Stale Index:**
```bash
# Rebuild index
kubectl create job --from=cronjob/build-milvus-index rebuild-now -n production
kubectl wait --for=condition=complete job/rebuild-now -n production --timeout=600s
```

**Out of Memory:**
```bash
# Check Milvus memory usage
kubectl top pod milvus-0 -n production

# Increase memory limit
kubectl edit statefulset milvus -n production
# Update: resources.limits.memory: 16Gi
```

---

## 4. Deployment Rollback

### 4.1 API Deployment Rollback

```bash
# View rollout history
kubectl rollout history deployment/fastapi-gateway -n production

# Rollback to previous version
kubectl rollout undo deployment/fastapi-gateway -n production

# Rollback to specific revision
kubectl rollout undo deployment/fastapi-gateway --to-revision=3 -n production

# Monitor rollback
kubectl rollout status deployment/fastapi-gateway -n production
```

### 4.2 Model Rollback

See [Model Quality Degradation](#34--model-quality-degradation) section.

### 4.3 Database Rollback

**Minor Schema Change (Additive):**
```bash
# Revert migration (Alembic example)
kubectl exec -it postgres-pod -- alembic downgrade -1
```

**Major Corruption:**
```bash
# Restore from snapshot (see ARCHITECTURE.md § 8.3)
aws rds restore-db-instance-from-db-snapshot ...
```

---

## 5. Scheduled Maintenance

### 5.1 Model Retraining

**Schedule:**
- Retrieval: Weekly (Sunday 2 AM UTC)
- Ranking: Daily (2 AM UTC)

**Monitor:**
```bash
# Check CronJob status
kubectl get cronjobs -n production

# View last run
kubectl get jobs -n production --sort-by=.metadata.creationTimestamp

# Manual trigger (if automated job fails)
kubectl create job --from=cronjob/train-ranking-model train-manual-$(date +%s) -n production
```

### 5.2 Database Maintenance

**Vacuum & Analyze (Weekly):**
```bash
kubectl exec -it postgres-pod -- psql -U admin -d recommendations -c "VACUUM ANALYZE;"
```

**Partition Cleanup (Monthly):**
```sql
-- Drop partitions older than 90 days
DROP TABLE IF EXISTS events_2025_07;
```

### 5.3 Certificate Renewal

**TLS Certs (Let's Encrypt, auto-renewed by cert-manager):**
```bash
# Check expiry
kubectl get certificates -n production

# Force renewal if needed
kubectl delete secret tls-cert -n production
# cert-manager will recreate
```

---

## 6. Monitoring & Alerts

### 6.1 Alert Rules (Prometheus)

**Critical Alerts** (page on-call):
- `HighErrorRate`: Error rate > 5% for 5 minutes
- `APIDown`: All API pods down
- `DatabaseDown`: PostgreSQL unreachable

**Warning Alerts** (Slack notification):
- `HighLatency`: P95 > 300ms for 10 minutes
- `ModelDrift`: Drift score > 0.15
- `DiskSpaceAlert`: < 10% free on RDS

### 6.2 Logs

**Centralized Logging (ELK / CloudWatch):**
```bash
# Query API errors (last 1 hour)
aws logs filter-log-events \
  --log-group-name /aws/eks/learning-rec/production \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Or kubectl
kubectl logs -n production -l app=fastapi-gateway --since=1h | grep ERROR
```

---

## 7. Contacts & Escalation

| Role                  | Contact                   | Escalate If                          |
|-----------------------|---------------------------|--------------------------------------|
| On-Call Engineer      | platform-oncall@co.com    | First responder                      |
| Platform Lead         | alice@company.com         | Incident > 30 min unresolved         |
| ML Engineer           | bob@company.com           | Model/data issues                    |
| Database Admin        | carol@company.com         | DB corruption, performance tuning    |
| Security Team         | security@company.com      | Auth issues, suspected breach        |

**PagerDuty**: https://company.pagerduty.com/incidents

---

## 8. Post-Incident Checklist

After resolving incident:

- [ ] Update incident ticket with resolution
- [ ] Post mortem meeting within 48 hours
- [ ] Document root cause in `docs/post-mortems/YYYY-MM-DD-incident.md`
- [ ] Create action items (e.g., add monitoring, fix race condition)
- [ ] Update runbook with lessons learned

---

## 9. Useful Commands Cheat Sheet

```bash
# Restart all services
kubectl rollout restart deployment -n production

# Scale API
kubectl scale deployment/fastapi-gateway --replicas=10 -n production

# Exec into API pod
kubectl exec -it $(kubectl get pod -n production -l app=fastapi-gateway -o jsonpath='{.items[0].metadata.name}') -n production -- /bin/bash

# Port-forward to local
kubectl port-forward svc/fastapi-gateway 8000:8000 -n production

# Tail logs
kubectl logs -f -n production -l app=fastapi-gateway --max-log-requests=10

# Check resource usage
kubectl top nodes
kubectl top pods -n production

# Describe pod for troubleshooting
kubectl describe pod <pod-name> -n production
```

---

**Last Updated**: 2025-10-10  
**Maintained By**: Platform SRE Team
