variable "portainer_token" {
  type      = string
  sensitive = true
}

variable "endpoint_id" {
  type = number
  default = 3
}

variable "repository_url" {
  type = string
  default = "https://github.com/m1xxos/shisha-server"
}

variable "repository_reference_name" {
  type = string
  default = "refs/heads/main"
}