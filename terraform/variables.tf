variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ticketing"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# EKS
variable "eks_cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

variable "eks_node_groups" {
  description = "EKS managed node groups configuration"
  type = map(object({
    min_size       = number
    max_size       = number
    desired_size   = number
    instance_types = list(string)
    capacity_type  = string
    labels         = map(string)
    taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
  }))
  default = {
    general = {
      min_size       = 3
      max_size       = 20
      desired_size   = 5
      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
      labels         = { workload = "general" }
      taints         = []
    }
    inventory = {
      min_size       = 5
      max_size       = 50
      desired_size   = 10
      instance_types = ["c5.xlarge"]
      capacity_type  = "SPOT"
      labels         = { workload = "inventory" }
      taints = [{
        key    = "workload"
        value  = "inventory"
        effect = "NoSchedule"
      }]
    }
  }
}

# RDS
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_multi_az" {
  description = "Enable RDS Multi-AZ"
  type        = bool
  default     = true
}

# ElastiCache Redis
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_cache_clusters" {
  description = "Number of cache clusters (1 primary + N replicas)"
  type        = number
  default     = 3
}

# DynamoDB
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

# MSK Kafka
variable "msk_instance_type" {
  description = "MSK Kafka instance type"
  type        = string
  default     = "kafka.m5.large"
}

variable "msk_number_of_broker_nodes" {
  description = "Number of Kafka broker nodes"
  type        = number
  default     = 3
}

variable "msk_kafka_version" {
  description = "Kafka version"
  type        = string
  default     = "3.5.1"
}

# OpenSearch
variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "r6g.large.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 3
}

variable "opensearch_version" {
  description = "OpenSearch version"
  type        = string
  default     = "2.9"
}
