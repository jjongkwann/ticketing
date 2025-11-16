FROM golang:1.21-alpine AS builder

WORKDIR /app

# 시스템 dependencies
RUN apk add --no-cache git gcc musl-dev protobuf-dev

# Go dependencies
COPY go.mod go.sum ./
RUN go mod download

# Protobuf 생성 (프로덕션에서는 미리 생성된 파일 사용 권장)
# RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
# RUN go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Application code
COPY . .

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
