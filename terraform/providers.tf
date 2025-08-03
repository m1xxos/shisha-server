terraform {
  required_providers {
    portainer = {
      source = "portainer/portainer"
      version = "1.10.0"
    }
  }
  backend "s3" {
    endpoint                    = "https://storage.yandexcloud.net"
    region                      = "ru-central1"
    bucket                      = var.bucket
    key                         = "shisha-state.tfstate"
    access_key                  = var.access_key
    secret_key                  = var.secret_key
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }
}

provider "portainer" {
  endpoint = "https://192.168.1.128:9443"
  api_key = var.portainer_token
  skip_ssl_verify = true
}