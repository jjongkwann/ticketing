#!/bin/bash

# DynamoDB Local 테이블 초기화 스크립트
# Docker Compose 환경에서 실행

set -e

ENDPOINT="http://localhost:8001"
REGION="us-east-1"

echo "🚀 DynamoDB Local 테이블 생성 중..."

# Bookings 테이블
echo "📦 Bookings 테이블 생성..."
aws dynamodb create-table \
  --table-name bookings \
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
  --endpoint-url $ENDPOINT \
  --region $REGION \
  2>/dev/null || echo "⚠️  Bookings 테이블이 이미 존재합니다."

# Seats 테이블
echo "📦 Seats 테이블 생성..."
aws dynamodb create-table \
  --table-name ticketing-seats \
  --attribute-definitions \
      AttributeName=event_id,AttributeType=S \
      AttributeName=seat_number,AttributeType=S \
      AttributeName=status,AttributeType=S \
  --key-schema \
      AttributeName=event_id,KeyType=HASH \
      AttributeName=seat_number,KeyType=RANGE \
  --global-secondary-indexes \
      '[
        {
          "IndexName": "status-index",
          "KeySchema": [
            {"AttributeName":"event_id","KeyType":"HASH"},
            {"AttributeName":"status","KeyType":"RANGE"}
          ],
          "Projection": {"ProjectionType":"ALL"}
        }
      ]' \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url $ENDPOINT \
  --region $REGION \
  2>/dev/null || echo "⚠️  Seats 테이블이 이미 존재합니다."

# Reservations 테이블
echo "📦 Reservations 테이블 생성..."
aws dynamodb create-table \
  --table-name ticketing-reservations \
  --attribute-definitions \
      AttributeName=reservation_id,AttributeType=S \
      AttributeName=event_id,AttributeType=S \
      AttributeName=user_id,AttributeType=S \
  --key-schema \
      AttributeName=reservation_id,KeyType=HASH \
  --global-secondary-indexes \
      '[
        {
          "IndexName": "event-index",
          "KeySchema": [{"AttributeName":"event_id","KeyType":"HASH"}],
          "Projection": {"ProjectionType":"ALL"}
        },
        {
          "IndexName": "user-index",
          "KeySchema": [{"AttributeName":"user_id","KeyType":"HASH"}],
          "Projection": {"ProjectionType":"ALL"}
        }
      ]' \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url $ENDPOINT \
  --region $REGION \
  2>/dev/null || echo "⚠️  Reservations 테이블이 이미 존재합니다."

# Inventory Bookings 테이블
echo "📦 Inventory Bookings 테이블 생성..."
aws dynamodb create-table \
  --table-name ticketing-bookings \
  --attribute-definitions \
      AttributeName=booking_id,AttributeType=S \
      AttributeName=event_id,AttributeType=S \
      AttributeName=user_id,AttributeType=S \
  --key-schema \
      AttributeName=booking_id,KeyType=HASH \
  --global-secondary-indexes \
      '[
        {
          "IndexName": "event-index",
          "KeySchema": [{"AttributeName":"event_id","KeyType":"HASH"}],
          "Projection": {"ProjectionType":"ALL"}
        },
        {
          "IndexName": "user-index",
          "KeySchema": [{"AttributeName":"user_id","KeyType":"HASH"}],
          "Projection": {"ProjectionType":"ALL"}
        }
      ]' \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url $ENDPOINT \
  --region $REGION \
  2>/dev/null || echo "⚠️  Inventory Bookings 테이블이 이미 존재합니다."

echo ""
echo "✅ DynamoDB 테이블 초기화 완료!"
echo ""
echo "📋 생성된 테이블 목록:"
aws dynamodb list-tables --endpoint-url $ENDPOINT --region $REGION
