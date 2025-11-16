output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

# EKS Outputs
output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# DynamoDB Outputs
output "dynamodb_seats_table_name" {
  description = "DynamoDB seats table name"
  value       = module.dynamodb.seats_table_name
}

output "dynamodb_reservations_table_name" {
  description = "DynamoDB reservations table name"
  value       = module.dynamodb.reservations_table_name
}

output "dynamodb_bookings_table_name" {
  description = "DynamoDB bookings table name"
  value       = module.dynamodb.bookings_table_name
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.database_name
}

# Redis Outputs
output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.redis.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = module.redis.reader_endpoint_address
}

# MSK Outputs
output "msk_bootstrap_brokers" {
  description = "MSK bootstrap brokers"
  value       = module.msk.bootstrap_brokers_tls
  sensitive   = true
}

output "msk_zookeeper_connect_string" {
  description = "MSK ZooKeeper connection string"
  value       = module.msk.zookeeper_connect_string
  sensitive   = true
}

# OpenSearch Outputs
output "opensearch_endpoint" {
  description = "OpenSearch endpoint"
  value       = module.opensearch.endpoint
}

output "opensearch_kibana_endpoint" {
  description = "OpenSearch Dashboards endpoint"
  value       = module.opensearch.kibana_endpoint
}
