# TestPilot AI Infrastructure as Code

This directory contains the Terraform configuration for provisioning AWS infrastructure for the TestPilot AI project.

## Directory Structure

```
terraform/
├── modules/                 # Reusable Terraform modules
│   ├── vpc/                # VPC and networking components
│   ├── ecs-cluster/        # ECS cluster and services
│   ├── rds/                # RDS PostgreSQL database
│   ├── elasticache/        # Redis ElastiCache cluster
│   ├── s3-buckets/         # S3 buckets for artifacts
│   └── iam-roles/          # IAM roles and policies
├── envs/                   # Environment-specific configurations
│   ├── staging/            # Staging environment
│   └── production/         # Production environment
├── scripts/                # Helper scripts
│   └── init-backend.sh     # Initialize remote state backend
├── backend.tf              # Backend configuration template
└── README.md               # This file
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **Docker** (for running infrastructure tools)

## Quick Start

### 1. Initialize Backend Infrastructure

First, create the S3 buckets and DynamoDB tables for remote state:

```bash
# From the infra/ directory
cd terraform
./scripts/init-backend.sh
```

This script will create:
- S3 buckets: `testpilot-ai-terraform-state-staging` and `testpilot-ai-terraform-state-production`
- DynamoDB tables: `testpilot-ai-terraform-locks-staging` and `testpilot-ai-terraform-locks-production`

### 2. Deploy Staging Environment

```bash
cd envs/staging
terraform init
terraform plan
terraform apply
```

### 3. Deploy Production Environment

```bash
cd envs/production
terraform init
terraform plan
terraform apply
```

## Infrastructure Components

### VPC Module
- Creates VPC with public and private subnets
- Internet Gateway for public subnets
- NAT Gateway for private subnets
- Route tables and associations

### ECS Cluster Module (TODO)
- ECS cluster on Fargate
- Task definitions and services
- Load balancer integration
- Auto-scaling policies

### RDS Module (TODO)
- PostgreSQL RDS instance
- Multi-AZ deployment
- Automated backups
- Security groups

### ElastiCache Module (TODO)
- Redis cluster
- Multi-AZ replication
- Security groups
- Parameter groups

### S3 Buckets Module (TODO)
- Application assets bucket
- Logs bucket
- Backup bucket
- Lifecycle policies

### IAM Roles Module (TODO)
- ECS task execution role
- ECS task role
- RDS access role
- S3 access policies

## Environment Variables

The following environment variables should be set:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Security Considerations

- All S3 buckets have encryption enabled
- Public access is blocked on S3 buckets
- IAM roles follow least-privilege principle
- Security groups restrict access to necessary ports only
- RDS instances are in private subnets

## Cost Optimization

- Use Fargate Spot for non-critical workloads
- Enable RDS automated backups with appropriate retention
- Configure S3 lifecycle policies
- Use appropriate instance sizes for staging vs production

## Troubleshooting

### Common Issues

1. **Backend initialization fails**: Ensure AWS credentials are configured
2. **Terraform init fails**: Check S3 bucket and DynamoDB table exist
3. **Plan fails**: Verify AWS region and credentials

### Useful Commands

```bash
# Check backend status
terraform state list

# Import existing resources
terraform import aws_vpc.main vpc-12345

# Destroy specific resources
terraform destroy -target=aws_ecs_cluster.main

# View outputs
terraform output
```

## Contributing

When adding new modules or modifying existing ones:

1. Follow the existing naming conventions
2. Add appropriate variables and outputs
3. Include documentation in module README files
4. Test in staging before applying to production
5. Update this README with new components

## Support

For infrastructure issues or questions, refer to:
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/) 