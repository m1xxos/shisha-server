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

  # Groq withdrew the Llama models in August 2026; this is the small
  # gpt-oss, which is what the app's own preset now points at.
  env {
    name  = "LLM_GROQ_SMALL_MODEL"
    value = "openai/gpt-oss-20b"
  }

  env {
    name  = "LLM_GROQ_SMALL_KEY"
    value = var.LLM_GROQ_KEY
  }

  # A container's clock is UTC, and the digest's schedule is read in this zone
  # — without it an 08:00 daily digest is built at 11:00 Moscow time, which is
  # the wrong end of the morning to be handed the morning's reading. The times
  # themselves stay on the app's defaults (08:00 daily, Sun 19:00 weekly), and
  # the Settings dialog still wins over all three.
  #
  # Kept last on purpose: the provider keys env blocks by position, so a new
  # one inserted higher up renames every block below it in the plan.
  env {
    name  = "DIGEST_TZ"
    value = "Europe/Moscow"
  }

  # Eleven feeds fail on every refresh from this host — Harper's, the
  # Cloudflare blog, half the Substacks — not with a 403 but with a connection
  # that never completes. The app has always fallen back to a proxy for those;
  # it had nothing to fall back to, because only the LLM's proxy was ever set.
  # A feed that answers directly never touches it. Appended rather than
  # inserted, for the same positional reason as the block above.
  env {
    name  = "FEED_PROXY_URL"
    value = var.PROXY
  }
}
