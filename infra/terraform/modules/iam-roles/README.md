# IAM Roles and Policies Module

This Terraform module creates IAM roles and policies for the TestPilot AI infrastructure, following the principle of least privilege.

## Resources Created

### Roles

1. **ECS Task Execution Role** (`aws_iam_role.ecs_task_execution`)
   - Allows ECS to pull container images from ECR
   - Enables writing logs to CloudWatch
   - Attached to the AWS managed policy `AmazonECSTaskExecutionRolePolicy`

2. **ECS Task Role** (`aws_iam_role.ecs_task`)
   - Allows the application running in ECS to access AWS services
   - Attached to custom policies for S3, RDS, ElastiCache, and CloudWatch Logs

3. **RDS Monitoring Role** (`aws_iam_role.rds_monitoring`)
   - Enables enhanced monitoring for RDS instances
   - Attached to the AWS managed policy `AmazonRDSEnhancedMonitoringRole`

### Policies

1. **S3 Access Policy** (`aws_iam_policy.s3_access`)
   - Grants read/write access to project-specific S3 buckets
   - Resources: `arn:aws:s3:::testpilot-ai-*` and `arn:aws:s3:::testpilot-ai-*/*`
   - Actions: `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`

2. **RDS Access Policy** (`aws_iam_policy.rds_access`)
   - Enables database connections using IAM authentication
   - Restricted to connections from the specified VPC
   - Actions: `rds-db:connect`

3. **ElastiCache Access Policy** (`aws_iam_policy.elasticache_access`)
   - Allows describing ElastiCache resources for connection management
   - Actions: `elasticache:DescribeReplicationGroups`, `elasticache:DescribeCacheClusters`

4. **CloudWatch Logs Policy** (`aws_iam_policy.cloudwatch_logs`)
   - Enables application logging to CloudWatch
   - Resources: `/ecs/testpilot-ai-*` log groups
   - Actions: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogStreams`

## Usage

```hcl
module "iam_roles" {
  source = "../../modules/iam-roles"

  project_name = "testpilot-ai"
  environment  = "staging"
  vpc_id       = module.vpc.vpc_id
  rds_resource_id = module.rds.db_resource_id
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_name | Project name for resource tagging | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |
| vpc_id | VPC ID for RDS access policy conditions | `string` | n/a | yes |
| rds_resource_id | RDS resource ID for database user access | `string` | `""` | no |

## Outputs

| Name | Description |
|------|-------------|
| ecs_task_execution_role_arn | ARN of the ECS task execution role |
| ecs_task_execution_role_name | Name of the ECS task execution role |
| ecs_task_role_arn | ARN of the ECS task role |
| ecs_task_role_name | Name of the ECS task role |
| rds_monitoring_role_arn | ARN of the RDS monitoring role |
| rds_monitoring_role_name | Name of the RDS monitoring role |
| s3_access_policy_arn | ARN of the S3 access policy |
| rds_access_policy_arn | ARN of the RDS access policy |
| elasticache_access_policy_arn | ARN of the ElastiCache access policy |
| cloudwatch_logs_policy_arn | ARN of the CloudWatch Logs policy |

## Security Considerations

- All policies follow the principle of least privilege
- RDS access is restricted to connections from the specified VPC
- S3 access is limited to project-specific buckets
- CloudWatch Logs access is scoped to ECS log groups
- ElastiCache access is read-only for resource discovery

## Dependencies

This module depends on:
- VPC module (for `vpc_id`)
- RDS module (for `rds_resource_id`)

## Testing

To test the IAM roles and policies:

1. Deploy the module in a sandbox environment
2. Verify role creation: `aws iam get-role --role-name testpilot-ai-ecs-task-staging`
3. Verify policy attachments: `aws iam list-attached-role-policies --role-name testpilot-ai-ecs-task-staging`
4. Test policy permissions using AWS CLI or SDK 