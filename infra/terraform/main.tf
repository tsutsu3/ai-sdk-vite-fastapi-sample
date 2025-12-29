resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = local.log_analytics_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

resource "azurerm_application_insights" "main" {
  name                = local.app_insights_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.common_tags
}

resource "azurerm_cosmosdb_account" "main" {
  name                = local.cosmos_account_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  consistency_policy {
    consistency_level = "Session"
  }
  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }
  public_network_access_enabled = true
  tags                          = local.common_tags
}

resource "azurerm_cosmosdb_sql_database" "main" {
  name                = local.cosmos_db_name
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = 400
}

resource "azurerm_storage_account" "main" {
  name                     = local.storage_account_name
  location                 = azurerm_resource_group.main.location
  resource_group_name      = azurerm_resource_group.main.name
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"
  allow_blob_public_access = false
  tags                     = local.common_tags
}

resource "azurerm_storage_container" "attachments" {
  name                  = var.storage_container_name
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_eventhub_namespace" "main" {
  name                = local.eventhub_namespace_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.eventhub_sku
  tags                = local.common_tags
}

resource "azurerm_eventhub" "usage" {
  name                = var.eventhub_name
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = azurerm_resource_group.main.name
  partition_count     = 2
  message_retention   = 1
}

resource "azurerm_eventhub_namespace_authorization_rule" "usage_sender" {
  name                = "usage-sender"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = azurerm_resource_group.main.name
  send                = true
  listen              = false
  manage              = false
}

resource "azurerm_search_service" "main" {
  name                = local.search_service_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.search_sku
  replica_count       = 1
  partition_count     = 1
  tags                = local.common_tags
}

resource "azurerm_cognitive_account" "openai" {
  name                = local.openai_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"
  custom_subdomain_name = local.openai_name
  tags                = local.common_tags
}

resource "azurerm_service_plan" "main" {
  name                = local.app_service_plan_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = var.app_service_sku
  tags                = local.common_tags
}

resource "azurerm_linux_web_app" "main" {
  name                = local.app_service_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = merge(
    {
      APP_ENV                            = var.environment
      AZURE_MONITOR_CONNECTION_STRING     = azurerm_application_insights.main.connection_string
      AZURE_OPENAI_ENDPOINT               = azurerm_cognitive_account.openai.endpoint
      RETRIEVAL_AI_SEARCH_URL             = azurerm_search_service.main.query_endpoint
      AZURE_BLOB_ENDPOINT                 = azurerm_storage_account.main.primary_blob_endpoint
      COSMOS_ENDPOINT                     = azurerm_cosmosdb_account.main.endpoint
      USAGE_EVENTHUB_NAMESPACE            = format("%s.servicebus.windows.net", azurerm_eventhub_namespace.main.name)
      USAGE_EVENTHUB_NAME                 = azurerm_eventhub.usage.name
      AUTH_MODE                           = var.auth_mode
    },
    var.auth_mode == "key" ? {
      AZURE_OPENAI_API_KEY       = azurerm_cognitive_account.openai.primary_access_key
      RETRIEVAL_AI_SEARCH_API_KEY = azurerm_search_service.main.primary_key
      RETRIEVAL_AI_SEARCH_AUTH_HEADER = "api-key"
      AZURE_BLOB_API_KEY         = azurerm_storage_account.main.primary_access_key
      COSMOS_KEY                 = azurerm_cosmosdb_account.main.primary_key
      USAGE_EVENTHUB_KEY_NAME    = azurerm_eventhub_namespace_authorization_rule.usage_sender.name
      USAGE_EVENTHUB_API_KEY     = azurerm_eventhub_namespace_authorization_rule.usage_sender.primary_key
    } : {},
    var.app_settings
  )

  dynamic "identity" {
    for_each = var.auth_mode == "managed_identity" ? [1] : []
    content {
      type = "SystemAssigned"
    }
  }

  tags = local.common_tags
}

resource "azurerm_role_assignment" "storage_blob_contributor" {
  count                = var.auth_mode == "managed_identity" ? 1 : 0
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "cosmos_data_contributor" {
  count                = var.auth_mode == "managed_identity" ? 1 : 0
  scope                = azurerm_cosmosdb_account.main.id
  role_definition_name = "Cosmos DB Built-in Data Contributor"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "eventhub_sender" {
  count                = var.auth_mode == "managed_identity" ? 1 : 0
  scope                = azurerm_eventhub_namespace.main.id
  role_definition_name = "Azure Event Hubs Data Sender"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "search_contributor" {
  count                = var.auth_mode == "managed_identity" ? 1 : 0
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "openai_user" {
  count                = var.auth_mode == "managed_identity" ? 1 : 0
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}
