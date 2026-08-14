variable "portainer_token" {
  type      = string
  sensitive = true
}

variable "endpoint_id" {
  type    = number
  default = 3
}

variable "repository_url" {
  type    = string
  default = "https://github.com/m1xxos/shisha-server"
}

variable "repository_reference_name" {
  type    = string
  default = "refs/heads/main"
}

variable "filesystem_path" {
  type    = string
  default = "/mnt"
}

variable "update_interval" {
  type    = string
  default = "5m"
}

variable "CF_DNS_API_TOKEN" {
  type      = string
  sensitive = true
}

variable "CF_API_EMAIL" {
  type      = string
  sensitive = true
}

variable "PROXY" {
  type      = string
  sensitive = true
}

variable "ENCRYPTION_KEY" {
  type      = string
  sensitive = true
}

variable "AUTH_SECRET" {
  type      = string
  sensitive = true
}

variable "CLIENT_ID_GITHUB_LOGIN" {
  type      = string
  sensitive = true
}

variable "CLIENT_SECRET_GITHUB_LOGIN" {
  type      = string
  sensitive = true
}

variable "EXPLO_PASS" {
  type      = string
  sensitive = true
}

variable "GITHUB_APP_ID_KANEO" {
  type      = string
  sensitive = true
  default   = ""
}

variable "GITHUB_APP_NAME_KANEO" {
  type    = string
  default = ""
}

variable "GITHUB_PRIVATE_KEY_BASE64_KANEO" {
  type      = string
  sensitive = true
  default   = ""
}

# Groq API key for the magShorts digest annotations. Empty is fine: the digest
# still builds, with extractive summaries instead of written ones.
variable "LLM_GROQ_KEY" {
  type      = string
  sensitive = true
  default   = ""
}
