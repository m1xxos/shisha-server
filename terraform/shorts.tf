resource "portainer_stack" "shorts" {
  name                      = "shorts"
  method                    = "repository"
  deployment_type           = "standalone"
  endpoint_id               = var.endpoint_id
  repository_url            = var.repository_url
  repository_reference_name = var.repository_reference_name
  file_path_in_repository   = "stacks/shorts/compose.yaml"
  filesystem_path           = var.filesystem_path
  stack_webhook             = true
  update_interval           = var.update_interval
  pull_image                = true
  force_update              = false

  # The digest writes its card blurbs with a language model. All of this is
  # optional — with LLM_GROQ_KEY empty the digest still builds and falls back
  # to the articles' own opening lines.
  env {
    name  = "LLM_PROVIDERS"
    value = var.LLM_GROQ_KEY == "" ? "" : "groq"
  }

  env {
    name  = "LLM_GROQ_KEY"
    value = var.LLM_GROQ_KEY
  }

  # Groq geo-blocks and answers 403 without this. Only the provider calls are
  # routed through it; feeds and article covers keep going out directly.
  env {
    name  = "LLM_PROXY_URL"
    value = var.PROXY
  }

  # Ranking the shortlist is one large prompt rather than several small ones,
  # and Groq meters tokens per model — so it runs on a second model and gets a
  # budget of its own instead of competing with the annotations.
  env {
    name  = "LLM_RANK_PROVIDERS"
    value = var.LLM_GROQ_KEY == "" ? "" : "groq-small"
  }

  env {
    name  = "LLM_GROQ_SMALL_URL"
    value = "https://api.groq.com/openai/v1"
  }

  env {
    name  = "LLM_GROQ_SMALL_MODEL"
    value = "llama-3.1-8b-instant"
  }

  env {
    name  = "LLM_GROQ_SMALL_KEY"
    value = var.LLM_GROQ_KEY
  }
}
