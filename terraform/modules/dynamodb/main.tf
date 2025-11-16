# Seats Table
resource "aws_dynamodb_table" "seats" {
  name           = "${var.project_name}-seats-${var.environment}"
  billing_mode   = var.billing_mode
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
    enabled = var.environment == "prod" ? true : false
  }

  ttl {
    enabled        = false
    attribute_name = ""
  }

  tags = {
    Name        = "${var.project_name}-seats-${var.environment}"
    Environment = var.environment
  }
}

# Reservations Table
resource "aws_dynamodb_table" "reservations" {
  name           = "${var.project_name}-reservations-${var.environment}"
  billing_mode   = var.billing_mode
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

  point_in_time_recovery {
    enabled = var.environment == "prod" ? true : false
  }

  ttl {
    enabled        = true
    attribute_name = "ttl"
  }

  tags = {
    Name        = "${var.project_name}-reservations-${var.environment}"
    Environment = var.environment
  }
}

# Bookings Table
resource "aws_dynamodb_table" "bookings" {
  name           = "${var.project_name}-bookings-${var.environment}"
  billing_mode   = var.billing_mode
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
    enabled = var.environment == "prod" ? true : false
  }

  ttl {
    enabled        = false
    attribute_name = ""
  }

  tags = {
    Name        = "${var.project_name}-bookings-${var.environment}"
    Environment = var.environment
  }
}
