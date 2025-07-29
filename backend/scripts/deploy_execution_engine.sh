#!/bin/bash

# Deployment script for Playwright Execution Engine
# This script builds and deploys the execution engine to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-testpilotai-467409}"
REGION="${REGION:-us-central1}"
ENVIRONMENT="${ENVIRONMENT:-staging}"
SERVICE_NAME="testpilot-ai-execution-engine-${ENVIRONMENT}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/execution-engine:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check if project is set
    if ! gcloud config get-value project &> /dev/null; then
        log_warn "No project set in gcloud config. Setting to ${PROJECT_ID}..."
        gcloud config set project ${PROJECT_ID}
    fi
    
    log_info "Prerequisites check passed."
}

# Build the container image
build_image() {
    log_info "Building container image: ${IMAGE_NAME}"
    
    # Build the image
    docker build -f Dockerfile.execution -t ${IMAGE_NAME} .
    
    if [ $? -eq 0 ]; then
        log_info "Container image built successfully."
    else
        log_error "Failed to build container image."
        exit 1
    fi
}

# Push the container image
push_image() {
    log_info "Pushing container image to Google Container Registry..."
    
    # Configure docker to use gcloud as a credential helper
    gcloud auth configure-docker
    
    # Push the image
    docker push ${IMAGE_NAME}
    
    if [ $? -eq 0 ]; then
        log_info "Container image pushed successfully."
    else
        log_error "Failed to push container image."
        exit 1
    fi
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    # Deploy the service
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_NAME} \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --memory 4Gi \
        --cpu 2 \
        --timeout 900 \
        --max-instances 10 \
        --set-env-vars "ENVIRONMENT=${ENVIRONMENT},LOG_LEVEL=INFO" \
        --service-account "testpilot-ai-execution-engine-${ENVIRONMENT}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    if [ $? -eq 0 ]; then
        log_info "Deployment to Cloud Run completed successfully."
        
        # Get the service URL
        SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")
        log_info "Service URL: ${SERVICE_URL}"
    else
        log_error "Failed to deploy to Cloud Run."
        exit 1
    fi
}

# Run health check
health_check() {
    log_info "Running health check..."
    
    # Wait a moment for the service to be ready
    sleep 10
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")
    
    # Test the health endpoint
    if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
        log_info "Health check passed."
    else
        log_warn "Health check failed. The service might still be starting up."
    fi
}

# Clean up old images (optional)
cleanup_old_images() {
    log_info "Cleaning up old images..."
    
    # Keep only the last 5 images
    gcloud container images list-tags gcr.io/${PROJECT_ID}/execution-engine --limit=5 --sort-by=~timestamp --format="value(digest)" | tail -n +6 | xargs -I {} gcloud container images delete gcr.io/${PROJECT_ID}/execution-engine@{} --quiet || true
}

# Main deployment function
main() {
    log_info "Starting deployment of Playwright Execution Engine..."
    log_info "Project ID: ${PROJECT_ID}"
    log_info "Region: ${REGION}"
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Service Name: ${SERVICE_NAME}"
    log_info "Image Name: ${IMAGE_NAME}"
    
    # Run deployment steps
    check_prerequisites
    build_image
    push_image
    deploy_to_cloud_run
    health_check
    cleanup_old_images
    
    log_info "Deployment completed successfully!"
    log_info "Service URL: $(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --project-id PROJECT_ID    Google Cloud project ID"
            echo "  --region REGION           Google Cloud region"
            echo "  --environment ENVIRONMENT Environment (staging/production)"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main 