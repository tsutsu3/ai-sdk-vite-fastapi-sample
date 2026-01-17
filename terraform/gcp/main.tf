locals {
  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# =============================================================================
# Firestore Database
# =============================================================================
resource "google_firestore_database" "db" {
  name        = "${var.environment}-${var.firestore_database_id}"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}


resource "google_firestore_field" "messages_parts_text" {
  project  = var.project_id
  database = google_firestore_database.db.name

  collection = "messages"
  field      = "parts.text"

  index_config {}
}
