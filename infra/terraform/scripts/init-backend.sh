#!/bin/bash

# Script to initialize Terraform backend infrastructure
# This script creates the S3 buckets and DynamoDB tables needed for remote state

set -e

# Configuration
PROJECT_NAME="testpilot-ai"
REGION="us-east-1"
ENVIRONMENTS=("staging" "production")

echo "Initializing Terraform backend infrastructure for $PROJECT_NAME..."

# Create S3 buckets and DynamoDB tables for each environment
for ENV in "${ENVIRONMENTS[@]}"; do
    echo "Setting up backend for $ENV environment..."
    
    # S3 bucket names
    STATE_BUCKET="${PROJECT_NAME}-terraform-state-${ENV}"
    LOCK_TABLE="${PROJECT_NAME}-terraform-locks-${ENV}"
    
    echo "Creating S3 bucket: $STATE_BUCKET"
    
    # Create S3 bucket with versioning and encryption
    if [ "$REGION" = "us-east-1" ]; then
        # us-east-1 doesn't need LocationConstraint
        aws s3api create-bucket \
            --bucket "$STATE_BUCKET" \
            --region "$REGION" || true
    else
        # Other regions need LocationConstraint
        aws s3api create-bucket \
            --bucket "$STATE_BUCKET" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION" || true
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$STATE_BUCKET" \
        --versioning-configuration Status=Enabled
    
    # Enable server-side encryption
    aws s3api put-bucket-encryption \
        --bucket "$STATE_BUCKET" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    # Block public access
    aws s3api put-public-access-block \
        --bucket "$STATE_BUCKET" \
        --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    
    echo "Creating DynamoDB table: $LOCK_TABLE"
    
    # Create DynamoDB table for state locking
    aws dynamodb create-table \
        --table-name "$LOCK_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" || true
    
    # Wait for table to be active
    echo "Waiting for DynamoDB table to be active..."
    aws dynamodb wait table-exists \
        --table-name "$LOCK_TABLE" \
        --region "$REGION"
    
    echo "Backend setup complete for $ENV environment"
    echo "  S3 Bucket: $STATE_BUCKET"
    echo "  DynamoDB Table: $LOCK_TABLE"
    echo ""
done

echo "Terraform backend initialization complete!"
echo ""
echo "Next steps:"
echo "1. Navigate to infra/terraform/envs/staging"
echo "2. Run: terraform init"
echo "3. Run: terraform plan"
echo "4. Run: terraform apply"
echo ""
echo "Then repeat for production environment." 