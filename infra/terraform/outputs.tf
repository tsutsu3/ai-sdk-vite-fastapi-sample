output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "location" {
  value = azurerm_resource_group.main.location
}

output "cosmos_endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "cosmos_key" {
  value     = azurerm_cosmosdb_account.main.primary_key
  sensitive = true
}

output "cosmos_database" {
  value = azurerm_cosmosdb_sql_database.main.name
}

output "blob_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}

output "blob_key" {
  value     = azurerm_storage_account.main.primary_access_key
  sensitive = true
}

output "blob_container" {
  value = azurerm_storage_container.attachments.name
}

output "eventhub_namespace" {
  value = format("%s.servicebus.windows.net", azurerm_eventhub_namespace.main.name)
}

output "eventhub_name" {
  value = azurerm_eventhub.usage.name
}

output "eventhub_key_name" {
  value = azurerm_eventhub_namespace_authorization_rule.usage_sender.name
}

output "eventhub_key" {
  value     = azurerm_eventhub_namespace_authorization_rule.usage_sender.primary_key
  sensitive = true
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "openai_key" {
  value     = azurerm_cognitive_account.openai.primary_access_key
  sensitive = true
}

output "search_endpoint" {
  value = azurerm_search_service.main.query_endpoint
}

output "search_key" {
  value     = azurerm_search_service.main.primary_key
  sensitive = true
}

output "app_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}

output "app_service_url" {
  value = "https://${azurerm_linux_web_app.main.default_hostname}"
}
