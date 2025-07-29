# Staging Environment Variables

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
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "google_credentials_path" {
  description = "Path to Google service account key file"
  type        = string
  default     = null
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

# Optional variables for future use
variable "frontend_image" {
  description = "Frontend container image"
  type        = string
  default     = ""
}

variable "backend_image" {
  description = "Backend container image"
  type        = string
  default     = ""
} 