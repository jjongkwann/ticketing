resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-${var.environment}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-${var.environment}"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}"

  engine            = "mysql"
  engine_version    = "8.0.35"
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage

  db_name  = "ticketing_main"
  username = "admin"
  password = random_password.db_password.result

  multi_az               = var.multi_az
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.environment == "prod" ? 7 : 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  performance_insights_enabled    = var.environment == "prod" ? true : false

  skip_final_snapshot = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-${var.environment}-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  tags = {
    Name        = "${var.project_name}-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.project_name}-${var.environment}-db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
  })
}
