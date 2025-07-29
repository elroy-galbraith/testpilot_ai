output "vpc_id" {
  description = "VPC ID"
  value       = google_compute_network.vpc.id
}

output "vpc_name" {
  description = "VPC name"
  value       = google_compute_network.vpc.name
}

output "vpc_self_link" {
  description = "VPC self link"
  value       = google_compute_network.vpc.self_link
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = google_compute_subnetwork.private[*].id
}

output "private_subnet_names" {
  description = "Private subnet names"
  value       = google_compute_subnetwork.private[*].name
}

output "private_subnet_self_links" {
  description = "Private subnet self links"
  value       = google_compute_subnetwork.private[*].self_link
}

output "router_id" {
  description = "Cloud Router ID"
  value       = google_compute_router.router.id
}

output "router_name" {
  description = "Cloud Router name"
  value       = google_compute_router.router.name
}

output "nat_id" {
  description = "Cloud NAT ID"
  value       = google_compute_router_nat.nat.id
}

output "nat_name" {
  description = "Cloud NAT name"
  value       = google_compute_router_nat.nat.name
}

output "vpc_connector_id" {
  description = "VPC Connector ID (if enabled)"
  value       = var.enable_vpc_connector ? google_vpc_access_connector.connector[0].id : null
}

output "vpc_connector_name" {
  description = "VPC Connector name (if enabled)"
  value       = var.enable_vpc_connector ? google_vpc_access_connector.connector[0].name : null
}

output "private_vpc_connection_id" {
  description = "Private VPC connection ID"
  value       = google_service_networking_connection.private_vpc_connection.id
} 