resource "random_password" "kaneo_postgres" {
  length  = 24
  special = false
}

resource "random_password" "kaneo_auth_secret" {
  length  = 64
  special = false
}

resource "portainer_stack" "kaneo" {
  name                      = "kaneo"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/kaneo/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = false

  env {
    name  = "POSTGRES_PASSWORD"
    value = random_password.kaneo_postgres.result
  }

  env {
    name  = "AUTH_SECRET_KANEO"
    value = random_password.kaneo_auth_secret.result
  }
}
