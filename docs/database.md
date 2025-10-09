# PostgreSQL Database Guide

FinOpsGuard uses PostgreSQL for persistent storage of policies and analysis history.

## Overview

### Features

- **Policy Persistence**: Policies survive restarts and can be shared across instances
- **Analysis History**: Complete audit trail of all cost analyses
- **Query Support**: SQL queries for reporting and analytics
- **Hybrid Storage**: In-memory cache with database persistence
- **Automatic Failover**: Graceful degradation to in-memory storage
- **Connection Pooling**: Efficient resource usage

### Architecture

```
┌──────────────────────────┐
│   API Layer (FastAPI)    │
└──────────┬───────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐  ┌──────────┐
│ In-Memory│  │PostgreSQL│
│  Store   │  │   DB     │
└─────────┘  └──────────┘
   (Fast)      (Persistent)
```

**Hybrid Approach:**
- Policies: Loaded into memory on startup, synced to database on changes
- Analyses: Stored in both (memory for fast recent access, DB for history)

---

## Quick Start

### Docker Compose

**1. Start PostgreSQL:**
```bash
# Start with database profile
docker-compose --profile database up -d

# Enable database in environment
echo "DB_ENABLED=true" >> .env
docker-compose restart finopsguard
```

**2. Verify Connection:**
```bash
# Check health (should show database: healthy)
curl http://localhost:8080/healthz

# Get database statistics
curl http://localhost:8080/mcp/database/info
```

**3. Manage Database:**
```bash
# Initialize database (create tables)
make db-init

# Check migration status
make db-status

# Backup database
make db-backup

# Open PostgreSQL shell
make db-shell
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_ENABLED` | false | Enable PostgreSQL storage |
| `DATABASE_URL` | postgresql://... | Full connection string |
| `POSTGRES_HOST` | postgres | Database host |
| `POSTGRES_PORT` | 5432 | Database port |
| `POSTGRES_DB` | finopsguard | Database name |
| `POSTGRES_USER` | finopsguard | Database user |
| `POSTGRES_PASSWORD` | finopsguard | Database password |
| `DB_POOL_SIZE` | 10 | Connection pool size |
| `DB_MAX_OVERFLOW` | 20 | Max overflow connections |
| `DB_POOL_TIMEOUT` | 30 | Pool timeout (seconds) |
| `DB_POOL_RECYCLE` | 3600 | Recycle connections after (seconds) |

### Connection String Format

```
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
```

**Examples:**
```bash
# Local development
DATABASE_URL=postgresql://finopsguard:finopsguard@localhost:5432/finopsguard

# Docker Compose
DATABASE_URL=postgresql://finopsguard:finopsguard@postgres:5432/finopsguard

# Cloud (AWS RDS)
DATABASE_URL=postgresql://admin:pass@my-db.rds.amazonaws.com:5432/finopsguard

# Cloud (GCP Cloud SQL)
DATABASE_URL=postgresql://user:pass@/finopsguard?host=/cloudsql/project:region:instance

# SSL enabled
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

---

## Database Schema

### Tables

#### **policies**
Stores policy definitions:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(255) | Policy ID (PK) |
| name | VARCHAR(255) | Policy name |
| description | TEXT | Policy description |
| budget | FLOAT | Budget amount (nullable) |
| expression_json | JSON | Policy expression |
| on_violation | VARCHAR(50) | Action on violation |
| enabled | BOOLEAN | Is policy enabled |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| created_by | VARCHAR(255) | Creator (future) |
| updated_by | VARCHAR(255) | Last updater (future) |

**Indexes:**
- `idx_policy_enabled` on `enabled`
- `idx_policy_created_at` on `created_at`

#### **analyses**
Stores analysis history:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID (PK) |
| request_id | VARCHAR(255) | Unique request ID |
| started_at | TIMESTAMP | Analysis start time |
| completed_at | TIMESTAMP | Analysis completion time |
| duration_ms | INTEGER | Duration in milliseconds |
| iac_type | VARCHAR(50) | IaC type (terraform, k8s) |
| environment | VARCHAR(50) | Environment (dev/staging/prod) |
| estimated_monthly_cost | FLOAT | Estimated monthly cost |
| estimated_first_week_cost | FLOAT | Estimated first week cost |
| resource_count | INTEGER | Number of resources |
| policy_status | VARCHAR(50) | Policy evaluation status |
| policy_id | VARCHAR(255) | Policy ID evaluated |
| risk_flags | JSON | Array of risk flags |
| recommendations_count | INTEGER | Number of recommendations |
| result_json | JSON | Full analysis result |
| created_at | TIMESTAMP | Record creation time |

**Indexes:**
- `idx_analysis_request_id` on `request_id` (unique)
- `idx_analysis_started_at` on `started_at`
- `idx_analysis_environment` on `environment`
- `idx_analysis_policy_status` on `policy_status`
- `idx_analysis_created_at` on `created_at`

#### **cache_metadata**
Tracks cache usage (future):

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID (PK) |
| cache_key | VARCHAR(255) | Cache key |
| cache_type | VARCHAR(50) | Cache type |
| created_at | TIMESTAMP | Creation time |
| expires_at | TIMESTAMP | Expiration time |
| hit_count | INTEGER | Number of hits |
| last_accessed | TIMESTAMP | Last access time |

---

## Migrations

FinOpsGuard uses Alembic for database migrations.

### Create Migration

```bash
# Generate migration based on model changes
make db-migrate

# Or manually
alembic revision --autogenerate -m "Add new column"
```

### Apply Migrations

```bash
# Upgrade to latest version
make db-upgrade

# Or manually
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback to beginning
alembic downgrade base
```

### Migration Status

```bash
# Show current version
make db-status

# Or manually
alembic current
alembic history
```

---

## Database Management

### Initialization

```bash
# Initialize database (create all tables)
make db-init

# Or using script
./scripts/db-manage.sh init
```

### Backup & Restore

**Backup:**
```bash
# Create backup
make db-backup

# Or with custom filename
./scripts/db-manage.sh backup my-backup.sql
```

**Restore:**
```bash
# Restore from backup
./scripts/db-manage.sh restore my-backup.sql
```

### Shell Access

```bash
# Open psql shell
make db-shell

# Or manually
docker exec -it finopsguard-postgres psql -U finopsguard -d finopsguard
```

### Reset Database

```bash
# WARNING: Deletes all data
make db-reset

# Or using script
./scripts/db-manage.sh reset
```

---

## Queries and Analytics

### Useful SQL Queries

**Total analyses by environment:**
```sql
SELECT environment, COUNT(*) as count, AVG(estimated_monthly_cost) as avg_cost
FROM analyses
WHERE environment IS NOT NULL
GROUP BY environment
ORDER BY count DESC;
```

**Top 10 most expensive analyses:**
```sql
SELECT request_id, environment, estimated_monthly_cost, started_at
FROM analyses
ORDER BY estimated_monthly_cost DESC
LIMIT 10;
```

**Policy block rate:**
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN policy_status = 'block' THEN 1 ELSE 0 END) as blocked,
    ROUND(100.0 * SUM(CASE WHEN policy_status = 'block' THEN 1 ELSE 0 END) / COUNT(*), 2) as block_rate
FROM analyses
WHERE policy_status IS NOT NULL;
```

**Cost trends over time:**
```sql
SELECT 
    DATE_TRUNC('day', started_at) as day,
    AVG(estimated_monthly_cost) as avg_cost,
    MAX(estimated_monthly_cost) as max_cost,
    COUNT(*) as analyses
FROM analyses
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', started_at)
ORDER BY day DESC;
```

**Active policies:**
```sql
SELECT id, name, budget, on_violation, enabled
FROM policies
WHERE enabled = true
ORDER BY created_at DESC;
```

---

## Kubernetes Deployment

### StatefulSet with PostgreSQL

**Option 1: Use Cloud Provider Database (Recommended)**

```yaml
# ConfigMap with database connection
apiVersion: v1
kind: ConfigMap
metadata:
  name: finopsguard-config
  namespace: finopsguard
data:
  DB_ENABLED: "true"
  POSTGRES_HOST: "my-db.rds.amazonaws.com"  # or Cloud SQL, Azure Database
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "finopsguard"
  POSTGRES_USER: "finopsguard"
```

```yaml
# Secret with password
apiVersion: v1
kind: Secret
metadata:
  name: finopsguard-db-secret
  namespace: finopsguard
type: Opaque
stringData:
  POSTGRES_PASSWORD: "your-secure-password"
  DATABASE_URL: "postgresql://user:pass@host:5432/db"
```

**Option 2: PostgreSQL StatefulSet**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: finopsguard
spec:
  ports:
  - port: 5432
  clusterIP: None
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: finopsguard
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: finopsguard
        - name: POSTGRES_USER
          value: finopsguard
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: finopsguard-db-secret
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

---

## Monitoring

### Database Metrics

**Health Check:**
```bash
curl http://localhost:8080/healthz
```

Response includes database status:
```json
{
  "status": "ok",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "cache": "disabled"
  }
}
```

**Database Statistics:**
```bash
curl http://localhost:8080/mcp/database/info
```

Response:
```json
{
  "enabled": true,
  "total_analyses": 1234,
  "average_monthly_cost": 845.50,
  "blocked_count": 12
}
```

### Prometheus Metrics

Monitor database performance:

```promql
# Database connection pool
pg_pool_size
pg_pool_active_connections
pg_pool_idle_connections

# Database queries (add custom metrics)
finops_db_queries_total
finops_db_query_duration_seconds
```

---

## Troubleshooting

### Connection Issues

**Error: Cannot connect to database**

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs finopsguard-postgres

# Test connection manually
PGPASSWORD=finopsguard psql -h localhost -p 5432 -U finopsguard -d finopsguard
```

**Error: Password authentication failed**

```bash
# Verify environment variables
docker exec finopsguard env | grep POSTGRES

# Reset password
docker exec -it finopsguard-postgres psql -U postgres -c "ALTER USER finopsguard PASSWORD 'newpassword';"
```

### Migration Issues

**Error: Migration failed**

```bash
# Check migration status
make db-status

# Rollback to previous version
make db-downgrade

# Try upgrade again
make db-upgrade
```

**Error: Table already exists**

```bash
# Mark current state as migrated
alembic stamp head

# Or reset and reinitialize
make db-reset
```

### Performance Issues

**Slow queries:**

```bash
# Check indexes
docker exec finopsguard-postgres psql -U finopsguard -d finopsguard -c "\d+ analyses"

# Analyze query performance
docker exec finopsguard-postgres psql -U finopsguard -d finopsguard -c "EXPLAIN ANALYZE SELECT * FROM analyses ORDER BY created_at DESC LIMIT 10;"
```

**Too many connections:**

```bash
# Check active connections
docker exec finopsguard-postgres psql -U finopsguard -d finopsguard -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

---

## Best Practices

### 1. Regular Backups

```bash
# Daily backup (add to cron)
0 2 * * * cd /path/to/FinOpsGuard && make db-backup
```

### 2. Clean Old Data

```python
# Clean analyses older than 90 days
from finopsguard.database import get_analysis_store

store = get_analysis_store()
deleted = store.delete_old_analyses(days=90)
print(f"Deleted {deleted} old analyses")
```

### 3. Monitor Database Size

```sql
# Check database size
SELECT pg_size_pretty(pg_database_size('finopsguard'));

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 4. Index Maintenance

```sql
# Reindex for performance
REINDEX DATABASE finopsguard;

# Vacuum for cleanup
VACUUM ANALYZE;
```

### 5. Security

**Use secure passwords:**
```bash
# Generate secure password
openssl rand -base64 32

# Update .env
POSTGRES_PASSWORD=<generated-password>
```

**Enable SSL:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

**Limit access:**
```sql
-- Revoke public access
REVOKE ALL ON DATABASE finopsguard FROM PUBLIC;

-- Grant specific permissions
GRANT CONNECT ON DATABASE finopsguard TO finopsguard;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO finopsguard;
```

---

## Production Deployment

### AWS RDS

**Create RDS Instance:**
```bash
aws rds create-db-instance \
    --db-instance-identifier finopsguard-db \
    --db-instance-class db.t3.small \
    --engine postgres \
    --engine-version 15.3 \
    --master-username finopsguard \
    --master-user-password <secure-password> \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name my-subnet-group \
    --backup-retention-period 7 \
    --no-publicly-accessible
```

**Configure FinOpsGuard:**
```bash
DATABASE_URL=postgresql://finopsguard:<password>@finopsguard-db.xxxxx.us-east-1.rds.amazonaws.com:5432/finopsguard
DB_ENABLED=true
```

### GCP Cloud SQL

**Create Cloud SQL Instance:**
```bash
gcloud sql instances create finopsguard-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=<secure-password>

# Create database
gcloud sql databases create finopsguard --instance=finopsguard-db

# Create user
gcloud sql users create finopsguard \
    --instance=finopsguard-db \
    --password=<secure-password>
```

**Configure FinOpsGuard:**
```bash
# Using Cloud SQL Proxy
DATABASE_URL=postgresql://finopsguard:<password>@127.0.0.1:5432/finopsguard
DB_ENABLED=true
```

### Azure Database for PostgreSQL

**Create Azure Database:**
```bash
az postgres server create \
    --resource-group finopsguard-rg \
    --name finopsguard-db \
    --location eastus \
    --admin-user finopsguard \
    --admin-password <secure-password> \
    --sku-name B_Gen5_1 \
    --version 15
```

**Configure FinOpsGuard:**
```bash
DATABASE_URL=postgresql://finopsguard@finopsguard-db:<password>@finopsguard-db.postgres.database.azure.com:5432/finopsguard?sslmode=require
DB_ENABLED=true
```

---

## Data Retention

### Automatic Cleanup

Add to cron or Kubernetes CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: finopsguard-cleanup
  namespace: finopsguard
spec:
  schedule: "0 2 * * 0"  # Weekly at 2 AM Sunday
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: finopsguard:latest
            command:
            - python
            - -c
            - |
              from finopsguard.database import get_analysis_store
              store = get_analysis_store()
              deleted = store.delete_old_analyses(days=90)
              print(f"Deleted {deleted} old analyses")
          restartPolicy: OnFailure
```

---

## Migration from In-Memory

### Export Current Data

```python
# Export policies
from finopsguard.engine.policy_engine import PolicyEngine

engine = PolicyEngine(use_database=False)
policies = engine.list_policies()

# Save to file
import json
with open('policies_backup.json', 'w') as f:
    json.dump([p.model_dump() for p in policies], f, indent=2)
```

### Import to PostgreSQL

```python
# Import policies
from finopsguard.database import get_policy_store
from finopsguard.types.policy import Policy
import json

store = get_policy_store()

with open('policies_backup.json') as f:
    policies_data = json.load(f)

for policy_data in policies_data:
    policy = Policy(**policy_data)
    store.create_policy(policy)
    print(f"Imported policy: {policy.name}")
```

---

## See Also

- [Deployment Guide](./deployment.md)
- [Architecture Documentation](./architecture.md)
- [Requirements](./requirements.md)
- [Quick Start](../deploy/QUICK_START.md)

