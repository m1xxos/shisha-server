resource "portainer_docker_network" "traefik_proxy" {
  endpoint_id = 3
  name        = "traefik_proxy"
}

resource "portainer_stack" "traefik" {
  name            = "traefik"
  method          = "file"
  deployment_type = "standalone"
  endpoint_id     = 3
  stack_file_path = "stacks/traefik.yaml"

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