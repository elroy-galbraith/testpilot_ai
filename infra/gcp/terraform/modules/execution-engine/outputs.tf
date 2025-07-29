# Outputs for the Playwright Execution Engine Cloud Run module

output "service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.execution_engine.status[0].url
}

output "service_name" {
  description = "The name of the deployed Cloud Run service"
  value       = google_cloud_run_service.execution_engine.name
}

output "service_location" {
  description = "The location of the deployed Cloud Run service"
  value       = google_cloud_run_service.execution_engine.location
}

output "service_account_email" {
  description = "The email of the service account used by the execution engine"
  value       = google_service_account.execution_engine.email
}

output "service_account_name" {
  description = "The name of the service account used by the execution engine"
  value       = google_service_account.execution_engine.name
}

output "latest_ready_revision_name" {
  description = "The name of the latest ready revision"
  value       = google_cloud_run_service.execution_engine.status[0].latest_ready_revision_name
}

output "latest_ready_revision_url" {
  description = "The URL of the latest ready revision"
  value       = google_cloud_run_service.execution_engine.status[0].latest_ready_revision_name != null ? "${google_cloud_run_service.execution_engine.status[0].url}/executions" : null
} 