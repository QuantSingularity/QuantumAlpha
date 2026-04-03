variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
}

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS worker nodes"
  type        = list(string)
  default     = ["t3.large"]
}

variable "eks_node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}

variable "eks_node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "eks_node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 4
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Allocated storage for RDS instance in GB"
  type        = number
  default     = 20
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15"
}

variable "rds_master_username" {
  description = "Master username for RDS instance"
  type        = string
  default     = "postgres"
}

variable "rds_master_password" {
  description = "Master password for RDS instance. Must be set via TF_VAR_rds_master_password env var or tfvars file - never hardcoded."
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.rds_master_password) >= 16
    error_message = "RDS master password must be at least 16 characters long."
  }
}

variable "rds_allowed_cidr_blocks" {
  description = "CIDR blocks allowed to connect to RDS"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.small"
}

variable "elasticache_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "msk_kafka_version" {
  description = "Kafka version for MSK cluster"
  type        = string
  default     = "3.5.1"
}

variable "msk_broker_instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
  default     = "kafka.t3.small"
}

variable "msk_broker_count" {
  description = "Number of broker nodes"
  type        = number
  default     = 3
}

variable "msk_ebs_volume_size" {
  description = "EBS volume size for MSK brokers in GB"
  type        = number
  default     = 100
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "quantumalpha"
    ManagedBy   = "terraform"
    Compliance  = "SOX,PCI-DSS,GLBA"
  }
}
