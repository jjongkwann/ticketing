# Ticketing System - Terraform Infrastructure

AWS infrastructure for production-grade ticketing system.

## Infrastructure Components

- **EKS** - Kubernetes cluster with managed node groups
- **DynamoDB** - Seats, Reservations, Bookings tables
- **RDS MySQL** - Events, Users data
- **ElastiCache Redis** - Distributed locks and caching
- **MSK (Kafka)** - Event streaming
- **OpenSearch** - Event search

## Directory Structure

```
terraform/
├── main.tf           # Main configuration
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── versions.tf       # Provider versions
├── modules/
│   ├── dynamodb/     # DynamoDB tables
│   ├── rds/          # MySQL RDS
│   ├── redis/        # ElastiCache Redis
│   ├── msk/          # MSK Kafka
│   └── opensearch/   # OpenSearch
└── environments/
    ├── dev/          # Dev environment config
    └── prod/         # Prod environment config
```

## Prerequisites

```bash
# Install Terraform
brew install terraform

# Configure AWS credentials
aws configure

# Install kubectl
brew install kubectl
```

## Usage

### Development Environment

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan infrastructure
terraform plan -var-file=environments/dev/terraform.tfvars

# Apply infrastructure
terraform apply -var-file=environments/dev/terraform.tfvars

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name ticketing-dev
```

### Production Environment

```bash
cd terraform

# Use separate state for production
terraform init -backend-config=environments/prod/backend.hcl

# Plan
terraform plan -var-file=environments/prod/terraform.tfvars

# Apply with approval
terraform apply -var-file=environments/prod/terraform.tfvars
```

## Outputs

After applying, Terraform will output:

- EKS cluster name and endpoint
- DynamoDB table names
- RDS endpoint
- Redis endpoint
- MSK bootstrap brokers
- OpenSearch endpoint

## Cost Estimate

### Development (~$200/month)
- EKS: ~$75
- RDS t3.medium: ~$30
- Redis t3.medium: ~$15
- MSK t3.small: ~$50
- OpenSearch t3.medium: ~$30

### Production (~$1,500/month)
- EKS: ~$150
- RDS r6g.xlarge Multi-AZ: ~$400
- Redis r6g.large cluster: ~$200
- MSK m5.large (3 nodes): ~$450
- OpenSearch r6g.large (3 nodes): ~$300

## Security

- All traffic encrypted in transit (TLS)
- Encryption at rest enabled
- VPC isolation
- Security groups restrict access
- Secrets stored in AWS Secrets Manager
