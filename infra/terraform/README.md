# Terraform (Azure)

This module provisions the Azure resources needed by the app:

- Cosmos DB (SQL API)
- Blob Storage
- Event Hub (usage buffer)
- Azure OpenAI
- Azure AI Search
- Azure Monitor (Log Analytics + App Insights)
- App Service (Linux)

## Quick start

```bash
cd infra/terraform
terraform init
terraform plan -var-file=env/local.key.tfvars
terraform apply -var-file=env/local.key.tfvars
```

## Environment switching

Switch environments by choosing a different tfvars file:

```bash
terraform plan -var-file=env/local.key.tfvars
terraform plan -var-file=env/local.mi.tfvars
```

You can also override any variable via `TF_VAR_` environment variables.

## Auth mode

- `auth_mode = "key"` provisions resources and injects keys into App Service settings.
- `auth_mode = "managed_identity"` enables a system-assigned identity on App Service and assigns RBAC roles.

Note: The current application configuration expects key-based auth for Azure services.
If you plan to use managed identity, update the app to support it.

## Outputs

Use `terraform output` to fetch endpoints and keys for local `.env` files.
Key outputs are marked as sensitive.
