resource "random_password" "datacore_admin_token" {
  length  = 32
  special = false
}

resource "portainer_stack" "datacore" {
  name                      = "datacore"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/datacore/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = false

  env {
    name  = "ADMIN_TOKEN"
    value = random_password.datacore_admin_token.result
  }
}

output "datacore_admin_token" {
  description = "Admin token for DataCore control panel"
  value       = random_password.datacore_admin_token.result
  sensitive   = true
}
