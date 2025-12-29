variable "location" {
  description = "Azure region (e.g. japaneast)."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name."
  type        = string
}

variable "environment" {
  description = "Environment name (e.g. local, dev, prod)."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names."
  type        = string
  default     = "ai"
}

variable "project_name" {
  description = "Project name for tagging."
  type        = string
  default     = "ai-sdk-vite-fastapi-sample"
}

variable "service_name" {
  description = "Service name for tagging."
  type        = string
  default     = "ai-sdk-vite-fastapi-sample"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = ""
}

variable "cost_center" {
  description = "Cost center tag value."
  type        = string
  default     = ""
}

variable "resource_suffix" {
  description = "Optional suffix to ensure globally unique resource names."
  type        = string
  default     = ""
}

variable "auth_mode" {
  description = "Authentication mode: key or managed_identity."
  type        = string
  default     = "key"
  validation {
    condition     = contains(["key", "managed_identity"], var.auth_mode)
    error_message = "auth_mode must be 'key' or 'managed_identity'."
  }
}

variable "tags" {
  description = "Additional tags to merge with common tags."
  type        = map(string)
  default     = {}
}

variable "cosmos_database_name" {
  description = "Cosmos DB SQL database name."
  type        = string
  default     = "chatdb"
}

variable "eventhub_name" {
  description = "Event Hub name for usage buffer."
  type        = string
  default     = "usage"
}

variable "eventhub_sku" {
  description = "Event Hub namespace SKU (Basic or Standard)."
  type        = string
  default     = "Basic"
}

variable "storage_container_name" {
  description = "Blob storage container name."
  type        = string
  default     = "attachments"
}

variable "search_sku" {
  description = "Azure AI Search SKU (basic or standard)."
  type        = string
  default     = "basic"
}

variable "app_service_sku" {
  description = "App Service plan SKU (e.g. B1, S1)."
  type        = string
  default     = "B1"
}

variable "app_settings" {
  description = "Additional App Service app settings."
  type        = map(string)
  default     = {}
}
