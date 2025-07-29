output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_service.service.name
}

output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_location" {
  description = "Cloud Run service location"
  value       = google_cloud_run_service.service.location
}

output "service_account_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}

output "latest_ready_revision_name" {
  description = "Latest ready revision name"
  value       = google_cloud_run_service.service.status[0].latest_ready_revision_name
}

# Backend outputs
output "backend_service_name" {
  description = "Backend Cloud Run service name"
  value       = var.deploy_backend ? google_cloud_run_service.backend[0].name : null
}

output "backend_service_url" {
  description = "Backend Cloud Run service URL"
  value       = var.deploy_backend ? google_cloud_run_service.backend[0].status[0].url : null
}

output "backend_latest_ready_revision_name" {
  description = "Backend latest ready revision name"
  value       = var.deploy_backend ? google_cloud_run_service.backend[0].status[0].latest_ready_revision_name : null
} 