# Variables for enhanced RDS module with financial-grade security

variable "project_name" {
  description = "Name of the project"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the database"
  type        = list(string)
  default     = []
}

variable "allowed_security_groups" {
  description = "List of security group IDs allowed to access the database"
  type        = list(string)
  default     = []
}

# Database Configuration
variable "engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"
  validation {
    condition     = contains(["postgres", "mysql", "mariadb"], var.engine)
    error_message = "Engine must be one of: postgres, mysql, mariadb."
  }
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "14.9"
}

variable "major_engine_version" {
  description = "Major version of the database engine"
  type        = string
  default     = "14"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
  validation {
    condition     = can(regex("^db\\.", var.instance_class))
    error_message = "Instance class must start with 'db.'."
  }
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100
  validation {
    condition     = var.allocated_storage >= 20
    error_message = "Allocated storage must be at least 20 GB."
  }
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 1000
  # Must be >= allocated_storage; that cross-variable check lives in a precondition on
  # aws_db_instance.main because variable validation may only reference its own variable
  # before Terraform 1.9.
}

variable "storage_type" {
  description = "Storage type"
  type        = string
  default     = "gp3"
  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2"], var.storage_type)
    error_message = "Storage type must be one of: gp2, gp3, io1, io2."
  }
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "quantumalpha"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.database_name))
    error_message = "Database name must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "postgres"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.master_username))
    error_message = "Master username must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "master_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.master_password) >= 12
    error_message = "Master password must be at least 12 characters long for security compliance."
  }
}

variable "database_port" {
  description = "Port for the database"
  type        = number
  default     = 5432
  validation {
    condition     = var.database_port > 0 && var.database_port <= 65535
    error_message = "Database port must be between 1 and 65535."
  }
}

# Backup Configuration
variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
  validation {
    condition     = var.backup_retention_period >= 7 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 7 and 35 days."
  }
}

variable "backup_window" {
  description = "Backup window"
  type        = string
  default     = "03:00-04:00"
  validation {
    condition     = can(regex("^[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$", var.backup_window))
    error_message = "Backup window must be in format HH:MM-HH:MM."
  }
}

variable "maintenance_window" {
  description = "Maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
  validation {
    condition     = can(regex("^(mon|tue|wed|thu|fri|sat|sun):[0-9]{2}:[0-9]{2}-(mon|tue|wed|thu|fri|sat|sun):[0-9]{2}:[0-9]{2}$", var.maintenance_window))
    error_message = "Maintenance window must be in format ddd:HH:MM-ddd:HH:MM."
  }
}

variable "auto_minor_version_upgrade" {
  description = "Enable auto minor version upgrade"
  type        = bool
  default     = true
}

# Security Configuration
variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = true
}

variable "storage_encrypted" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "kms_key_deletion_window" {
  description = "Number of days before KMS key deletion"
  type        = number
  default     = 7
  validation {
    condition     = var.kms_key_deletion_window >= 7 && var.kms_key_deletion_window <= 30
    error_message = "KMS key deletion window must be between 7 and 30 days."
  }
}

variable "enable_key_rotation" {
  description = "Enable automatic KMS key rotation"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 60
  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.monitoring_interval)
    error_message = "Monitoring interval must be one of: 0, 1, 5, 10, 15, 30, 60."
  }
}

variable "enabled_cloudwatch_logs_exports" {
  description = "List of log types to export to CloudWatch"
  type        = list(string)
  default     = ["postgresql"]
  validation {
    condition     = alltrue([for log in var.enabled_cloudwatch_logs_exports : contains(["postgresql", "upgrade"], log)])
    error_message = "Enabled CloudWatch logs exports must be from: postgresql, upgrade."
  }
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 2555 # 7 years for SOX compliance
  validation {
    condition     = var.log_retention_days >= 365
    error_message = "Log retention must be at least 365 days for compliance."
  }
}

variable "performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 731 # 2 years
  validation {
    condition     = contains([7, 731], var.performance_insights_retention_period)
    error_message = "Performance Insights retention period must be 7 or 731 days."
  }
}

# Parameter Group Configuration
variable "db_parameter_group_family" {
  description = "DB parameter group family"
  type        = string
  default     = "postgres14"
}

variable "custom_parameters" {
  description = "Custom database parameters"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

# Read Replica Configuration
variable "create_read_replica" {
  description = "Create a read replica"
  type        = bool
  default     = false
}

variable "replica_instance_class" {
  description = "Instance class for read replica"
  type        = string
  default     = "db.t3.medium"
}

# Compliance Configuration
variable "create_compliance_snapshot" {
  description = "Create compliance snapshot"
  type        = bool
  default     = true
}

variable "secrets_recovery_window" {
  description = "Recovery window for secrets in days"
  type        = number
  default     = 7
  validation {
    condition     = var.secrets_recovery_window >= 7 && var.secrets_recovery_window <= 30
    error_message = "Secrets recovery window must be between 7 and 30 days."
  }
}

# Alerting Configuration
variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs to notify when alarm clears"
  type        = list(string)
  default     = []
}

# Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Terraform  = "true"
    Project    = "quantumalpha"
    Owner      = "platform-team"
    CostCenter = "engineering"
    Compliance = "sox,pci-dss,glba"
  }
}

variable "security_tags" {
  description = "Security-specific tags for compliance"
  type        = map(string)
  default = {
    "compliance.sox"      = "true"
    "compliance.pci-dss"  = "true"
    "compliance.glba"     = "true"
    "security.level"      = "high"
    "backup.required"     = "true"
    "monitoring.required" = "true"
    "encryption.required" = "true"
    "audit.required"      = "true"
  }
}

# Network Configuration
variable "publicly_accessible" {
  description = "Make the database publicly accessible"
  type        = bool
  default     = false
}

variable "ca_cert_identifier" {
  description = "Certificate authority certificate identifier"
  type        = string
  default     = "rds-ca-2019"
}

# Advanced Configuration
variable "apply_immediately" {
  description = "Apply changes immediately"
  type        = bool
  default     = false
}

variable "allow_major_version_upgrade" {
  description = "Allow major version upgrades"
  type        = bool
  default     = false
}

variable "copy_tags_to_snapshot" {
  description = "Copy tags to snapshots"
  type        = bool
  default     = true
}

variable "delete_automated_backups" {
  description = "Delete automated backups when instance is deleted"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when deleting"
  type        = bool
  default     = false
}

variable "final_snapshot_identifier_prefix" {
  description = "Prefix for final snapshot identifier"
  type        = string
  default     = "final-snapshot"
}

# Storage Configuration
variable "iops" {
  description = "IOPS for io1/io2 storage types"
  type        = number
  default     = null
}

variable "storage_throughput" {
  description = "Storage throughput for gp3"
  type        = number
  default     = null
}

# Option Group Configuration
variable "option_group_description" {
  description = "Description for the option group"
  type        = string
  default     = "Option group for RDS instance"
}

variable "options" {
  description = "List of options to apply"
  type = list(object({
    option_name = string
    option_settings = list(object({
      name  = string
      value = string
    }))
  }))
  default = []
}

# Timezone Configuration
variable "timezone" {
  description = "Timezone for the database"
  type        = string
  default     = "UTC"
}

# Character Set Configuration
variable "character_set_name" {
  description = "Character set name for Oracle databases"
  type        = string
  default     = null
}

# License Model
variable "license_model" {
  description = "License model for commercial databases"
  type        = string
  default     = null
}
