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

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]
}

variable "enable_vpc_connector" {
  description = "Enable VPC connector for Cloud Run"
  type        = bool
  default     = false
}

variable "vpc_connector_cidr" {
  description = "CIDR block for VPC connector"
  type        = string
  default     = "10.8.0.0/28"
} 