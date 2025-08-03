resource "portainer_docker_network" "traefik_proxy" {
  endpoint_id = var.endpoint_id
  name        = "traefik_proxy"
}

resource "portainer_stack" "traefik" {
  name            = "traefik"
  method          = "repository"
  deployment_type = "standalone"
  endpoint_id     = var.endpoint_id
  repository_url = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository = "stacks/traefik/compose.yaml"

  env {
    name  = "CF_API_EMAIL"
    value = "bulynin.misha@gmail.com"
  }

  env {
    name  = "ENV_VAR_2"
    value = "value2"
  }

  depends_on = [portainer_docker_network.traefik_proxy]
}