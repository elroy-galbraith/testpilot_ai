variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "testpilot-ai"
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "vpc_network_self_link" {
  description = "VPC network self link for private networking"
  type        = string
}

variable "instance_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"  # Free tier for staging, upgrade for production
}

variable "disk_size_gb" {
  description = "Disk size in GB"
  type        = number
  default     = 10
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "testpilot"
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "testpilot_user"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "app_password" {
  description = "Application database password"
  type        = string
  sensitive   = true
} 