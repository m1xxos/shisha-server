resource "random_password" "games_postgres" {
  length  = 24
  special = false
}

resource "portainer_stack" "games" {
  name                      = "games"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/games/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = true

  env {
    name  = "POSTGRES_PASSWORD"
    value = random_password.games_postgres.result
  }

  env {
    name  = "AUTH_SECRET"
    value = var.AUTH_SECRET
  }

  env {
    name  = "AUTH_URL"
    value = "https://games.home.m1xxos.online"
  }
}
