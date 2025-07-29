# GCP Infrastructure for TestPilot AI

This directory contains the Google Cloud Platform (GCP) infrastructure as code for the TestPilot AI project.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Infrastructure                       │
├─────────────────────────────────────────────────────────────┤
│  Cloud Run (Frontend)  │  Cloud Run (Backend)              │
│  - Auto-scaling        │  - FastAPI containers             │
│  - HTTPS by default    │  - Serverless execution           │
├─────────────────────────────────────────────────────────────┤
│  Cloud SQL (PostgreSQL) │  Memorystore (Redis)             │
│  - Private IP only      │  - Session storage               │
│  - Automated backups    │  - Cache layer                   │
├─────────────────────────────────────────────────────────────┤
│  Cloud Storage          │  Cloud Logging                   │
│  - Test artifacts       │  - Centralized logging           │
│  - Screenshots/logs     │  - Structured logging            │
├─────────────────────────────────────────────────────────────┤
│  VPC Network            │  IAM & Security                  │
│  - Private subnets      │  - Service accounts              │
│  - Cloud NAT            │  - Least privilege access        │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
infra/gcp/
├── terraform/
│   ├── modules/
│   │   ├── vpc/              # VPC, subnets, firewall rules
│   │   ├── cloud-run/        # Cloud Run services
│   │   ├── cloud-sql/        # PostgreSQL instance
│   │   ├── memorystore/      # Redis instance
│   │   ├── storage/          # Cloud Storage buckets
│   │   └── iam/             # Service accounts and roles
│   ├── envs/
│   │   ├── staging/         # Staging environment
│   │   └── production/      # Production environment
│   └── scripts/
│       ├── init-backend.sh  # Initialize Terraform backend
│       └── destroy-backend.sh # Clean up backend resources
├── cloudbuild/              # CI/CD pipeline configuration
├── docker/                  # Container configurations
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud SDK** installed and configured
2. **Terraform** installed (or use Docker)
3. **Docker** for container builds
4. **GCP Project** with billing enabled

### Setup Steps

1. **Initialize GCP Project**
   ```bash
   # Set your project ID
   export PROJECT_ID="your-project-id"
   gcloud config set project $PROJECT_ID
   
   # Enable required APIs
   gcloud services enable \
     cloudbuild.googleapis.com \
     run.googleapis.com \
     sqladmin.googleapis.com \
     redis.googleapis.com \
     storage.googleapis.com \
     compute.googleapis.com
   ```

2. **Initialize Terraform Backend**
   ```bash
   cd infra/gcp/terraform
   ./scripts/init-backend.sh
   ```

3. **Deploy Staging Environment**
   ```bash
   cd envs/staging
   terraform init
   terraform plan
   terraform apply
   ```

4. **Deploy Production Environment**
   ```bash
   cd ../production
   terraform init
   terraform plan
   terraform apply
   ```

## 💰 Cost Estimation

### Monthly Costs (Estimated)

| **Service** | **Staging** | **Production** | **Total** |
|-------------|-------------|----------------|-----------|
| **Cloud Run** | $10-20 | $30-50 | $40-70 |
| **Cloud SQL** | $15-25 | $40-60 | $55-85 |
| **Memorystore** | $10-15 | $25-35 | $35-50 |
| **Cloud Storage** | $5-10 | $10-20 | $15-30 |
| **Network** | $5-10 | $10-15 | $15-25 |
| **Total** | **$45-80** | **$115-180** | **$160-260** |

### Free Tier Benefits

- **Cloud Run**: 2M requests/month
- **Cloud Storage**: 5GB storage
- **Cloud SQL**: 1GB storage (limited)
- **Cloud Build**: 120 build-minutes/day

## 🔧 Services Overview

### Core Services

1. **Cloud Run**
   - Serverless container platform
   - Auto-scaling from 0 to 1000+ instances
   - HTTPS by default
   - Pay only for actual request processing

2. **Cloud SQL**
   - Fully managed PostgreSQL
   - Automated backups and updates
   - High availability options
   - Private IP connectivity

3. **Memorystore Redis**
   - Fully managed Redis
   - Automatic failover
   - VPC-native connectivity
   - No maintenance overhead

4. **Cloud Storage**
   - Object storage for artifacts
   - Lifecycle management
   - Fine-grained access control
   - Global edge locations

### Supporting Services

1. **VPC Network**
   - Private subnets for databases
   - Cloud NAT for outbound internet
   - Firewall rules for security
   - VPC peering if needed

2. **IAM & Security**
   - Service accounts for applications
   - Least privilege access
   - Workload identity
   - Secret Manager integration

3. **Cloud Logging**
   - Centralized logging
   - Structured log format
   - Log-based metrics
   - Integration with monitoring

## 🔒 Security Features

- **Private networking** for databases
- **Service accounts** with minimal permissions
- **VPC firewall rules** for network security
- **Cloud Armor** for DDoS protection (optional)
- **Secret Manager** for sensitive data
- **Audit logging** for compliance

## 📊 Monitoring & Observability

- **Cloud Monitoring** dashboards
- **Cloud Logging** for centralized logs
- **Error Reporting** for application errors
- **Trace** for distributed tracing
- **Profiler** for performance analysis

## 🚀 Deployment Strategy

### Environment Strategy

1. **Staging Environment**
   - Smaller instance sizes
   - Development data
   - Manual deployments
   - Cost optimization

2. **Production Environment**
   - Larger instance sizes
   - Production data
   - Automated deployments
   - High availability

### CI/CD Pipeline

- **Cloud Build** for container builds
- **Cloud Run** for deployments
- **Terraform** for infrastructure
- **GitHub Actions** for orchestration

## 🛠️ Development Workflow

1. **Local Development**
   - Docker Compose for local services
   - Cloud Code for IDE integration
   - Local testing with emulators

2. **Staging Deployment**
   - Automated on feature branches
   - Integration testing
   - Performance validation

3. **Production Deployment**
   - Manual approval required
   - Blue-green deployment
   - Rollback capabilities

## 🔧 Troubleshooting

### Common Issues

1. **Permission Errors**
   - Check service account permissions
   - Verify IAM roles are assigned
   - Ensure APIs are enabled

2. **Network Connectivity**
   - Verify VPC configuration
   - Check firewall rules
   - Validate Cloud NAT setup

3. **Cost Optimization**
   - Use appropriate instance sizes
   - Enable autoscaling
   - Monitor resource usage

### Useful Commands

```bash
# Check project configuration
gcloud config list

# List enabled APIs
gcloud services list --enabled

# Check IAM permissions
gcloud projects get-iam-policy $PROJECT_ID

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision"

# Monitor costs
gcloud billing accounts list
```

## 📚 Additional Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
- [GCP Architecture Framework](https://cloud.google.com/architecture/framework)

## 🤝 Contributing

1. Follow the existing directory structure
2. Use consistent naming conventions
3. Document all variables and outputs
4. Test changes in staging first
5. Update this README as needed 