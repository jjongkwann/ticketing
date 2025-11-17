FROM golang:1.23-alpine AS builder

WORKDIR /app

# 시스템 dependencies
RUN apk add --no-cache git gcc musl-dev protobuf-dev

# Protobuf 플러그인 설치
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.34.0
RUN go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.4.0

# Go dependencies 초기 복사
COPY go.mod ./
COPY go.sum* ./

# Proto 파일 복사 및 생성
COPY proto/ ./proto/
RUN protoc --go_out=. --go-grpc_out=. proto/inventory.proto

# 모든 소스 복사
COPY . .

# Go 모듈 다운로드 (proto 파일 생성 후)
RUN go mod download

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o inventory-server ./cmd/server

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/inventory-server .

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 50051 8080

# Non-root user
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
USER appuser

CMD ["./inventory-server"]
