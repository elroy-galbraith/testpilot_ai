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

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "frontend"
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}

variable "invoker_service_account" {
  description = "Service account that can invoke the service"
  type        = string
  default     = null
}

variable "min_scale" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_scale" {
  description = "Maximum number of instances"
  type        = number
  default     = 100
}

variable "cpu_limit" {
  description = "CPU limit"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit"
  type        = string
  default     = "512Mi"
}

variable "cpu_request" {
  description = "CPU request"
  type        = string
  default     = "250m"
}

variable "memory_request" {
  description = "Memory request"
  type        = string
  default     = "256Mi"
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/health"
}

variable "environment_variables" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secret_environment_variables" {
  description = "Secret environment variables"
  type = map(object({
    secret_name = string
    secret_key  = string
  }))
  default = {}
}

variable "vpc_connector" {
  description = "VPC connector for private networking"
  type        = string
  default     = null
}

# Backend-specific variables
variable "deploy_backend" {
  description = "Deploy backend service"
  type        = bool
  default     = false
}

variable "backend_container_image" {
  description = "Backend container image URL"
  type        = string
  default     = ""
}

variable "backend_container_port" {
  description = "Backend container port"
  type        = number
  default     = 8000
}

variable "backend_min_scale" {
  description = "Backend minimum number of instances"
  type        = number
  default     = 0
}

variable "backend_max_scale" {
  description = "Backend maximum number of instances"
  type        = number
  default     = 100
}

variable "backend_cpu_limit" {
  description = "Backend CPU limit"
  type        = string
  default     = "2000m"
}

variable "backend_memory_limit" {
  description = "Backend memory limit"
  type        = string
  default     = "1Gi"
}

variable "backend_cpu_request" {
  description = "Backend CPU request"
  type        = string
  default     = "500m"
}

variable "backend_memory_request" {
  description = "Backend memory request"
  type        = string
  default     = "512Mi"
}

variable "backend_health_check_path" {
  description = "Backend health check path"
  type        = string
  default     = "/health"
}

variable "backend_environment_variables" {
  description = "Backend environment variables"
  type        = map(string)
  default     = {}
}

variable "backend_secret_environment_variables" {
  description = "Backend secret environment variables"
  type = map(object({
    secret_name = string
    secret_key  = string
  }))
  default = {}
} 