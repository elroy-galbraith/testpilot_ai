#!/bin/bash

# Script to initialize GCP Terraform backend
# Creates Cloud Storage bucket and enables required APIs

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
PROJECT_NAME="testpilot-ai"
REGION="us-central1"
ENVIRONMENTS=("staging" "production")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    print_error "PROJECT_ID is not set. Please set it or run 'gcloud config set project YOUR_PROJECT_ID'"
    exit 1
fi

print_status "Initializing GCP Terraform backend for project: $PROJECT_ID"

# Enable required APIs
print_status "Enabling required GCP APIs..."

gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com \
    vpcaccess.googleapis.com \
    secretmanager.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    --project="$PROJECT_ID"

print_status "APIs enabled successfully"

# Create Cloud Storage bucket for Terraform state
for ENV in "${ENVIRONMENTS[@]}"; do
    print_status "Setting up backend for $ENV environment..."
    
    # Bucket name (must be globally unique)
    STATE_BUCKET="${PROJECT_NAME}-terraform-state-${ENV}-${PROJECT_ID}"
    
    print_status "Creating Cloud Storage bucket: $STATE_BUCKET"
    
    # Create bucket if it doesn't exist
    if ! gsutil ls -b "gs://$STATE_BUCKET" >/dev/null 2>&1; then
        gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$STATE_BUCKET"
        print_status "Bucket created successfully"
    else
        print_warning "Bucket already exists"
    fi
    
    # Enable versioning
    gsutil versioning set on "gs://$STATE_BUCKET"
    
    # Set lifecycle policy to delete old versions after 90 days
    cat > /tmp/lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "age": 90,
        "isLive": false
      }
    }
  ]
}
EOF
    
    gsutil lifecycle set /tmp/lifecycle.json "gs://$STATE_BUCKET"
    rm /tmp/lifecycle.json
    
    # Set uniform bucket-level access
    gsutil uniformbucketlevelaccess set on "gs://$STATE_BUCKET"
    
    # Create backend configuration file
    BACKEND_CONFIG_FILE="envs/${ENV}/backend.tf"
    
    cat > "$BACKEND_CONFIG_FILE" << EOF
terraform {
  backend "gcs" {
    bucket = "$STATE_BUCKET"
    prefix = "terraform/state"
  }
}
EOF
    
    print_status "Backend configuration created: $BACKEND_CONFIG_FILE"
    print_status "Backend setup complete for $ENV environment"
    echo ""
done

# Create service account for Terraform (if it doesn't exist)
SERVICE_ACCOUNT_NAME="terraform-admin"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

print_status "Setting up Terraform service account..."

# Check if service account exists
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Terraform Admin Service Account" \
        --description="Service account for Terraform infrastructure management" \
        --project="$PROJECT_ID"
    
    print_status "Service account created: $SERVICE_ACCOUNT_EMAIL"
else
    print_warning "Service account already exists: $SERVICE_ACCOUNT_EMAIL"
fi

# Grant necessary roles to the service account
print_status "Granting necessary IAM roles..."

ROLES=(
    "roles/storage.admin"
    "roles/compute.admin"
    "roles/run.admin"
    "roles/sql.admin"
    "roles/redis.admin"
    "roles/iam.serviceAccountAdmin"
    "roles/resourcemanager.projectIamAdmin"
    "roles/vpcaccess.admin"
    "roles/secretmanager.admin"
    "roles/logging.admin"
    "roles/monitoring.admin"
)

for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$ROLE" \
        --quiet
done

print_status "IAM roles granted successfully"

# Create and download service account key (optional, for local development)
print_status "Creating service account key for local development..."

KEY_FILE="terraform-admin-key.json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT_EMAIL" \
    --project="$PROJECT_ID"

print_status "Service account key created: $KEY_FILE"
print_warning "Keep this key secure and add it to .gitignore"

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Service account keys
*.json

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
EOF
    print_status "Created .gitignore file"
fi

print_status "GCP Terraform backend initialization complete!"
echo ""
print_status "Next steps:"
echo "1. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable:"
echo "   export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/$KEY_FILE\""
echo ""
echo "2. Initialize Terraform in staging environment:"
echo "   cd envs/staging"
echo "   terraform init"
echo "   terraform plan"
echo ""
echo "3. Initialize Terraform in production environment:"
echo "   cd envs/production"
echo "   terraform init"
echo "   terraform plan"
echo ""
print_warning "Remember to add $KEY_FILE to .gitignore and keep it secure!" 