# Playwright Execution Engine Cloud Run Module
# This module deploys the execution engine as a Cloud Run service

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Cloud Run service for the execution engine
resource "google_cloud_run_service" "execution_engine" {
  name     = "${var.project_name}-execution-engine-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image
        
        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        env {
          name  = "PLAYWRIGHT_TIMEOUT"
          value = var.playwright_timeout
        }

        env {
          name  = "ARTIFACT_BUCKET"
          value = var.artifact_bucket
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "LOG_LEVEL"
          value = var.log_level
        }

        # Port configuration for Cloud Run
        ports {
          container_port = 8080
        }
      }

      # Service account for the execution engine
      service_account_name = google_service_account.execution_engine.email

      # Timeout configuration
      timeout_seconds = var.timeout_seconds
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_scale
        "autoscaling.knative.dev/maxScale" = var.max_scale
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Service account for the execution engine
resource "google_service_account" "execution_engine" {
  account_id   = "${var.project_name}-execution-engine-${var.environment}"
  display_name = "Playwright Execution Engine Service Account"
  description  = "Service account for the Playwright execution engine"
}

# IAM bindings for the service account
resource "google_project_iam_binding" "execution_engine_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  members = [
    "serviceAccount:${google_service_account.execution_engine.email}"
  ]
}

resource "google_project_iam_binding" "execution_engine_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  members = [
    "serviceAccount:${google_service_account.execution_engine.email}"
  ]
}

# Cloud Run service IAM - allow unauthenticated invocations
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_service.execution_engine.location
  service  = google_cloud_run_service.execution_engine.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run service IAM - allow authenticated invocations
resource "google_cloud_run_service_iam_member" "authenticated_access" {
  count    = var.allow_authenticated ? 1 : 0
  location = google_cloud_run_service.execution_engine.location
  service  = google_cloud_run_service.execution_engine.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Scheduler job for periodic health checks (optional)
resource "google_cloud_scheduler_job" "execution_engine_health_check" {
  count         = var.enable_health_checks ? 1 : 0
  name          = "${var.project_name}-execution-engine-health-${var.environment}"
  description   = "Periodic health check for execution engine"
  schedule      = "*/5 * * * *"  # Every 5 minutes
  time_zone     = "UTC"
  attempt_deadline = "600s"

  http_target {
    http_method = "GET"
    uri         = "${google_cloud_run_service.execution_engine.status[0].url}/health"

    headers = {
      "User-Agent" = "Google-Cloud-Scheduler"
    }
  }
} 