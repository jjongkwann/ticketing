output "seats_table_name" {
  description = "Seats table name"
  value       = aws_dynamodb_table.seats.name
}

output "seats_table_arn" {
  description = "Seats table ARN"
  value       = aws_dynamodb_table.seats.arn
}

output "seats_stream_arn" {
  description = "Seats table stream ARN"
  value       = aws_dynamodb_table.seats.stream_arn
}

output "reservations_table_name" {
  description = "Reservations table name"
  value       = aws_dynamodb_table.reservations.name
}

output "reservations_table_arn" {
  description = "Reservations table ARN"
  value       = aws_dynamodb_table.reservations.arn
}

output "reservations_stream_arn" {
  description = "Reservations table stream ARN"
  value       = aws_dynamodb_table.reservations.stream_arn
}

output "bookings_table_name" {
  description = "Bookings table name"
  value       = aws_dynamodb_table.bookings.name
}

output "bookings_table_arn" {
  description = "Bookings table ARN"
  value       = aws_dynamodb_table.bookings.arn
}

output "bookings_stream_arn" {
  description = "Bookings table stream ARN"
  value       = aws_dynamodb_table.bookings.stream_arn
}
