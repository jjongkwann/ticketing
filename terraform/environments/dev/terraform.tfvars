environment = "dev"
aws_region  = "us-east-1"

# Smaller instances for dev
eks_node_groups = {
  general = {
    min_size       = 2
    max_size       = 5
    desired_size   = 2
    instance_types = ["t3.medium"]
    capacity_type  = "ON_DEMAND"
    labels         = { workload = "general" }
    taints         = []
  }
}

rds_instance_class   = "db.t3.medium"
rds_multi_az         = false
rds_allocated_storage = 20

redis_node_type         = "cache.t3.medium"
redis_num_cache_clusters = 1

msk_instance_type        = "kafka.t3.small"
msk_number_of_broker_nodes = 1

opensearch_instance_type  = "t3.medium.search"
opensearch_instance_count = 1
