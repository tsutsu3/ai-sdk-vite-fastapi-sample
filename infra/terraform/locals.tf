resource "random_string" "suffix" {
  length  = 6
  lower   = true
  upper   = false
  numeric = true
  special = false
}

locals {
  suffix = var.resource_suffix != "" ? var.resource_suffix : random_string.suffix.result
  base   = lower(replace("${var.name_prefix}-${var.environment}-${local.suffix}", "/[^a-z0-9-]/", ""))

  storage_account_name = substr(
    lower(replace("st${var.name_prefix}${var.environment}${local.suffix}", "/[^a-z0-9]/", "")),
    0,
    24
  )
  cosmos_account_name = substr(
    lower(replace("cos${var.name_prefix}-${var.environment}-${local.suffix}", "/[^a-z0-9-]/", "")),
    0,
    44
  )
  eventhub_namespace_name = substr(
    lower(replace("ehns-${local.base}", "/[^a-z0-9-]/", "")),
    0,
    50
  )
  search_service_name = substr(
    lower(replace("srch-${local.base}", "/[^a-z0-9-]/", "")),
    0,
    60
  )
  openai_name = substr(
    lower(replace("aoai-${local.base}", "/[^a-z0-9-]/", "")),
    0,
    63
  )
  app_service_plan_name = "asp-${local.base}"
  app_service_name      = "app-${local.base}"
  log_analytics_name    = "law-${local.base}"
  app_insights_name     = "appi-${local.base}"
  cosmos_db_name        = var.cosmos_database_name

  common_tags = merge(
    {
      environment = var.environment
      project     = var.project_name
      service     = var.service_name
      owner       = var.owner
      cost_center = var.cost_center
      managed_by  = "terraform"
    },
    var.tags
  )
}
