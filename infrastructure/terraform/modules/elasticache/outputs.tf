output "endpoint" {
  description = "Primary endpoint of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "reader_endpoint" {
  description = "Reader endpoint of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
}

output "port" {
  description = "Port number for ElastiCache Redis"
  value       = aws_elasticache_replication_group.redis.port
}

output "security_group_id" {
  description = "Security group ID for ElastiCache Redis"
  value       = aws_security_group.redis.id
}
