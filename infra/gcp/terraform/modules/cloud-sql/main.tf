# Cloud SQL Module for GCP
# Creates a PostgreSQL instance with private networking

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id
  
  # Instance settings
  settings {
    tier                        = var.instance_tier
    disk_type                   = "PD_SSD"
    disk_size                   = var.disk_size_gb
    disk_autoresize             = true
    disk_autoresize_limit       = var.disk_size_gb * 2
    availability_type           = var.environment == "production" ? "REGIONAL" : "ZONAL"
    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = var.environment == "production" ? 7 : 3
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 7 : 3
      }
    }
    
    # Maintenance window
    maintenance_window {
      day          = 7  # Sunday
      hour         = 3  # 3 AM
      update_track = "stable"
    }
    
    # IP configuration - private IP only
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_network_self_link
      ssl_mode        = "ENCRYPTED_ONLY"
    }
    
    # Database flags for performance
    database_flags {
      name  = "max_connections"
      value = var.environment == "production" ? "200" : "100"
    }
    
    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking more than 1 second
    }
    
    # User labels
    user_labels = {
      environment = var.environment
      project     = var.project_name
      managed_by  = "terraform"
    }
  }
  
  # Deletion protection for production
  deletion_protection = var.environment == "production"
  
  lifecycle {
    prevent_destroy = false  # Allow destruction for staging
  }
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
  
  charset   = "UTF8"
  collation = "en_US.UTF8"
}

# Database user
resource "google_sql_user" "user" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
  
  password = var.database_password
  
  # Use IAM authentication if available
  type = "BUILT_IN"
}

# Cloud SQL Admin API user (for application connections)
resource "google_sql_user" "app_user" {
  name     = "${var.database_user}_app"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
  
  password = var.app_password
  
  type = "BUILT_IN"
}

# Cloud SQL Proxy service account (for secure connections)
resource "google_service_account" "sql_proxy" {
  account_id   = "${var.project_name}-sql-proxy-${var.environment}"
  display_name = "Cloud SQL Proxy Service Account for ${var.environment}"
  project      = var.project_id
}

# Grant Cloud SQL Client role to the service account
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.sql_proxy.email}"
}

# Grant Cloud SQL Instance User role to the service account
resource "google_project_iam_member" "sql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.sql_proxy.email}"
} 