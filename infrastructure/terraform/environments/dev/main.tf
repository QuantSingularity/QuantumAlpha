provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.common_tags
  }
}

module "vpc" {
  source = "../../modules/vpc"

  project_name         = "quantumalpha"
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnets
  private_subnet_cidrs = var.private_subnets
  common_tags          = var.common_tags
}

module "eks" {
  source = "../../modules/eks"

  environment         = var.environment
  cluster_name        = "quantumalpha-${var.environment}"
  cluster_version     = var.eks_cluster_version
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_instance_types = var.eks_node_instance_types
  node_desired_size   = var.eks_node_desired_size
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
}

module "rds" {
  source = "../../modules/rds"

  project_name           = "quantumalpha"
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  instance_class         = var.rds_instance_class
  allocated_storage      = var.rds_allocated_storage
  engine_version         = var.rds_engine_version
  database_name          = "quantumalpha"
  master_username        = var.rds_master_username
  master_password        = var.rds_master_password
  allowed_cidr_blocks    = var.rds_allowed_cidr_blocks
  allowed_security_groups = [module.eks.node_security_group_id]
  common_tags            = var.common_tags
}

module "elasticache" {
  source = "../../modules/elasticache"

  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_type          = var.elasticache_node_type
  engine_version     = var.elasticache_engine_version
  num_cache_nodes    = var.elasticache_num_cache_nodes
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS cluster CA data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
}

output "elasticache_endpoint" {
  description = "ElastiCache primary endpoint"
  value       = module.elasticache.endpoint
}
