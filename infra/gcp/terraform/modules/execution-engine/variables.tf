# Variables for the Playwright Execution Engine Cloud Run module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "The environment (staging, production)"
  type        = string
}

variable "region" {
  description = "The GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "The container image URL for the execution engine"
  type        = string
}

variable "cpu_limit" {
  description = "CPU limit for the Cloud Run service"
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for the Cloud Run service"
  type        = string
  default     = "4Gi"
}

variable "playwright_timeout" {
  description = "Default timeout for Playwright tests (milliseconds)"
  type        = string
  default     = "30000"
}

variable "artifact_bucket" {
  description = "GCS bucket for storing test artifacts"
  type        = string
}

variable "timeout_seconds" {
  description = "Request timeout for the Cloud Run service"
  type        = number
  default     = 900  # 15 minutes
}

variable "min_scale" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_scale" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "log_level" {
  description = "Log level for the execution engine"
  type        = string
  default     = "INFO"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the Cloud Run service"
  type        = bool
  default     = false
}

variable "allow_authenticated" {
  description = "Allow authenticated access to the Cloud Run service"
  type        = bool
  default     = true
}

variable "enable_health_checks" {
  description = "Enable periodic health checks via Cloud Scheduler"
  type        = bool
  default     = true
} 