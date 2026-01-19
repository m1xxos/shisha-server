resource "random_password" "enc_key" {
  length = 20
}

resource "random_password" "auth_secret" {
  length = 20
}

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
    name = "ENCRYPTION_KEY"
    value = random_password.enc_key.result
  }
  env {
    name = "AUTH_SECRET"
    value = random_password.auth_secret.result
  }
  env {
    name = "POSTGRES_PASSWORD"
    value = random_password.pg_pass.result
  }

}
