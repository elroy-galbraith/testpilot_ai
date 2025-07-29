# VPC Module for GCP
# Creates a VPC with private subnets, Cloud NAT, and firewall rules

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc-${var.environment}"
  auto_create_subnetworks = false
  routing_mode           = "REGIONAL"
  
  delete_default_routes_on_create = false
  
  lifecycle {
    prevent_destroy = true
  }
}

# Private Subnets
resource "google_compute_subnetwork" "private" {
  count = length(var.private_subnet_cidrs)
  
  name          = "${var.project_name}-private-${var.environment}-${count.index + 1}"
  ip_cidr_range = var.private_subnet_cidrs[count.index]
  region        = var.region
  network       = google_compute_network.vpc.id
  
  # Enable flow logs for network monitoring
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling       = 0.5
    metadata           = "INCLUDE_ALL_METADATA"
  }
  
  # Private Google Access for Cloud SQL and other Google APIs
  private_ip_google_access = true
}

# Cloud Router for NAT
resource "google_compute_router" "router" {
  name    = "${var.project_name}-router-${var.environment}"
  region  = var.region
  network = google_compute_network.vpc.id
  
  bgp {
    asn = 64514
  }
}

# Cloud NAT for outbound internet access
resource "google_compute_router_nat" "nat" {
  name                               = "${var.project_name}-nat-${var.environment}"
  router                            = google_compute_router.router.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  # Log NAT translations for debugging
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rule for internal communication
resource "google_compute_firewall" "internal" {
  name    = "${var.project_name}-internal-${var.environment}"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = var.private_subnet_cidrs
  target_tags   = ["internal"]
  
  description = "Allow internal communication between private subnets"
}

# Firewall rule for Cloud Run to Cloud SQL
resource "google_compute_firewall" "cloud_run_to_sql" {
  name    = "${var.project_name}-cloud-run-to-sql-${var.environment}"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["5432"]  # PostgreSQL
  }
  
  allow {
    protocol = "tcp"
    ports    = ["6379"]  # Redis
  }
  
  source_ranges = var.private_subnet_cidrs
  target_tags   = ["cloud-sql"]
  
  description = "Allow Cloud Run services to access Cloud SQL and Memorystore"
}

# Firewall rule for Cloud Run to Cloud Storage
resource "google_compute_firewall" "cloud_run_to_storage" {
  name    = "${var.project_name}-cloud-run-to-storage-${var.environment}"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["443"]  # HTTPS
  }
  
  source_ranges = var.private_subnet_cidrs
  target_tags   = ["cloud-storage"]
  
  description = "Allow Cloud Run services to access Cloud Storage"
}

# Private Services Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# VPC Connector for Cloud Run (if needed for VPC connectivity)
resource "google_vpc_access_connector" "connector" {
  count = var.enable_vpc_connector ? 1 : 0
  
  name          = "testpilot-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = var.vpc_connector_cidr
  
  machine_type = "e2-micro"
  min_instances = 2
  max_instances = 10
} 