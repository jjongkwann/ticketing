# Production Deployment Guide

## 목차

1. [배포 아키텍처](#배포-아키텍처)
2. [사전 준비](#사전-준비)
3. [AWS 인프라 설정](#aws-인프라-설정)
4. [데이터베이스 설정](#데이터베이스-설정)
5. [백엔드 서비스 배포](#백엔드-서비스-배포)
6. [프론트엔드 배포](#프론트엔드-배포)
7. [모니터링 및 로깅](#모니터링-및-로깅)
8. [보안 설정](#보안-설정)
9. [백업 및 복구](#백업-및-복구)
10. [트러블슈팅](#트러블슈팅)

---

## 배포 아키텍처

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CloudFront (CDN)                     │
│                  SSL/TLS Termination                    │
└────────────┬───────────────────────────┬────────────────┘
             │                           │
      ┌──────▼──────┐           ┌───────▼────────┐
      │   S3        │           │  Application   │
      │  (Static)   │           │  Load Balancer │
      └─────────────┘           └───────┬────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
            ┌───────▼──────┐   ┌───────▼──────┐   ┌───────▼──────┐
            │  ECS Cluster │   │  ECS Cluster │   │  ECS Cluster │
            │  (Services)  │   │  (Services)  │   │  (Services)  │
            └───────┬──────┘   └───────┬──────┘   └───────┬──────┘
                    │                   │                   │
            ┌───────▼───────────────────▼───────────────────▼──────┐
            │                                                       │
            │              VPC (Private Subnets)                    │
            │                                                       │
            │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│
            │  │   RDS   │  │DynamoDB │  │  Redis  │  │OpenSearch││
            │  │(Postgres)│  │         │  │ Cluster │  │         ││
            │  └─────────┘  └─────────┘  └─────────┘  └─────────┘│
            └───────────────────────────────────────────────────────┘
```

### 서비스 구성

| Service | Technology | Instances | Scaling |
|---------|-----------|-----------|---------|
| Frontend | React on S3/CloudFront | N/A | Auto |
| API Gateway | FastAPI on ECS | 2-10 | Auto |
| Auth Service | FastAPI on ECS | 2-8 | Auto |
| Events Service | FastAPI on ECS | 2-8 | Auto |
| Booking Service | FastAPI on ECS | 3-15 | Auto |
| Payment Service | FastAPI on ECS | 2-10 | Auto |
| Search Service | FastAPI on ECS | 2-6 | Auto |
| Notification Service | FastAPI on ECS | 2-6 | Auto |
| Inventory Service | Go on ECS | 3-15 | Auto |

---

## 사전 준비

### 1. AWS 계정 및 권한

**필요한 AWS 서비스:**
- EC2 / ECS
- RDS (PostgreSQL)
- DynamoDB
- ElastiCache (Redis)
- OpenSearch Service
- S3
- CloudFront
- Route 53
- ACM (Certificate Manager)
- Secrets Manager
- CloudWatch
- VPC

**IAM 권한:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "ec2:*",
        "rds:*",
        "dynamodb:*",
        "elasticache:*",
        "s3:*",
        "cloudfront:*",
        "route53:*",
        "acm:*",
        "secretsmanager:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. 도메인 및 SSL 인증서

**도메인 구매:**
- Route 53 또는 외부 도메인 등록 업체

**서브도메인 구조:**
```
ticketing-pro.com              → Frontend (CloudFront)
api.ticketing-pro.com          → API Gateway (ALB)
admin.ticketing-pro.com        → Admin Panel
status.ticketing-pro.com       → Status Page
```

**SSL 인증서 발급 (ACM):**
```bash
aws acm request-certificate \
  --domain-name ticketing-pro.com \
  --subject-alternative-names \
    "*.ticketing-pro.com" \
  --validation-method DNS
```

### 3. 환경 변수 설정

**Secrets Manager에 저장할 민감 정보:**
- Database credentials
- JWT secret keys
- Stripe API keys
- AWS access keys
- Redis passwords

```bash
# JWT Secret 생성 및 저장
aws secretsmanager create-secret \
  --name ticketing/jwt-secret \
  --secret-string "$(openssl rand -base64 32)"

# Stripe Secret Key 저장
aws secretsmanager create-secret \
  --name ticketing/stripe-secret-key \
  --secret-string "sk_live_XXXXXXXX"
```

---

## AWS 인프라 설정

### 1. VPC 생성

```bash
# VPC 생성
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ticketing-vpc}]'

# Public Subnets (2개, Multi-AZ)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ticketing-public-1a}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ticketing-public-1b}]'

# Private Subnets (2개, Multi-AZ)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ticketing-private-1a}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ticketing-private-1b}]'
```

### 2. Security Groups

**ALB Security Group:**
```bash
aws ec2 create-security-group \
  --group-name ticketing-alb-sg \
  --description "Security group for ALB" \
  --vpc-id vpc-xxxxx

# HTTPS 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

**ECS Tasks Security Group:**
```bash
aws ec2 create-security-group \
  --group-name ticketing-ecs-sg \
  --description "Security group for ECS tasks" \
  --vpc-id vpc-xxxxx

# ALB로부터의 트래픽만 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-yyyyy \
  --protocol tcp \
  --port 8000 \
  --source-group sg-xxxxx
```

### 3. Application Load Balancer

```bash
# ALB 생성
aws elbv2 create-load-balancer \
  --name ticketing-alb \
  --subnets subnet-public-1a subnet-public-1b \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application

# Target Group 생성 (각 서비스별로)
aws elbv2 create-target-group \
  --name ticketing-api-gateway-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path /health

# Listener 생성
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

## 데이터베이스 설정

### 1. RDS PostgreSQL

```bash
# DB Subnet Group 생성
aws rds create-db-subnet-group \
  --db-subnet-group-name ticketing-db-subnet \
  --db-subnet-group-description "Subnet group for Ticketing DB" \
  --subnet-ids subnet-private-1a subnet-private-1b

# RDS Instance 생성
aws rds create-db-instance \
  --db-instance-identifier ticketing-postgres \
  --db-instance-class db.r5.xlarge \
  --engine postgres \
  --engine-version 14.7 \
  --master-username admin \
  --master-user-password <strong-password> \
  --allocated-storage 100 \
  --storage-type gp3 \
  --db-subnet-group-name ticketing-db-subnet \
  --vpc-security-group-ids sg-zzzzz \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --multi-az \
  --storage-encrypted \
  --enable-performance-insights
```

**데이터베이스 초기화:**
```bash
# Auth Service DB
psql -h ticketing-postgres.xxxxx.rds.amazonaws.com -U admin -d postgres
CREATE DATABASE ticketing_auth;
\c ticketing_auth
-- Run migrations
```

### 2. DynamoDB

```bash
# Bookings Table
aws dynamodb create-table \
  --table-name ticketing-bookings \
  --attribute-definitions \
    AttributeName=booking_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
    AttributeName=event_id,AttributeType=S \
  --key-schema \
    AttributeName=booking_id,KeyType=HASH \
  --global-secondary-indexes \
    '[
      {
        "IndexName": "user-index",
        "KeySchema": [{"AttributeName":"user_id","KeyType":"HASH"}],
        "Projection": {"ProjectionType":"ALL"}
      },
      {
        "IndexName": "event-index",
        "KeySchema": [{"AttributeName":"event_id","KeyType":"HASH"}],
        "Projection": {"ProjectionType":"ALL"}
      }
    ]' \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

### 3. ElastiCache Redis

```bash
# Redis Subnet Group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name ticketing-redis-subnet \
  --cache-subnet-group-description "Subnet group for Redis" \
  --subnet-ids subnet-private-1a subnet-private-1b

# Redis Cluster
aws elasticache create-replication-group \
  --replication-group-id ticketing-redis \
  --replication-group-description "Redis cluster for Ticketing" \
  --engine redis \
  --cache-node-type cache.r5.large \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --cache-subnet-group-name ticketing-redis-subnet \
  --security-group-ids sg-redis \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

### 4. OpenSearch

```bash
# OpenSearch Domain
aws opensearch create-domain \
  --domain-name ticketing-search \
  --engine-version OpenSearch_2.5 \
  --cluster-config \
    InstanceType=r5.large.search,InstanceCount=2,DedicatedMasterEnabled=true,DedicatedMasterType=r5.large.search,DedicatedMasterCount=3 \
  --ebs-options \
    EBSEnabled=true,VolumeType=gp3,VolumeSize=100 \
  --access-policies '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"AWS": "*"},
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/ticketing-search/*"
    }]
  }' \
  --vpc-options SubnetIds=subnet-private-1a,SecurityGroupIds=sg-opensearch
```

---

## 백엔드 서비스 배포

### 1. ECR Repository 생성

```bash
# 각 서비스별 ECR Repository 생성
for service in api-gateway auth events booking payment search notification inventory; do
  aws ecr create-repository \
    --repository-name ticketing/${service} \
    --image-scanning-configuration scanOnPush=true
done
```

### 2. Docker 이미지 빌드 및 푸시

**참고:** Python 서비스는 [uv](https://github.com/astral-sh/uv) 패키지 매니저를 사용합니다.
의존성은 각 서비스의 `pyproject.toml`에 정의되어 있으며, Dockerfile에서 자동으로 설치됩니다.

```bash
# ECR 로그인
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# API Gateway 예시
cd services/api-gateway
docker build -t ticketing/api-gateway:latest .
docker tag ticketing/api-gateway:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/ticketing/api-gateway:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ticketing/api-gateway:latest

# 모든 서비스 반복...
```

### 3. ECS Cluster 생성

```bash
# ECS Cluster 생성 (Fargate)
aws ecs create-cluster \
  --cluster-name ticketing-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
    capacityProvider=FARGATE_SPOT,weight=4
```

### 4. Task Definition 등록

**API Gateway Task Definition 예시:**

```json
{
  "family": "ticketing-api-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "api-gateway",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/ticketing/api-gateway:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:ticketing/jwt-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ticketing-api-gateway",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

```bash
# Task Definition 등록
aws ecs register-task-definition \
  --cli-input-json file://task-definitions/api-gateway.json
```

### 5. ECS Service 생성

```bash
# API Gateway Service
aws ecs create-service \
  --cluster ticketing-cluster \
  --service-name api-gateway \
  --task-definition ticketing-api-gateway:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-private-1a,subnet-private-1b],
    securityGroups=[sg-ecs],
    assignPublicIp=DISABLED
  }" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api-gateway,containerPort=8000" \
  --health-check-grace-period-seconds 60

# Auto Scaling 설정
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ticketing-cluster/api-gateway \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name api-gateway-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/ticketing-cluster/api-gateway \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

**모든 서비스 반복 (Auth, Events, Booking, Payment, Search, Notification, Inventory)**

---

## 프론트엔드 배포

### 1. S3 Bucket 생성

```bash
# S3 Bucket 생성
aws s3api create-bucket \
  --bucket ticketing-pro-frontend \
  --region us-east-1

# Static Website Hosting 활성화
aws s3 website s3://ticketing-pro-frontend/ \
  --index-document index.html \
  --error-document index.html

# Bucket Policy 설정 (CloudFront만 접근 가능)
aws s3api put-bucket-policy \
  --bucket ticketing-pro-frontend \
  --policy file://s3-bucket-policy.json
```

### 2. CloudFront Distribution 생성

```json
{
  "CallerReference": "ticketing-frontend-2024",
  "Comment": "Ticketing Pro Frontend CDN",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-ticketing-pro-frontend",
        "DomainName": "ticketing-pro-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/XXXXX"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-ticketing-pro-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "CachedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "Compress": true,
    "DefaultTTL": 86400,
    "MinTTL": 0,
    "MaxTTL": 31536000
  },
  "ViewerCertificate": {
    "ACMCertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "Aliases": {
    "Quantity": 1,
    "Items": ["ticketing-pro.com"]
  }
}
```

```bash
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json
```

### 3. 프론트엔드 빌드 및 배포

```bash
cd frontend

# 프로덕션 빌드
npm run build

# S3에 업로드
aws s3 sync dist/ s3://ticketing-pro-frontend/ \
  --delete \
  --cache-control "max-age=31536000, public" \
  --exclude "index.html"

# index.html은 짧은 캐시 타임
aws s3 cp dist/index.html s3://ticketing-pro-frontend/index.html \
  --cache-control "max-age=300, public"

# CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id EXXXXXXXXXXXXX \
  --paths "/*"
```

---

## 모니터링 및 로깅

### 1. CloudWatch Logs

```bash
# Log Groups 생성
for service in api-gateway auth events booking payment search notification inventory; do
  aws logs create-log-group \
    --log-group-name /ecs/ticketing-${service}
done

# Log Retention 설정 (30일)
for service in api-gateway auth events booking payment search notification inventory; do
  aws logs put-retention-policy \
    --log-group-name /ecs/ticketing-${service} \
    --retention-in-days 30
done
```

### 2. CloudWatch Metrics & Alarms

```bash
# CPU 사용률 알람
aws cloudwatch put-metric-alarm \
  --alarm-name ticketing-api-gateway-cpu-high \
  --alarm-description "API Gateway CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=api-gateway Name=ClusterName,Value=ticketing-cluster

# 에러율 알람
aws cloudwatch put-metric-alarm \
  --alarm-name ticketing-api-gateway-errors \
  --alarm-description "API Gateway 5xx errors" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### 3. X-Ray 설정

```bash
# X-Ray Daemon Sidecar 추가 (Task Definition)
{
  "name": "xray-daemon",
  "image": "amazon/aws-xray-daemon",
  "cpu": 32,
  "memoryReservation": 256,
  "portMappings": [
    {
      "containerPort": 2000,
      "protocol": "udp"
    }
  ]
}
```

---

## 보안 설정

### 1. WAF (Web Application Firewall)

```bash
# Web ACL 생성
aws wafv2 create-web-acl \
  --name ticketing-waf \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --rules file://waf-rules.json
```

**WAF Rules:**
- Rate limiting (100 req/5min per IP)
- SQL Injection protection
- XSS protection
- Known bad inputs
- Geo-blocking (선택적)

### 2. Secrets Rotation

```bash
# Secrets Manager에서 자동 rotation 설정
aws secretsmanager rotate-secret \
  --secret-id ticketing/database-password \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerRotation \
  --rotation-rules AutomaticallyAfterDays=30
```

### 3. VPC Flow Logs

```bash
# VPC Flow Logs 활성화
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/ticketing
```

---

## 백업 및 복구

### 1. RDS 자동 백업

```bash
# 자동 백업 활성화 (이미 설정됨)
aws rds modify-db-instance \
  --db-instance-identifier ticketing-postgres \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"

# 수동 스냅샷 생성
aws rds create-db-snapshot \
  --db-instance-identifier ticketing-postgres \
  --db-snapshot-identifier ticketing-postgres-$(date +%Y%m%d)
```

### 2. DynamoDB 백업

```bash
# Point-in-time Recovery 활성화
aws dynamodb update-continuous-backups \
  --table-name ticketing-bookings \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# On-demand 백업
aws dynamodb create-backup \
  --table-name ticketing-bookings \
  --backup-name ticketing-bookings-$(date +%Y%m%d)
```

### 3. S3 Versioning

```bash
# S3 버저닝 활성화
aws s3api put-bucket-versioning \
  --bucket ticketing-pro-frontend \
  --versioning-configuration Status=Enabled
```

---

## 트러블슈팅

### 1. ECS Task 시작 실패

**원인:**
- 이미지 pull 실패
- Insufficient memory/CPU
- Secrets Manager 접근 권한 없음

**해결:**
```bash
# Task 로그 확인
aws ecs describe-tasks \
  --cluster ticketing-cluster \
  --tasks <task-arn>

# CloudWatch Logs 확인
aws logs tail /ecs/ticketing-api-gateway --follow
```

### 2. 데이터베이스 연결 실패

**원인:**
- Security Group 설정 오류
- 잘못된 credentials
- Connection pool exhausted

**해결:**
```bash
# Security Group ingress 확인
aws ec2 describe-security-groups --group-ids sg-xxxxx

# RDS 연결 테스트
psql -h ticketing-postgres.xxxxx.rds.amazonaws.com -U admin -d ticketing_auth
```

### 3. 높은 지연 시간 (High Latency)

**원인:**
- 비효율적인 데이터베이스 쿼리
- Cold start (Lambda/Fargate)
- 캐시 미사용

**해결:**
- RDS Performance Insights 확인
- 슬로우 쿼리 로그 분석
- Redis 캐싱 추가
- CloudFront 캐시 설정 최적화

---

## 배포 체크리스트

### Pre-Deployment

- [ ] 모든 환경 변수 설정 완료
- [ ] Secrets Manager에 민감 정보 저장
- [ ] SSL 인증서 발급 및 적용
- [ ] 데이터베이스 마이그레이션 테스트
- [ ] 로드 테스트 수행 (10,000+ req/s)
- [ ] 보안 취약점 스캔
- [ ] 백업 및 복구 절차 테스트

### Deployment

- [ ] Blue/Green deployment 전략 사용
- [ ] Health check 통과 확인
- [ ] Auto Scaling 동작 확인
- [ ] CloudWatch 알람 설정
- [ ] WAF rules 활성화
- [ ] CDN 캐시 warming

### Post-Deployment

- [ ] 프로덕션 smoke tests
- [ ] 사용자 모니터링 (Real User Monitoring)
- [ ] 에러율 모니터링
- [ ] 성능 메트릭 확인
- [ ] 백업 자동화 검증
- [ ] Incident response plan 준비

---

## 참고 자료

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Stripe Production Checklist](https://stripe.com/docs/security/guide)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

**배포 완료 후 status.ticketing-pro.com에서 시스템 상태를 모니터링하세요!**
