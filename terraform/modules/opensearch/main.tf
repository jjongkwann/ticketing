resource "aws_security_group" "opensearch" {
  name_prefix = "${var.project_name}-opensearch-${var.environment}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
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

resource "aws_opensearch_domain" "main" {
  domain_name    = "${var.project_name}-${var.environment}"
  engine_version = "OpenSearch_${var.opensearch_version}"

  cluster_config {
    instance_type  = var.instance_type
    instance_count = var.instance_count

    zone_awareness_enabled = var.instance_count > 1 ? true : false

    dynamic "zone_awareness_config" {
      for_each = var.instance_count > 1 ? [1] : []
      content {
        availability_zone_count = var.instance_count >= 3 ? 3 : 2
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 100
    iops        = 3000
    throughput  = 125
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.opensearch.id]
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = "admin"
      master_user_password = random_password.opensearch_password.result
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action   = "es:*"
        Resource = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${var.project_name}-${var.environment}/*"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-opensearch-${var.environment}"
    Environment = var.environment
  }
}

resource "random_password" "opensearch_password" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "opensearch_password" {
  name = "${var.project_name}-${var.environment}-opensearch-password"
}

resource "aws_secretsmanager_secret_version" "opensearch_password" {
  secret_id = aws_secretsmanager_secret.opensearch_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.opensearch_password.result
    endpoint = aws_opensearch_domain.main.endpoint
  })
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
