#!/bin/bash

# Script to destroy Terraform backend infrastructure
# WARNING: This will permanently delete S3 buckets and DynamoDB tables

set -e

# Configuration
PROJECT_NAME="testpilot-ai"
REGION="us-east-1"
ENVIRONMENTS=("staging" "production")

echo "WARNING: This will permanently delete all Terraform state and backend infrastructure!"
echo "This action cannot be undone."
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Destroying Terraform backend infrastructure for $PROJECT_NAME..."

# Delete S3 buckets and DynamoDB tables for each environment
for ENV in "${ENVIRONMENTS[@]}"; do
    echo "Destroying backend for $ENV environment..."
    
    # S3 bucket names
    STATE_BUCKET="${PROJECT_NAME}-terraform-state-${ENV}"
    LOCK_TABLE="${PROJECT_NAME}-terraform-locks-${ENV}"
    
    echo "Deleting S3 bucket: $STATE_BUCKET"
    
    # Delete all objects in the bucket first
    aws s3 rm s3://$STATE_BUCKET --recursive --region $REGION 2>/dev/null || true
    
    # Delete the bucket
    aws s3api delete-bucket --bucket $STATE_BUCKET --region $REGION 2>/dev/null || true
    
    echo "Deleting DynamoDB table: $LOCK_TABLE"
    
    # Delete the DynamoDB table
    aws dynamodb delete-table --table-name $LOCK_TABLE --region $REGION 2>/dev/null || true
    
    echo "Backend destruction complete for $ENV environment"
    echo ""
done

echo "Terraform backend destruction complete!"
echo ""
echo "To rebuild the infrastructure:"
echo "1. Run: ./scripts/init-backend.sh"
echo "2. Navigate to envs/staging and run: terraform init && terraform apply"
echo "3. Repeat for production environment" 