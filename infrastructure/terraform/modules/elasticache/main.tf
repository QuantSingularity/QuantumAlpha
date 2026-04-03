resource "aws_elasticache_subnet_group" "main" {
  name       = "quantumalpha-${var.environment}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "quantumalpha-${var.environment}-redis-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "redis" {
  name        = "quantumalpha-${var.environment}-redis-sg"
  description = "Security group for ElastiCache Redis cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "Allow Redis traffic from within VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "quantumalpha-${var.environment}-redis-sg"
    Environment = var.environment
  }
}

resource "aws_elasticache_parameter_group" "redis" {
  name   = "quantumalpha-${var.environment}-redis-params"
  family = "redis${split(".", var.engine_version)[0]}.x"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  tags = {
    Name        = "quantumalpha-${var.environment}-redis-params"
    Environment = var.environment
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "quantumalpha-${var.environment}-redis"
  description                = "QuantumAlpha ${var.environment} Redis cluster"
  node_type                  = var.node_type
  num_cache_clusters         = var.num_cache_nodes
  parameter_group_name       = aws_elasticache_parameter_group.redis.name
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  engine_version             = var.engine_version
  port                       = 6379
  automatic_failover_enabled = var.num_cache_nodes > 1
  multi_az_enabled           = var.num_cache_nodes > 1
  auto_minor_version_upgrade = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name        = "quantumalpha-${var.environment}-redis"
    Environment = var.environment
  }
}
