resource "random_password" "searxng_secret" {
  length  = 32
  special = false
}

resource "portainer_stack" "searxng" {
  name                      = "searxng"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/searxng/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = false

  env {
    name  = "SEARXNG_SECRET"
    value = random_password.searxng_secret.result
  }

  env {
    name  = "SEARXNG_BASE_URL"
    value = "https://search.home.m1xxos.online/"
  }
}
