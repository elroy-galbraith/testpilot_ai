# AWS to GCP Migration Guide

This guide outlines the migration from AWS to GCP for the TestPilot AI project.

## 🎯 Why GCP?

### **Personal Project Benefits:**
- ✅ **No new email account needed** - Use existing Google account
- ✅ **Lower costs** - Especially for serverless workloads
- ✅ **Better free tier** - More generous than AWS
- ✅ **Simpler deployment** - Cloud Run vs ECS complexity
- ✅ **Integrated services** - Better developer experience

### **Cost Comparison:**
| **Service** | **AWS (Monthly)** | **GCP (Monthly)** | **Savings** |
|-------------|-------------------|-------------------|-------------|
| **Compute** | $50-100 (ECS) | $20-40 (Cloud Run) | 50-60% |
| **Database** | $50-80 (RDS) | $40-60 (Cloud SQL) | 20-25% |
| **Cache** | $30-50 (ElastiCache) | $25-40 (Memorystore) | 15-20% |
| **Storage** | $10-20 (S3) | $8-15 (Cloud Storage) | 20-25% |
| **Total** | **$140-250** | **$93-155** | **~35% savings** |

## 🏗️ Architecture Mapping

| **AWS Service** | **GCP Equivalent** | **Status** |
|----------------|-------------------|------------|
| **ECS Fargate** | **Cloud Run** | ✅ Implemented |
| **RDS PostgreSQL** | **Cloud SQL** | ✅ Implemented |
| **ElastiCache Redis** | **Memorystore Redis** | 🔄 In Progress |
| **S3** | **Cloud Storage** | 🔄 In Progress |
| **VPC** | **VPC** | ✅ Implemented |
| **IAM** | **IAM** | ✅ Implemented |
| **CloudWatch Logs** | **Cloud Logging** | 🔄 In Progress |

## 🚀 Migration Steps

### **Phase 1: Setup GCP Project**
```bash
# 1. Create GCP project (if not exists)
gcloud projects create testpilot-ai-$(date +%s) --name="TestPilot AI"

# 2. Set project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 3. Enable billing
# Go to GCP Console > Billing and link your account
```

### **Phase 2: Initialize Infrastructure**
```bash
# 1. Navigate to GCP infrastructure
cd infra/gcp/terraform

# 2. Initialize backend
./scripts/init-backend.sh

# 3. Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-admin-key.json"

# 4. Deploy staging environment
cd envs/staging
terraform init
terraform plan -var="project_id=$PROJECT_ID" -var="database_password=your_password" -var="app_password=your_app_password"
terraform apply -var="project_id=$PROJECT_ID" -var="database_password=your_password" -var="app_password=your_app_password"
```

### **Phase 3: Update Application Code**
```bash
# 1. Update Dockerfiles for GCP
# - Use Google Cloud SDK
# - Update environment variables
# - Configure for Cloud Run

# 2. Update CI/CD pipeline
# - Use Cloud Build instead of GitHub Actions
# - Deploy to Cloud Run
# - Update environment variables
```

### **Phase 4: Data Migration**
```bash
# 1. Export data from AWS RDS
pg_dump -h aws-rds-endpoint -U username -d database > backup.sql

# 2. Import to GCP Cloud SQL
psql -h gcp-sql-endpoint -U username -d database < backup.sql

# 3. Update connection strings in application
```

## 📁 File Structure Changes

### **Before (AWS):**
```
infra/
├── terraform/
│   ├── modules/
│   │   ├── vpc/
│   │   ├── ecs-cluster/
│   │   ├── rds/
│   │   └── iam-roles/
│   └── envs/
│       ├── staging/
│       └── production/
```

### **After (GCP):**
```
infra/
├── gcp/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── vpc/
│   │   │   ├── cloud-run/
│   │   │   ├── cloud-sql/
│   │   │   ├── memorystore/
│   │   │   ├── storage/
│   │   │   └── iam/
│   │   └── envs/
│   │       ├── staging/
│   │       └── production/
│   ├── cloudbuild/
│   └── docker/
└── aws/  # Keep for reference
    └── terraform/
```

## 🔧 Configuration Changes

### **Environment Variables:**
```bash
# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_DEFAULT_REGION=us-east-1

# GCP
GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
GOOGLE_CLOUD_PROJECT=your-project-id
```

### **Database Connection:**
```python
# AWS RDS
DATABASE_URL="postgresql://user:pass@aws-rds-endpoint:5432/db"

# GCP Cloud SQL
DATABASE_URL="postgresql://user:pass@gcp-sql-endpoint:5432/db"
# Or use Cloud SQL Proxy
DATABASE_URL="postgresql://user:pass@/db?host=/cloudsql/project:region:instance"
```

### **Storage:**
```python
# AWS S3
import boto3
s3 = boto3.client('s3')
s3.upload_file('file.txt', 'bucket', 'key')

# GCP Cloud Storage
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('bucket')
blob = bucket.blob('key')
blob.upload_from_filename('file.txt')
```

## 🚀 Deployment Changes

### **AWS ECS:**
```yaml
# task-definition.json
{
  "family": "testpilot-backend",
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512"
}
```

### **GCP Cloud Run:**
```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: testpilot-backend
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project/testpilot-backend
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
```

## 🔒 Security Considerations

### **IAM vs Service Accounts:**
- **AWS IAM**: Users, roles, policies
- **GCP IAM**: Service accounts, roles, bindings

### **Network Security:**
- **AWS**: Security groups, NACLs
- **GCP**: Firewall rules, VPC

### **Secret Management:**
- **AWS**: Secrets Manager
- **GCP**: Secret Manager

## 📊 Monitoring Changes

### **AWS CloudWatch → GCP Cloud Monitoring:**
```python
# AWS CloudWatch
import boto3
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(...)

# GCP Cloud Monitoring
from google.cloud import monitoring_v3
client = monitoring_v3.MetricServiceClient()
client.create_time_series(...)
```

## 💰 Cost Optimization

### **GCP-Specific Optimizations:**
1. **Use Cloud Run** - Pay only for requests
2. **Enable autoscaling** - Scale to zero
3. **Use Cloud SQL Proxy** - Secure connections
4. **Leverage free tier** - 2M requests/month on Cloud Run
5. **Use regional resources** - Lower latency and costs

### **Billing Alerts:**
```bash
# Set up billing alerts
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="TestPilot Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

## 🧪 Testing Strategy

### **Staging Environment:**
- Deploy to GCP staging first
- Test all functionality
- Validate costs
- Performance testing

### **Production Migration:**
- Blue-green deployment
- Data migration during maintenance window
- Rollback plan ready

## 📚 Additional Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
- [Migration Best Practices](https://cloud.google.com/architecture/framework)

## ⚠️ Rollback Plan

If issues arise during migration:

1. **Keep AWS infrastructure running** during migration
2. **Use DNS routing** to switch between environments
3. **Maintain data synchronization** between AWS and GCP
4. **Test rollback procedures** before migration
5. **Monitor both environments** during transition

## 🎉 Benefits After Migration

- **Lower operational costs** (~35% savings)
- **Simpler deployment process**
- **Better developer experience**
- **Integrated monitoring and logging**
- **Faster iteration cycles**
- **No vendor lock-in concerns** 