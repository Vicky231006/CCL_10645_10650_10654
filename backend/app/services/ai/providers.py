"""Provider-agnostic LLM abstraction.

Supported providers: ollama (default, local), openai-compatible, none.
The product is never bound to a single vendor; if no provider is reachable the
caller must fall back to deterministic behaviour.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings
from app.core.errors import AiUnavailableError
from app.core.logging import get_logger

logger = get_logger("resumo.ai")


class LLMProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def generate(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        ...

    def health(self) -> bool:
        try:
            self.generate("ping", system="Reply with the single word: pong", json_mode=False)
            return True
        except Exception:  # noqa: BLE001
            return False


class NullProvider(LLMProvider):
    name = "none"

    def generate(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        raise AiUnavailableError(
            "No AI provider is configured. Deterministic analysis is available; "
            "set LLM_PROVIDER and start Ollama (or configure an API key) to enable AI features."
        )


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.llm_timeout_seconds

    def generate(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict = {"model": self.model, "messages": messages, "stream": False}
        if json_mode:
            payload["format"] = "json"
            payload["options"] = {"temperature": 0.2}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
            return (data.get("message") or {}).get("content", "")
        except httpx.HTTPError as exc:
            logger.warning("ollama request failed", extra={"extra_fields": {"error": str(exc)}})
            raise AiUnavailableError(
                f"Local AI provider (Ollama at {self.base_url}) is not reachable. "
                "Ensure Ollama is running and the configured model is pulled."
            ) from exc


class OpenAICompatibleProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.openai_model
        self.api_key = settings.openai_api_key
        self.timeout = settings.llm_timeout_seconds

    def generate(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        if not self.api_key:
            raise AiUnavailableError("OPENAI_API_KEY is not configured.")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            logger.warning("openai request failed", extra={"extra_fields": {"error": str(exc)}})
            raise AiUnavailableError("The configured AI provider request failed.") from exc


class BedrockProvider(LLMProvider):
    name = "bedrock"

    def __init__(self) -> None:
        self.region = settings.bedrock_region
        self.model_id = settings.bedrock_model_id
        self.timeout = settings.llm_timeout_seconds

    def generate(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        try:
            import boto3
        except ImportError as exc:
            raise AiUnavailableError("boto3 is required for AWS Bedrock integration.") from exc

        try:
            client = boto3.client("bedrock-runtime", region_name=self.region)
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            kwargs: dict = {
                "modelId": self.model_id,
                "messages": messages,
                "inferenceConfig": {"temperature": 0.2},
            }
            if system:
                kwargs["system"] = [{"text": system}]
            response = client.converse(**kwargs)
            output_message = response.get("output", {}).get("message", {})
            content_list = output_message.get("content", [])
            if content_list and "text" in content_list[0]:
                return content_list[0]["text"]
            return ""
        except Exception as exc:
            logger.warning("bedrock request failed", extra={"extra_fields": {"error": str(exc)}})
            raise AiUnavailableError(
                f"AWS Bedrock request failed for model {self.model_id} in {self.region}: {exc}"
            ) from exc


def get_provider() -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    if settings.llm_provider == "openai":
        return OpenAICompatibleProvider()
    if settings.llm_provider == "bedrock":
        return BedrockProvider()
    return NullProvider()


def provider_status() -> dict:
    provider = get_provider()
    available = False
    detail = "AI provider disabled."
    if not isinstance(provider, NullProvider):
        try:
            available = provider.health()
            detail = "reachable" if available else "unreachable"
        except Exception as exc:  # noqa: BLE001
            detail = str(exc)

    model_name = settings.ollama_model
    if settings.llm_provider == "openai":
        model_name = settings.openai_model
    elif settings.llm_provider == "bedrock":
        model_name = settings.bedrock_model_id

    return {
        "provider": provider.name,
        "configured": settings.llm_provider,
        "available": available,
        "detail": detail,
        "model": model_name,
    }


def extract_json(text: str) -> dict | list | None:
    """Best-effort extraction of a JSON object/array from model output."""
    text = text.strip()
    if not text:
        return None
    # strip markdown fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1] or [-1])
    if start == -1:
        return None
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
