environment = "prod"
aws_region  = "us-east-1"

# Production-grade instances
eks_node_groups = {
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

rds_instance_class   = "db.r6g.xlarge"
rds_multi_az         = true
rds_allocated_storage = 100

redis_node_type         = "cache.r6g.large"
redis_num_cache_clusters = 3

msk_instance_type        = "kafka.m5.large"
msk_number_of_broker_nodes = 3

opensearch_instance_type  = "r6g.large.search"
opensearch_instance_count = 3
