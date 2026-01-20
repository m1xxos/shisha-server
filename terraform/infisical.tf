resource "random_password" "pg_pass" {
  length = 20
}

resource "portainer_stack" "infisical" {
  name                      = "infisical"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/infisical/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = false
  env {
    name  = "ENCRYPTION_KEY"
    value = var.ENCRYPTION_KEY
  }
  env {
    name  = "AUTH_SECRET"
    value = var.AUTH_SECRET
  }
  env {
    name  = "POSTGRES_PASSWORD"
    value = random_password.pg_pass.result
  }
  env {
    name  = "CLIENT_ID_GITHUB_LOGIN"
    value = var.CLIENT_ID_GITHUB_LOGIN
  }
  env {
    name  = "CLIENT_SECRET_GITHUB_LOGIN"
    value = var.CLIENT_SECRET_GITHUB_LOGIN
  }
}
