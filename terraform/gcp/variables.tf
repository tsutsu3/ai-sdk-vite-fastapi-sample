variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ai-chat"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "firestore_database_id" {
  description = "Firestore database ID"
  type        = string
  default     = "(default)"
}

variable "conversations_collection" {
  description = "Conversations collection name"
  type        = string
  default     = "conversations"
}

variable "messages_collection" {
  description = "Messages collection name"
  type        = string
  default     = "messages"
}

variable "users_collection" {
  description = "Users collection name"
  type        = string
  default     = "users"
}

variable "tenants_collection" {
  description = "Tenants collection name"
  type        = string
  default     = "tenants"
}

variable "useridentities_collection" {
  description = "User identities collection name"
  type        = string
  default     = "useridentities"
}

variable "provisioning_collection" {
  description = "Provisioning collection name"
  type        = string
  default     = "provisioning"
}
