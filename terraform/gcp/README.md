# GCP Terraform Configuration

This directory contains Terraform configuration for provisioning GCP resources.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- Google Cloud SDK with authentication configured
- GCP project with billing enabled

## Resources Created

- **Firestore Database**: Native mode Firestore for collections
  - Collections are created by the application on first use:
    - `conversations`: Conversation records
    - `messages`: Message records
    - `users`: User records
    - `tenants`: Tenant records
    - `useridentities`: User identity records
    - `provisioning`: User provisioning records
- **GCS Buckets**: Cloud Storage buckets
  - Attachments bucket: File uploads
  - Usage logs bucket: Application usage logs

## Usage

### 1. Initialize Terraform

```bash
cd terraform/gcp
terraform init
```

### 2. Configure Variables

Create a `terraform.tfvars` file:

```hcl
project_id   = "your-gcp-project-id"
project_name = "ai-chat"
environment  = "dev"
region       = "asia-northeast1"
```

### 3. Plan and Apply

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

### 4. Get Outputs

```bash
# View all outputs
terraform output

# View specific output
terraform output gcs_attachments_bucket
```

## Configuration in Application

After applying Terraform, update your backend `.env` file:

```bash
# From Terraform outputs
GCP_PROJECT_ID=$(terraform output -raw project_id)
GCP_LOCATION=$(terraform output -raw region)
GCS_BUCKET=$(terraform output -raw gcs_attachments_bucket)
USAGE_BUFFER_GCS_BUCKET=$(terraform output -raw gcs_usage_logs_bucket)

DB_BACKEND=gcp
BLOB_BACKEND=gcp
```

## Firestore Collections

Firestore collections are automatically created by the application when first accessed. No pre-creation is required in Terraform.

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all data in Firestore and GCS buckets.

## Notes

- Firestore Native mode is used (not Datastore mode)
- GCS buckets have uniform bucket-level access enabled
- All resources are labeled with project, environment, and managed_by tags
