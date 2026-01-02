# haval_insights/llm_client.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict, Union


class LLMResponse:
    def __init__(self, content: str, raw: Optional[Any] = None):
        self.content = content
        self.raw = raw


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: Union[List[Dict[str, str]], str],
        **kwargs: Any,
    ) -> LLMResponse:
        ...


class GeminiClient(BaseLLMClient):
    """
    Gemini wrapper.

    - Uses google-generativeai under the hood.
    - Returns empty content string if the model returns no usable text
      (e.g., safety block / max-tokens), so callers can handle gracefully.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.2,
    ):
        import google.generativeai as genai  # type: ignore

        self._genai = genai
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

        self._genai.configure(api_key=self.api_key)
        self._model = self._genai.GenerativeModel(self.model_name)

    def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> LLMResponse:
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_output_tokens": kwargs.get("max_tokens", 2048),
        }

        print(f"LLM generation config: {generation_config}")
        print(f"LLM prompt: \n{prompt}")
        try:
            resp = self._model.generate_content(
                prompt,
                generation_config=generation_config,
            )
        except Exception as e:
            # If the API itself fails, return empty content but keep raw error
            print(f"LLM generation error: {e}")
            return LLMResponse(content="", raw=e)

        # DO NOT call resp.text (it raises if there are no Parts)
        print(f"LLM raw response: {resp}")
        text = self._extract_text(resp)
        print(f"LLM extracted text:\n{text}")
        return LLMResponse(content=text, raw=resp)

    def _extract_text(self, resp: Any) -> str:
        """
        Safely extract concatenated text from a Gemini response.

        If there are no candidates/parts (e.g., safety filter), returns "".
        """
        try:
            candidates = getattr(resp, "candidates", None)
            if not candidates:
                return ""

            first = candidates[0]
            content = getattr(first, "content", None)
            if not content:
                return ""

            parts = getattr(content, "parts", None)
            if not parts:
                return ""

            chunks = []
            for p in parts:
                # Parts usually have a `text` attribute for text content
                t = getattr(p, "text", None)
                if t:
                    chunks.append(t)
            return "".join(chunks).strip()
        except Exception:
            # If anything unexpected happens, just return empty string
            return ""


class GrokClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str,
        model_name: str = "grok-3-fast",
        temperature: float = 0.2,
        base_url: str = "https://api.x.ai/v1",
    ):
        # Lazy import so this file doesn't hard-depend on openai unless needed.
        from openai import OpenAI  # type: ignore

        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.base_url = base_url

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def generate(
        self,
        prompt: Union[List[Dict[str, str]], str],
        **kwargs: Any,
    ) -> LLMResponse:
        # Mirror GeminiClient-style config & prints
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }


        # print(f"LLM generation config: {generation_config}")
        # print(f"LLM prompt: \n{prompt}")

        try:
            resp = self._client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                temperature=generation_config["temperature"],
            )
        except Exception as e:
            print(f"LLM generation error (Grok): {e}")
            return LLMResponse(content="", raw=e)

        # print(f"LLM raw response (Grok): {resp}")
        text = self._extract_text(resp)
        # print(f"LLM extracted text (Grok):\n{text}")
        return LLMResponse(content=text, raw=resp)

    def _extract_text(self, resp: Any) -> str:
        """
        Safely extract text from an OpenAI-compatible ChatCompletion response.

        Handles both:
        - resp.choices[0].message.content as a simple string
        - resp.choices[0].message.content as a list of parts (newer SDKs)
        """
        try:
            # Support both attribute and dict-style access just in case.
            choices = getattr(resp, "choices", None)
            if choices is None and isinstance(resp, dict):
                choices = resp.get("choices")

            if not choices:
                return ""

            first = choices[0]

            message = getattr(first, "message", None)
            if message is None and isinstance(first, dict):
                message = first.get("message")

            if message is None:
                return ""

            content = getattr(message, "content", None)
            if content is None and isinstance(message, dict):
                content = message.get("content")

            # Most common: simple string
            if isinstance(content, str):
                return content.strip()

            # Some clients use a list of content parts
            if isinstance(content, list):
                chunks = []
                for part in content:
                    if isinstance(part, str):
                        chunks.append(part)
                    elif isinstance(part, dict):
                        # OpenAI-style content parts: {"type": "text", "text": "..."}
                        if part.get("type") == "text":
                            chunks.append(part.get("text", ""))
                        elif "text" in part:
                            chunks.append(part["text"])
                    else:
                        # Object with .text attribute
                        t = getattr(part, "text", None)
                        if t:
                            chunks.append(t)
                return "".join(chunks).strip()

            # Fallback: best-effort string
            return str(content).strip() if content is not None else ""
        except Exception as e:
            print(f"Grok _extract_text error: {e}")
            return ""


class FallbackLLMClient(BaseLLMClient):
    """
    Wrapper client that automatically falls back to GPT-4o on Grok 429 errors.

    Handles:
    - 429 Rate Limit Errors (out of credits, quota exceeded)
    - 503 Service Unavailable

    Usage:
        primary = GrokClient(api_key=grok_key, model_name="grok-3-fast")
        fallback = OpenAIClient(api_key=openai_key, model_name="gpt-4o")

        client = FallbackLLMClient(
            primary_client=primary,
            fallback_client=fallback,
            primary_name="Grok-3-Fast",
            fallback_name="GPT-4o"
        )

        # Will try Grok first, auto-switch to GPT-4o on 429
        response = client.generate(messages)
    """

    def __init__(
        self,
        primary_client: BaseLLMClient,
        fallback_client: BaseLLMClient,
        primary_name: str = "Primary",
        fallback_name: str = "Fallback",
        fallback_on_empty: bool = True,
    ):
        self.primary = primary_client
        self.fallback = fallback_client
        self.primary_name = primary_name
        self.fallback_name = fallback_name
        self.fallback_on_empty = fallback_on_empty

    def generate(
        self,
        prompt: Union[List[Dict[str, str]], str],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response with automatic fallback on 429/503 errors."""
        # Try primary client first
        try:
            response = self.primary.generate(prompt, **kwargs)

            # Check if response is empty (indicates failure)
            if response.content and len(response.content.strip()) > 0:
                return response  # Success!

            # Empty response - check if we should fallback
            if self.fallback_on_empty:
                print(f"[Fallback] {self.primary_name} returned empty, switching to {self.fallback_name}")
                return self._try_fallback(prompt, kwargs)
            else:
                return response

        except Exception as e:
            error_str = str(e)

            # Check if it's a 429/503 error
            if self._should_fallback(error_str):
                error_code = self._extract_error_code(error_str)
                print(f"[Fallback] {self.primary_name} error {error_code}, switching to {self.fallback_name}")
                return self._try_fallback(prompt, kwargs)
            else:
                print(f"[Fallback] {self.primary_name} non-recoverable error: {error_str[:100]}")
                return LLMResponse(content="", raw=e)

    def _should_fallback(self, error_str: str) -> bool:
        """Check if error warrants fallback (429, 503, connection errors)."""
        fallback_indicators = [
            "429", "rate limit", "quota", "credits", "spending limit",
            "503", "500", "timeout", "connection", "unavailable"
        ]
        error_lower = error_str.lower()
        return any(indicator in error_lower for indicator in fallback_indicators)

    def _extract_error_code(self, error_str: str) -> str:
        """Extract error code from error message."""
        import re
        code_match = re.search(r'(?:error code:|error)\s*:?\s*(\d{3})', error_str, re.IGNORECASE)
        if code_match:
            return code_match.group(1)
        if "429" in error_str:
            return "429"
        if "503" in error_str:
            return "503"
        return "unknown"

    def _try_fallback(self, prompt: Union[List[Dict[str, str]], str], kwargs: Dict) -> LLMResponse:
        """Attempt fallback with secondary client."""
        try:
            print(f"[Fallback] Retrying with {self.fallback_name}...")
            response = self.fallback.generate(prompt, **kwargs)

            if response.content and len(response.content.strip()) > 0:
                print(f"[Fallback] ✅ {self.fallback_name} succeeded")
                return response
            else:
                print(f"[Fallback] ⚠️ {self.fallback_name} returned empty")
                return response

        except Exception as e:
            print(f"[Fallback] ❌ {self.fallback_name} failed: {str(e)[:100]}")
            return LLMResponse(content="", raw=e)
