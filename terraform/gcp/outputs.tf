output "region" {
  value       = var.region
  description = "GCP region"
}

output "project_id" {
  value       = var.project_id
  description = "GCP Project ID"
}

output "firestore_database_id" {
  value       = google_firestore_database.db.id
  description = "Firestore database ID"
}

output "firestore_database_name" {
  value       = google_firestore_database.db.name
  description = "Firestore database name"
}

output "collection_names" {
  value = {
    conversations  = var.conversations_collection
    messages       = var.messages_collection
    users          = var.users_collection
    tenants        = var.tenants_collection
    useridentities = var.useridentities_collection
    provisioning   = var.provisioning_collection
  }
  description = "Firestore collection names"
}
