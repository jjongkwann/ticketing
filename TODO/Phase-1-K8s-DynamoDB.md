# Phase 1: Kubernetes & DynamoDB Infrastructure (Production)

## 📋 Overview
Set up production-grade infrastructure on AWS with Kubernetes (EKS), DynamoDB tables, Redis cluster, Elasticsearch, and Kafka. Configure monitoring with Datadog, Prometheus, and Grafana.

## 🎯 Objectives
- **Kubernetes (EKS)**: Multi-AZ cluster with auto-scaling
- **DynamoDB**: Tables for seats, reservations, bookings with DynamoDB Streams
- **MySQL (RDS)**: Events and user data
- **Redis (ElastiCache)**: Distributed locks and caching
- **Elasticsearch (Amazon OpenSearch)**: Event search
- **Kafka (MSK)**: Event streaming and CDC
- **Monitoring**: Datadog, Prometheus, Grafana, Loki

## 👥 Agents Involved
- **cloud-architect**: AWS infrastructure design
- **devops-engineer**: Kubernetes setup, Helm charts
- **database-admin**: DynamoDB table design, MySQL schemas

---

## 📝 Tasks

### T1.1: Design AWS Infrastructure Architecture
**Agent**: `cloud-architect`
**Status**: ⏳ Pending

**AWS Services**:
```
┌─────────────────────────────────────────────────────┐
│                  Route 53 (DNS)                     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│         ALB (Application Load Balancer)             │
│         (SSL termination, path routing)             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  EKS Cluster                        │
│  ┌────────────┬────────────┬────────────────────┐   │
│  │ API Gateway│  Services  │ Inventory Service  │   │
│  │  (FastAPI) │ (FastAPI)  │      (Go)          │   │
│  └────────────┴────────────┴────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
┌────▼──────┐  ┌───────▼────────┐   ┌────▼──────┐
│ DynamoDB  │  │ RDS (MySQL)    │   │  Redis    │
│ (Seats,   │  │ (Events,Users) │   │ElastiCache│
│ Bookings) │  └────────────────┘   │ (Locks)   │
└───────────┘          │            └───────────┘
     │                 │
     │           DynamoDB Streams
     │                 │
     └────────┬────────┘
              │
      ┌───────▼────────┐
      │ MSK (Kafka)    │
      │  CDC Pipeline  │
      └────────┬───────┘
               │
      ┌────────▼────────┐
      │  OpenSearch     │
      │ (Elasticsearch) │
      └─────────────────┘
```

**Key Decisions**:
- Multi-AZ deployment (us-east-1a, us-east-1b, us-east-1c)
- EKS cluster with managed node groups
- DynamoDB on-demand pricing (or provisioned with auto-scaling)
- RDS Multi-AZ for high availability
- Redis Cluster mode for distributed locking
- MSK for Kafka (managed)

**Expected Output**:
- Infrastructure diagram
- AWS cost estimate
- Network topology (VPC, subnets, security groups)
- IAM roles and policies

---

### T1.2: Setup Kubernetes (EKS) Cluster
**Agent**: `devops-engineer`
**Status**: ⏳ Pending

**Cluster Configuration** (`terraform/eks-cluster.tf`):

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "ticketing-prod"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Managed node groups
  eks_managed_node_groups = {
    general = {
      min_size     = 3
      max_size     = 20
      desired_size = 5

      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"

      labels = {
        workload = "general"
      }
    }

    inventory = {
      min_size     = 5
      max_size     = 50
      desired_size = 10

      instance_types = ["c5.xlarge"]  # CPU-optimized for Go
      capacity_type  = "SPOT"  # 70% cost savings

      labels = {
        workload = "inventory"
      }

      taints = [{
        key    = "workload"
        value  = "inventory"
        effect = "NoSchedule"
      }]
    }
  }

  # Enable IRSA (IAM Roles for Service Accounts)
  enable_irsa = true

  tags = {
    Environment = "production"
    Terraform   = "true"
  }
}
```

**Helm Charts** (`helm/values-prod.yaml`):

```yaml
# Ingress Controller (AWS ALB)
aws-load-balancer-controller:
  clusterName: ticketing-prod
  serviceAccount:
    create: true
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/aws-load-balancer-controller

# Metrics Server
metrics-server:
  enabled: true

# Cluster Autoscaler
cluster-autoscaler:
  autoDiscovery:
    clusterName: ticketing-prod
  awsRegion: us-east-1
```

**Success Criteria**:
- [ ] EKS cluster running with 3+ nodes
- [ ] kubectl access configured
- [ ] Ingress controller deployed
- [ ] Cluster autoscaler working
- [ ] Pod → AWS resources connectivity verified

---

### T1.3: Create DynamoDB Tables
**Agent**: `database-admin`
**Status**: ⏳ Pending

**Terraform Configuration** (`terraform/dynamodb.tf`):

```hcl
# Table 1: Seats
resource "aws_dynamodb_table" "seats" {
  name           = "seats-prod"
  billing_mode   = "PAY_PER_REQUEST"  # or PROVISIONED
  hash_key       = "event_id"
  range_key      = "seat_number"

  attribute {
    name = "event_id"
    type = "N"
  }

  attribute {
    name = "seat_number"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "status-index"
    hash_key        = "event_id"
    range_key       = "status"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "seats-prod"
    Environment = "production"
  }
}

# Table 2: Reservations
resource "aws_dynamodb_table" "reservations" {
  name           = "reservations-prod"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "reservation_id"

  attribute {
    name = "reservation_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "expires_at"
    type = "N"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "user-reservations-index"
    hash_key        = "user_id"
    range_key       = "expires_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "expiry-index"
    hash_key        = "status"
    range_key       = "expires_at"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }
}

# Table 3: Bookings
resource "aws_dynamodb_table" "bookings" {
  name           = "bookings-prod"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_id"

  attribute {
    name = "booking_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "booking_reference"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  global_secondary_index {
    name            = "user-bookings-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "reference-index"
    hash_key        = "booking_reference"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  point_in_time_recovery {
    enabled = true
  }
}
```

**DynamoDB Auto-Scaling** (if using PROVISIONED mode):

```hcl
resource "aws_appautoscaling_target" "seats_read" {
  max_capacity       = 1000
  min_capacity       = 5
  resource_id        = "table/${aws_dynamodb_table.seats.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "seats_read_policy" {
  name               = "DynamoDBReadCapacityUtilization:${aws_appautoscaling_target.seats_read.resource_id}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.seats_read.resource_id
  scalable_dimension = aws_appautoscaling_target.seats_read.scalable_dimension
  service_namespace  = aws_appautoscaling_target.seats_read.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = 70.0
  }
}
```

---

### T1.4: Setup MySQL (RDS)
**Agent**: `database-admin`
**Status**: ⏳ Pending

```hcl
resource "aws_db_instance" "ticketing" {
  identifier = "ticketing-prod"

  engine            = "mysql"
  engine_version    = "8.0.35"
  instance_class    = "db.r6g.xlarge"
  allocated_storage = 100

  db_name  = "ticketing_main"
  username = "admin"
  password = random_password.db_password.result

  multi_az               = true
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]

  performance_insights_enabled = true

  tags = {
    Name        = "ticketing-prod"
    Environment = "production"
  }
}
```

**MySQL Schemas**:
```sql
-- Run via migration tool (Flyway or Liquibase)
CREATE DATABASE ticketing_main;

USE ticketing_main;

CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email)
) ENGINE=InnoDB;

CREATE TABLE events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    venue_name VARCHAR(255),
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    sale_start_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_event_date (event_date)
) ENGINE=InnoDB;

CREATE TABLE outbox_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    aggregate_id BIGINT NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    INDEX idx_processed_created (processed, created_at)
) ENGINE=InnoDB;
```

---

### T1.5: Setup Redis (ElastiCache)
**Agent**: `devops-engineer`
**Status**: ⏳ Pending

```hcl
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "ticketing-redis-cluster"
  replication_group_description = "Redis cluster for distributed locks and caching"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.r6g.large"
  number_cache_clusters = 3  # 1 primary + 2 replicas
  port                 = 6379

  parameter_group_name = "default.redis7.cluster.on"
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  automatic_failover_enabled = true
  multi_az_enabled          = true

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"

  tags = {
    Name        = "ticketing-redis"
    Environment = "production"
  }
}
```

---

### T1.6: Setup Kafka (MSK)
**Agent**: `devops-engineer`
**Status**: ⏳ Pending

```hcl
resource "aws_msk_cluster" "ticketing" {
  cluster_name           = "ticketing-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.msk.id]

    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.ticketing.arn
    revision = aws_msk_configuration.ticketing.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }
}

# Kafka Topics (created via Terraform provider or kafka-admin)
resource "kafka_topic" "seat_events" {
  name               = "seat.status.changed"
  replication_factor = 3
  partitions         = 10

  config = {
    "retention.ms" = "86400000"  # 1 day
    "compression.type" = "snappy"
  }
}
```

---

### T1.7: Setup Monitoring Stack
**Agent**: `devops-engineer`
**Status**: ⏳ Pending

**Datadog Agent** (Kubernetes DaemonSet):

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: datadog-agent
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: datadog-agent
  template:
    metadata:
      labels:
        app: datadog-agent
    spec:
      serviceAccountName: datadog-agent
      containers:
      - name: datadog-agent
        image: datadog/agent:latest
        env:
        - name: DD_API_KEY
          valueFrom:
            secretKeyRef:
              name: datadog-secret
              key: api-key
        - name: DD_SITE
          value: "datadoghq.com"
        - name: DD_LOGS_ENABLED
          value: "true"
        - name: DD_APM_ENABLED
          value: "true"
        - name: DD_PROCESS_AGENT_ENABLED
          value: "true"
        - name: DD_KUBERNETES_KUBELET_HOST
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
        volumeMounts:
        - name: dockersocket
          mountPath: /var/run/docker.sock
        - name: procdir
          mountPath: /host/proc
          readOnly: true
        - name: cgroups
          mountPath: /host/sys/fs/cgroup
          readOnly: true
      volumes:
      - name: dockersocket
        hostPath:
          path: /var/run/docker.sock
      - name: procdir
        hostPath:
          path: /proc
      - name: cgroups
        hostPath:
          path: /sys/fs/cgroup
```

**Prometheus** (via kube-prometheus-stack Helm chart):

```yaml
# values-prometheus.yaml
prometheus:
  prometheusSpec:
    retention: 15d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi

grafana:
  adminPassword: <secure-password>
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: alb
    hosts:
      - grafana.ticketing.com
```

---

## 🎯 Phase 1 Success Criteria

- [ ] EKS cluster running (3+ nodes, multi-AZ)
- [ ] DynamoDB tables created with streams enabled
- [ ] MySQL (RDS) accessible from EKS
- [ ] Redis cluster (ElastiCache) reachable
- [ ] Kafka (MSK) cluster running
- [ ] Datadog agent collecting metrics/logs
- [ ] Prometheus scraping metrics
- [ ] All infrastructure as code (Terraform)

## 📊 Estimated Timeline
**3-5 days** (with Terraform automation)

## 🔗 Next Phase
[Phase 3: Go Inventory Service (DynamoDB)](./Phase-3-Inventory-DynamoDB.md)

---

## 📌 Notes
- Use Terraform workspaces for staging/production
- Enable AWS CloudTrail for audit logging
- Configure VPC Flow Logs for network monitoring
- Use AWS Secrets Manager for sensitive data
- Set up AWS Backup for automated backups
