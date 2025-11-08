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
            max_tokens=8192,  # Increased from 4096 for longer outputs like revision patches
            messages=[{"role": "user", "content": user}],
        )

        text = "".join([p.text for p in msg.content if hasattr(p, "text")])

        # direct load
        try:
            return json.loads(text)
        except Exception as e:
            print(f"[DEBUG] Direct JSON parse failed: {e}")
            pass

        # fallback
        sanitized = self._extract_and_sanitize_json(text)
        if sanitized:
            return sanitized

        # Enhanced debugging output
        print("\n" + "="*80)
        print("ANTHROPIC JSON PARSE FAILURE")
        print("="*80)
        print(f"Model: {self.cfg.model}")
        print(f"Raw response length: {len(text)} chars")
        print(f"\nFirst 500 chars of raw response:")
        print(repr(text[:500]))
        print(f"\nLast 500 chars of raw response:")
        print(repr(text[-500:]))
        print("="*80 + "\n")

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
        
        # Strip markdown code fences first - be more aggressive
        cleaned = text.strip()
        
        # Remove opening fence with optional json/JSON language identifier
        cleaned = re.sub(r'^```(?:json|JSON)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        
        # Remove closing fence
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        
        # Also strip any remaining leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Extract first {...} using balanced brace matching
        brace_count = 0
        start_idx = cleaned.find('{')
        if start_idx == -1:
            print("[DEBUG SANITIZER] No opening brace found")
            return None
        
        end_idx = None
        for i, char in enumerate(cleaned[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx is None:
            print(f"[DEBUG SANITIZER] No matching closing brace (brace_count={brace_count})")
            return None
        
        chunk = cleaned[start_idx:end_idx + 1]
        print(f"[DEBUG SANITIZER] Extracted chunk length: {len(chunk)} chars")
        print(f"[DEBUG SANITIZER] Chunk ends with: {repr(chunk[-50:])}")
        
        # Fix newlines inside string values - be more aggressive about cleaning
        chunk = re.sub(r'"\s*\n\s*"', '" "', chunk)
        
        # Replace literal \n sequences in strings with spaces
        chunk = chunk.replace('\\n', ' ')
        
        # Remove actual newlines (inside strings)
        chunk = chunk.replace('\n', ' ')

        # Remove trailing commas in objects/arrays
        chunk = re.sub(r',\s*}', '}', chunk)
        chunk = re.sub(r',\s*]', ']', chunk)

        try:
            result = json.loads(chunk)
            print("[DEBUG SANITIZER] Successfully parsed JSON")
            return result
        except Exception as e:
            print(f"[DEBUG SANITIZER] JSON parse failed: {e}")
            print(f"[DEBUG SANITIZER] Failed chunk first 200 chars: {repr(chunk[:200])}")
            print(f"[DEBUG SANITIZER] Failed chunk last 200 chars: {repr(chunk[-200:])}")
            return None
        