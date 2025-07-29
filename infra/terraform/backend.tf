terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration will be set per environment
  # This is a template - actual backend config will be in each env directory
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Variables for backend configuration
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "testpilot-ai"
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

# Backend configuration template
# This will be used in each environment directory with specific values
locals {
  backend_config = {
    bucket         = "${var.project_name}-terraform-state-${var.environment}"
    key            = "terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "${var.project_name}-terraform-locks-${var.environment}"
    encrypt        = true
  }
} 