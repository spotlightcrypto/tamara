"""Provider-agnostic LLM gateway (via OpenRouter).

Services call `complete()` / `structured()` and never touch a vendor SDK or a
hard-coded model id. We route through OpenRouter (one key, many models); the
model per logical *role* is config-driven, so swapping models — or tiering
roles to different models later — is a settings change, not a code change.

`structured()` is model-agnostic: it asks for JSON, validates it against a
Pydantic schema, and re-prompts on failure. That works across any OpenRouter
model regardless of native structured-output support.
"""

from __future__ import annotations

import json
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import settings

# One OpenAI-compatible client pointed at OpenRouter.
_client = OpenAI(
    base_url=settings.openrouter_base_url,
    api_key=settings.openrouter_api_key,
    default_headers={"X-Title": "Tamara"},
)

# Logical role -> model. `synthesis` uses the heavyweight model for writing
# quality; `fast` uses a snappy model for latency-sensitive question generation.
_MODELS: dict[str, str] = {
    "synthesis": settings.llm_model,
    "fast": settings.llm_model_fast,
}

T = TypeVar("T", bound=BaseModel)


def complete(messages: list[dict[str, Any]], *, role: str = "fast", temperature: float = 0.4) -> str:
    """Return the model's text reply for a chat-style message list."""
    response = _client.chat.completions.create(
        model=_MODELS.get(role, settings.llm_model),
        messages=messages,  # type: ignore[arg-type]
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def structured(
    messages: list[dict[str, Any]],
    schema: type[T],
    *,
    role: str = "fast",
    retries: int = 2,
    temperature: float = 0.2,
) -> T:
    """Return a validated instance of `schema`, re-prompting until the model
    returns JSON that conforms (or raising after `retries`).

    `temperature` defaults low for stable, schema-faithful output; callers that
    want variety (e.g. synthesis) can raise it."""
    instruction = {
        "role": "system",
        "content": (
            "You output ONLY a single valid JSON object — no prose, no markdown, "
            "no code fences — conforming to this JSON Schema:\n"
            + json.dumps(schema.model_json_schema())
        ),
    }
    convo: list[dict[str, Any]] = [instruction, *messages]

    last_error = ""
    for _ in range(retries + 1):
        raw = complete(convo, role=role, temperature=temperature)
        candidate = _extract_json(raw)
        try:
            return schema.model_validate_json(candidate)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            convo.append({"role": "assistant", "content": raw})
            convo.append({
                "role": "user",
                "content": f"That was not valid. Error:\n{last_error}\nReturn ONLY the corrected JSON object.",
            })
    raise RuntimeError(f"LLM did not return valid JSON for {schema.__name__}: {last_error}")


def _extract_json(text: str) -> str:
    """Best-effort: strip code fences and isolate the outermost {...} object."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    start, end = t.find("{"), t.rfind("}")
    return t[start : end + 1] if start != -1 and end != -1 else t
