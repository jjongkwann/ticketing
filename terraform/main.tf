# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, i + length(var.availability_zones))]
  database_subnets = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, i + 2 * length(var.availability_zones))]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "dev" ? true : false
  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.eks_cluster_version

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  # IRSA (IAM Roles for Service Accounts)
  enable_irsa = true

  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_irsa.iam_role_arn
    }
  }

  # Managed node groups
  eks_managed_node_groups = {
    for k, v in var.eks_node_groups : k => {
      min_size       = v.min_size
      max_size       = v.max_size
      desired_size   = v.desired_size
      instance_types = v.instance_types
      capacity_type  = v.capacity_type

      labels = v.labels
      taints = v.taints

      iam_role_additional_policies = {
        AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
      }

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 100
            volume_type           = "gp3"
            iops                  = 3000
            throughput            = 150
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }
  }

  # aws-auth configmap
  manage_aws_auth_configmap = true

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

# EBS CSI Driver IRSA
module "ebs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "${var.project_name}-${var.environment}-ebs-csi"

  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = {
    Environment = var.environment
  }
}

# DynamoDB Tables
module "dynamodb" {
  source = "./modules/dynamodb"

  environment  = var.environment
  project_name = var.project_name
  billing_mode = var.dynamodb_billing_mode
}

# RDS MySQL
module "rds" {
  source = "./modules/rds"

  environment        = var.environment
  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.database_subnets
  instance_class     = var.rds_instance_class
  allocated_storage  = var.rds_allocated_storage
  multi_az           = var.rds_multi_az
  allowed_cidr_blocks = module.vpc.private_subnets_cidr_blocks
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"

  environment         = var.environment
  project_name        = var.project_name
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnets
  node_type           = var.redis_node_type
  num_cache_clusters  = var.redis_num_cache_clusters
  allowed_cidr_blocks = module.vpc.private_subnets_cidr_blocks
}

# MSK Kafka
module "msk" {
  source = "./modules/msk"

  environment              = var.environment
  project_name             = var.project_name
  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  kafka_version            = var.msk_kafka_version
  instance_type            = var.msk_instance_type
  number_of_broker_nodes   = var.msk_number_of_broker_nodes
  allowed_cidr_blocks      = module.vpc.private_subnets_cidr_blocks
}

# OpenSearch
module "opensearch" {
  source = "./modules/opensearch"

  environment        = var.environment
  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = slice(module.vpc.private_subnets, 0, var.opensearch_instance_count)
  instance_type      = var.opensearch_instance_type
  instance_count     = var.opensearch_instance_count
  opensearch_version = var.opensearch_version
  allowed_cidr_blocks = module.vpc.private_subnets_cidr_blocks
}
