# Cloud Run Module for GCP
# Deploys containerized applications to Cloud Run

# Service account for Cloud Run service
resource "google_service_account" "cloud_run" {
  account_id   = "${var.project_name}-cloud-run-${var.environment}"
  display_name = "Cloud Run Service Account for ${var.environment}"
  project      = var.project_id
}

# Grant Cloud Run Invoker role to allow unauthenticated access (if needed)
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_service.service.location
  project  = google_cloud_run_service.service.project
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant Cloud Run Invoker role to specific service account (if needed)
resource "google_cloud_run_service_iam_member" "service_account_access" {
  count    = var.invoker_service_account != null ? 1 : 0
  location = google_cloud_run_service.service.location
  project  = google_cloud_run_service.service.project
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.invoker_service_account}"
}

# Cloud Run service
resource "google_cloud_run_service" "service" {
  name     = "${var.project_name}-${var.service_name}-${var.environment}"
  location = var.region
  project  = var.project_id
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_scale
        "autoscaling.knative.dev/maxScale" = var.max_scale
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/cpu-throttling" = "false"
        "run.googleapis.com/startup-cpu-boost" = "true"
      }
    }
    
    spec {
      service_account_name = google_service_account.cloud_run.email
      
      containers {
        image = var.container_image
        
        ports {
          container_port = var.container_port
        }
        
        # Environment variables
        dynamic "env" {
          for_each = var.environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }
        
        # Secret environment variables
        dynamic "env" {
          for_each = var.secret_environment_variables
          content {
            name = env.key
            value_from {
              secret_key_ref {
                name = env.value.secret_name
                key  = env.value.secret_key
              }
            }
          }
        }
        
        # Resource limits
        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
          requests = {
            cpu    = var.cpu_request
            memory = var.memory_request
          }
        }
        
        # Health check
        liveness_probe {
          http_get {
            path = var.health_check_path
          }
          initial_delay_seconds = 30
          period_seconds        = 10
          timeout_seconds       = 5
          failure_threshold     = 3
        }
        
        readiness_probe {
          http_get {
            path = var.health_check_path
          }
          initial_delay_seconds = 5
          period_seconds        = 5
          timeout_seconds       = 3
          failure_threshold     = 3
        }
      }
      
      # VPC connector for private networking (if enabled)
      dynamic "vpc_access" {
        for_each = var.vpc_connector != null ? [1] : []
        content {
          connector = var.vpc_connector
          egress    = "ALL_TRAFFIC"
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  # Metadata
  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }
}

# Cloud Run service for backend (if different from frontend)
resource "google_cloud_run_service" "backend" {
  count    = var.deploy_backend ? 1 : 0
  name     = "${var.project_name}-backend-${var.environment}"
  location = var.region
  project  = var.project_id
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.backend_min_scale
        "autoscaling.knative.dev/maxScale" = var.backend_max_scale
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/cpu-throttling" = "false"
        "run.googleapis.com/startup-cpu-boost" = "true"
      }
    }
    
    spec {
      service_account_name = google_service_account.cloud_run.email
      
      containers {
        image = var.backend_container_image
        
        ports {
          container_port = var.backend_container_port
        }
        
        # Environment variables for backend
        dynamic "env" {
          for_each = var.backend_environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }
        
        # Secret environment variables for backend
        dynamic "env" {
          for_each = var.backend_secret_environment_variables
          content {
            name = env.key
            value_from {
              secret_key_ref {
                name = env.value.secret_name
                key  = env.value.secret_key
              }
            }
          }
        }
        
        # Resource limits for backend
        resources {
          limits = {
            cpu    = var.backend_cpu_limit
            memory = var.backend_memory_limit
          }
          requests = {
            cpu    = var.backend_cpu_request
            memory = var.backend_memory_request
          }
        }
        
        # Health check for backend
        liveness_probe {
          http_get {
            path = var.backend_health_check_path
          }
          initial_delay_seconds = 30
          period_seconds        = 10
          timeout_seconds       = 5
          failure_threshold     = 3
        }
        
        readiness_probe {
          http_get {
            path = var.backend_health_check_path
          }
          initial_delay_seconds = 5
          period_seconds        = 5
          timeout_seconds       = 3
          failure_threshold     = 3
        }
      }
      
      # VPC connector for backend
      dynamic "vpc_access" {
        for_each = var.vpc_connector != null ? [1] : []
        content {
          connector = var.vpc_connector
          egress    = "ALL_TRAFFIC"
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }
} 