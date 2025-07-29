# Staging Environment Configuration
# TestPilot AI - GCP Infrastructure

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
  
  # Use service account key if provided
  credentials = var.google_credentials_path != null ? file(var.google_credentials_path) : null
}

# Data sources
data "google_project" "current" {}
data "google_compute_network" "default" {
  name = "default"
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  project_id = var.project_id
  project_name = var.project_name
  environment = var.environment
  region = var.region
  
  # Enable VPC connector for Cloud Run
  enable_vpc_connector = true
}

# Cloud SQL Module
module "cloud_sql" {
  source = "../../modules/cloud-sql"
  
  project_id = var.project_id
  project_name = var.project_name
  environment = var.environment
  region = var.region
  
  vpc_network_self_link = module.vpc.vpc_self_link
  
  # Use smaller instance for staging
  instance_tier = "db-f1-micro"  # Free tier
  disk_size_gb = 10
  
  # Database credentials (should be stored in Secret Manager in production)
  database_password = var.database_password
  app_password = var.app_password
}

# Cloud Storage Module (placeholder for now)
# module "storage" {
#   source = "../../modules/storage"
#   
#   project_id = var.project_id
#   project_name = var.project_name
#   environment = var.environment
#   region = var.region
# }

# Cloud Run Module (placeholder for now)
# module "cloud_run" {
#   source = "../../modules/cloud-run"
#   
#   project_id = var.project_id
#   project_name = var.project_name
#   environment = var.environment
#   region = var.region
#   
#   container_image = var.frontend_image
#   vpc_connector = module.vpc.vpc_connector_name
#   
#   deploy_backend = true
#   backend_container_image = var.backend_image
#   backend_environment_variables = {
#     DATABASE_URL = module.cloud_sql.connection_string
#     REDIS_URL = module.memorystore.redis_url
#   }
# }

# Memorystore Module (placeholder for now)
# module "memorystore" {
#   source = "../../modules/memorystore"
#   
#   project_id = var.project_id
#   project_name = var.project_name
#   environment = var.environment
#   region = var.region
#   
#   vpc_self_link = module.vpc.vpc_self_link
# }

# Outputs
output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "vpc_name" {
  description = "VPC name"
  value       = module.vpc.vpc_name
}

output "vpc_connector_name" {
  description = "VPC connector name"
  value       = module.vpc.vpc_connector_name
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.cloud_sql.instance_name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloud_sql.instance_connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = module.cloud_sql.private_ip_address
  sensitive   = true
} 