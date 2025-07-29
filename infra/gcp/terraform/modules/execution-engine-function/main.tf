# Playwright Execution Engine Cloud Function Module
# This module deploys the execution engine as a Cloud Function

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Cloud Function for the execution engine
resource "google_cloudfunctions2_function" "execution_engine" {
  name        = "${var.project_name}-execution-engine-${var.environment}"
  location    = var.region
  description = "Playwright test execution engine"

  build_config {
    runtime     = "python311"
    entry_point = "execute_test"
    source {
      storage_source {
        bucket = var.source_bucket
        object = var.source_object
      }
    }
  }

  service_config {
    max_instance_count = var.max_instances
    available_memory   = var.memory
    timeout_seconds    = var.timeout_seconds
    environment_variables = {
      PLAYWRIGHT_TIMEOUT = var.playwright_timeout
      ARTIFACT_BUCKET    = var.artifact_bucket
      ENVIRONMENT        = var.environment
      LOG_LEVEL          = var.log_level
    }
    service_account_email = google_service_account.execution_engine_function.email
  }
}

# Service account for the Cloud Function
resource "google_service_account" "execution_engine_function" {
  account_id   = "${var.project_name}-execution-engine-fn-${var.environment}"
  display_name = "Playwright Execution Engine Function Service Account"
  description  = "Service account for the Playwright execution engine Cloud Function"
}

# IAM bindings for the service account
resource "google_project_iam_binding" "execution_engine_function_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  members = [
    "serviceAccount:${google_service_account.execution_engine_function.email}"
  ]
}

resource "google_project_iam_binding" "execution_engine_function_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  members = [
    "serviceAccount:${google_service_account.execution_engine_function.email}"
  ]
}

# Cloud Function IAM - allow unauthenticated invocations
resource "google_cloudfunctions2_function_iam_member" "public_access" {
  count       = var.allow_unauthenticated ? 1 : 0
  location    = google_cloudfunctions2_function.execution_engine.location
  name        = google_cloudfunctions2_function.execution_engine.name
  role        = "roles/cloudfunctions.invoker"
  member      = "allUsers"
}

# Cloud Function IAM - allow authenticated invocations
resource "google_cloudfunctions2_function_iam_member" "authenticated_access" {
  count       = var.allow_authenticated ? 1 : 0
  location    = google_cloudfunctions2_function.execution_engine.location
  name        = google_cloudfunctions2_function.execution_engine.name
  role        = "roles/cloudfunctions.invoker"
  member      = "allUsers"
}

# Cloud Scheduler job for periodic health checks (optional)
resource "google_cloud_scheduler_job" "execution_engine_function_health_check" {
  count         = var.enable_health_checks ? 1 : 0
  name          = "${var.project_name}-execution-engine-fn-health-${var.environment}"
  description   = "Periodic health check for execution engine function"
  schedule      = "*/5 * * * *"  # Every 5 minutes
  time_zone     = "UTC"
  attempt_deadline = "600s"

  http_target {
    http_method = "GET"
    uri         = "${google_cloudfunctions2_function.execution_engine.url}/health"

    headers = {
      "User-Agent" = "Google-Cloud-Scheduler"
    }
  }
} 