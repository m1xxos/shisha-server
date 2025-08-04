resource "portainer_docker_network" "traefik_proxy" {
  endpoint_id = var.endpoint_id
  name        = "traefik_proxy"
}

resource "portainer_stack" "traefik" {
  name                      = "traefik"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/traefik/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = true

  env {
    name  = "CF_API_EMAIL"
    value = var.CF_API_EMAIL
  }
  env {
    name  = "CF_DNS_API_TOKEN"
    value = var.CF_DNS_API_TOKEN
  }

  depends_on = [portainer_docker_network.traefik_proxy]
}
