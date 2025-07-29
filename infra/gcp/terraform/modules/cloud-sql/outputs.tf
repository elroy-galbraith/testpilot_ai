output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "instance_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "private_ip_address" {
  description = "Private IP address of the instance"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "Database user name"
  value       = google_sql_user.user.name
}

output "app_user" {
  description = "Application database user name"
  value       = google_sql_user.app_user.name
}

output "sql_proxy_service_account_email" {
  description = "Cloud SQL Proxy service account email"
  value       = google_service_account.sql_proxy.email
}

output "connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql://${google_sql_user.user.name}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.database.name}"
  sensitive   = true
} 