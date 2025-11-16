output "endpoint" {
  value = aws_opensearch_domain.main.endpoint
}

output "kibana_endpoint" {
  value = aws_opensearch_domain.main.dashboard_endpoint
}

output "domain_id" {
  value = aws_opensearch_domain.main.domain_id
}

output "arn" {
  value = aws_opensearch_domain.main.arn
}

output "secret_arn" {
  value = aws_secretsmanager_secret.opensearch_password.arn
}
