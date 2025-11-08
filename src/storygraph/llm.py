from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Tuple

# Optional backends
try:
    from openai import OpenAI  # openai>=1.43
except Exception:
    OpenAI = None

try:
    import anthropic  # anthropic>=0.34
except Exception:
    anthropic = None


# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

@dataclass
class LLMConfig:
    model: str
    seed: int = 137
    temperature: float = 0.2


# ------------------------------------------------------------
# MAIN CLIENT
# ------------------------------------------------------------

class LLMClient:
    """
    Unified LLM client for:
        - OpenAI GPT-5 / o1 / o3 via Responses API
        - OpenAI legacy chat completions
        - Anthropic Claude 3.5 / Opus / Sonnet

    Includes robust JSON extraction and sanitation.
    """

    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        self.backend, self.client = self._select_backend(cfg.model)

    def _select_backend(self, model: str) -> Tuple[str, Any]:
        """
        Determine backend handler.
        """

        if model.startswith("openai/"):
            if not OpenAI:
                raise RuntimeError("openai package not installed")
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY is not set")
            return ("openai", OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

        if model.startswith("anthropic/"):
            if not anthropic:
                raise RuntimeError("anthropic package not installed")
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise RuntimeError("ANTHROPIC_API_KEY is not set")
            return ("anthropic", anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")))

        raise RuntimeError(f"Unknown backend for model: {model}")

    # ------------------------------------------------------------
    # MAIN JSON ENTRYPOINT
    # ------------------------------------------------------------

    def complete_json(self, system: str, user: str, schema_hint: str) -> Dict[str, Any]:
        if self.backend == "openai":
            return self._openai_json(system, user, schema_hint)
        if self.backend == "anthropic":
            return self._anthropic_json(system, user, schema_hint)
        raise RuntimeError("Unsupported backend")

    # ------------------------------------------------------------
    # OPENAI BACKEND
    # ------------------------------------------------------------

    def _openai_json(self, system: str, user: str, schema_hint: str) -> Dict[str, Any]:
        """
        Unified OpenAI handler:
        - GPT-5, o1, o3 → Responses API
        - gpt-4x, etc     → Chat Completions API with json mode
        """

        model_name = self.cfg.model.split("/", 1)[1]

        # ----------------------------
        # RESPONSES API for GPT-5/o1/o3
        # ----------------------------
        if model_name.startswith(("gpt-5", "o1", "o3")):
            sys = (
                "Return ONLY valid JSON. No commentary. "
                "Validate keys/types using this schema hint:\n"
                f"{schema_hint}\n"
                "No markdown. No explanations."
            )

            combined = f"SYSTEM:\n{sys}\n\nUSER:\n{user}"

            resp = self.client.responses.create(
                model=model_name,
                input=combined,
                max_output_tokens=4096,
            )

            raw = resp.output_text or ""

            # direct load
            try:
                return json.loads(raw)
            except Exception:
                pass

            # fallback
            sanitized = self._extract_and_sanitize_json(raw)
            if sanitized is not None:
                return sanitized

            raise RuntimeError(
                "OpenAI GPT-5/o-model returned invalid JSON after sanitation:\n"
                + raw[:2000]
            )

        # ----------------------------
        # ChatCompletion JSON mode fallback
        # ----------------------------
        resp = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )

        raw = resp.choices[0].message.content

        # direct load
        try:
            return json.loads(raw)
        except Exception:
            sanitized = self._extract_and_sanitize_json(raw)
            if sanitized:
                return sanitized
            raise RuntimeError(
                "OpenAI ChatCompletion returned invalid JSON:\n" + raw[:2000]
            )

    # ------------------------------------------------------------
    # ANTHROPIC BACKEND
    # ------------------------------------------------------------

    def _anthropic_json(self, system: str, user: str, schema_hint: str) -> Dict[str, Any]:
        """
        Anthropic JSON extraction with strict instructions + sanitizer fallback.
        """

        sys = (
            system
            + "\n\nReturn ONLY valid JSON. "
            + "Validate keys/types using this schema:\n"
            + schema_hint
            + "\nNo markdown. No commentary."
        )

        msg = self.client.messages.create(
            model=self.cfg.model.split("/", 1)[1],
            temperature=self.cfg.temperature,
            system=sys,
            max_tokens=4096,
            messages=[{"role": "user", "content": user}],
        )

        text = "".join([p.text for p in msg.content if hasattr(p, "text")])

        # direct load
        try:
            return json.loads(text)
        except Exception:
            pass

        # fallback
        sanitized = self._extract_and_sanitize_json(text)
        if sanitized:
            return sanitized

        raise RuntimeError(
            "Anthropic returned invalid JSON even after sanitation:\n"
            + text[:2000]
        )

    # ------------------------------------------------------------
    # JSON SANITIZER
    # ------------------------------------------------------------

    def _extract_and_sanitize_json(self, text: str):
        """
        Extracts the first {...} block; fixes:
        - markdown code fences (```json ... ```)
        - unescaped newlines inside strings
        - trailing commas
        - broken/unterminated strings
        - garbage after JSON
        """
        
        # First, strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith('```'):
            # Remove opening fence (```json or just ```)
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            # Remove closing fence
            cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        
        # extract first {...} using balanced brace matching
        brace_count = 0
        start_idx = cleaned.find('{')
        if start_idx == -1:
            return None
        
        for i, char in enumerate(cleaned[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    chunk = cleaned[start_idx:i+1]
                    break
        else:
            return None

        # fix newlines inside string values - be more aggressive about cleaning
        chunk = re.sub(r'"\s*\n\s*"', '" "', chunk)
        
        # Replace literal \n sequences in strings with spaces
        chunk = chunk.replace('\\n', ' ')
        
        # remove actual newlines (inside strings)
        chunk = chunk.replace('\n', ' ')

        # remove trailing commas in objects/arrays
        chunk = re.sub(r",\s*}", "}", chunk)
        chunk = re.sub(r",\s*]", "]", chunk)

        # Strip any trailing content after the final }
        chunk = chunk.rstrip()
        if chunk.endswith('}'):
            # Find the last } and cut there
            last_brace = chunk.rfind('}')
            chunk = chunk[:last_brace + 1]

        try:
            return json.loads(chunk)
        except Exception:
            return None
