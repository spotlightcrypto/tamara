"""Application configuration.

All configuration and secrets live here, read from environment variables (and a
local `.env` file in development). Nothing secret is ever hard-coded in source.

We define ONE typed `Settings` class. Pydantic reads the environment, validates
types, applies defaults, and — for anything required — fails loudly at startup
instead of deep inside a request later.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # `model_config` tells pydantic-settings how to find values:
    #   - env_file=".env": also read a local .env file (handy in development)
    #   - extra="ignore": don't error on unrelated env vars (PATH, HOME, ...)
    # Field names map to env vars case-insensitively, so `app_env` <- APP_ENV.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "dev" or "prod". Has a default, so the app boots even with no .env yet.
    app_env: str = "dev"

    # Supabase connection details. We'll fill these in once we create the
    # Supabase project (build step 0.2). Empty defaults for now so importing
    # this module doesn't fail before that exists; we'll tighten these to be
    # required (no default) once they're real, to fail fast if misconfigured.
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # LLM via OpenRouter (OpenAI-compatible gateway to many models). One key;
    # models are config-driven so we can swap them without touching code.
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # The heavyweight model for synthesis (writing the narrative).
    llm_model: str = "z-ai/glm-5.2"
    # A fast model for the latency-sensitive `fast` role (question generation).
    # glm-5.2 took 20-50s here; Haiku 4.5 is ~8s and asks sharper questions.
    llm_model_fast: str = "anthropic/claude-haiku-4.5"


# A single shared instance, imported wherever config is needed:
#   from app.config import settings
settings = Settings()
