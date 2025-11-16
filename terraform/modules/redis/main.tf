resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-redis-${var.environment}"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-${var.environment}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-redis-${var.environment}"
  replication_group_description = "Redis cluster for distributed locks and caching"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.node_type
  number_cache_clusters = var.num_cache_clusters
  port                 = 6379
  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  automatic_failover_enabled = var.num_cache_clusters > 1 ? true : false
  multi_az_enabled          = var.num_cache_clusters > 1 ? true : false

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  snapshot_retention_limit = var.environment == "prod" ? 5 : 1
  snapshot_window          = "03:00-05:00"

  tags = {
    Name        = "${var.project_name}-redis-${var.environment}"
    Environment = var.environment
  }
}
