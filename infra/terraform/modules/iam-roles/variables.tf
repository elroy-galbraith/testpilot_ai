variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for RDS access policy conditions"
  type        = string
}

variable "rds_resource_id" {
  description = "RDS resource ID for database user access"
  type        = string
  default     = ""
} 