package repository

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/ticketing/inventory/internal/config"
)

var (
	ErrLockAlreadyHeld = errors.New("lock already held by another client")
	ErrLockNotHeld     = errors.New("lock not held")
)

type RedisRepository struct {
	client *redis.Client
	cfg    *config.Config
}

func NewRedisRepository(client *redis.Client, cfg *config.Config) *RedisRepository {
	return &RedisRepository{
		client: client,
		cfg:    cfg,
	}
}

// AcquireLock attempts to acquire a distributed lock for a seat
// Returns lock token if successful
func (r *RedisRepository) AcquireLock(ctx context.Context, eventID, seatNumber string) (string, error) {
	lockKey := r.getLockKey(eventID, seatNumber)
	lockToken := uuid.New().String()
	ttl := time.Duration(r.cfg.RedisLockTTL) * time.Second

	// SET key value NX EX ttl
	success, err := r.client.SetNX(ctx, lockKey, lockToken, ttl).Result()
	if err != nil {
		return "", fmt.Errorf("failed to acquire lock: %w", err)
	}

	if !success {
		return "", ErrLockAlreadyHeld
	}

	return lockToken, nil
}

// ReleaseLock releases a distributed lock
func (r *RedisRepository) ReleaseLock(ctx context.Context, eventID, seatNumber, lockToken string) error {
	lockKey := r.getLockKey(eventID, seatNumber)

	// Lua script for atomic get-and-delete
	script := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`

	result, err := r.client.Eval(ctx, script, []string{lockKey}, lockToken).Result()
	if err != nil {
		return fmt.Errorf("failed to release lock: %w", err)
	}

	if result.(int64) == 0 {
		return ErrLockNotHeld
	}

	return nil
}

// ExtendLock extends the TTL of an existing lock
func (r *RedisRepository) ExtendLock(ctx context.Context, eventID, seatNumber, lockToken string) error {
	lockKey := r.getLockKey(eventID, seatNumber)
	ttl := time.Duration(r.cfg.RedisLockTTL) * time.Second

	// Lua script for atomic check-and-extend
	script := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("EXPIRE", KEYS[1], ARGV[2])
		else
			return 0
		end
	`

	result, err := r.client.Eval(ctx, script, []string{lockKey}, lockToken, int(ttl.Seconds())).Result()
	if err != nil {
		return fmt.Errorf("failed to extend lock: %w", err)
	}

	if result.(int64) == 0 {
		return ErrLockNotHeld
	}

	return nil
}

// CheckLock checks if a lock exists and is held by the given token
func (r *RedisRepository) CheckLock(ctx context.Context, eventID, seatNumber, lockToken string) (bool, error) {
	lockKey := r.getLockKey(eventID, seatNumber)

	value, err := r.client.Get(ctx, lockKey).Result()
	if err != nil {
		if errors.Is(err, redis.Nil) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check lock: %w", err)
	}

	return value == lockToken, nil
}

func (r *RedisRepository) getLockKey(eventID, seatNumber string) string {
	return fmt.Sprintf("lock:seat:%s:%s", eventID, seatNumber)
}
