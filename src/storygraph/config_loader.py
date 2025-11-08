# src/storygraph/config_loader.py
from __future__ import annotations
import os, yaml
from pathlib import Path
from typing import Dict, Tuple

_ROOT = Path(__file__).resolve().parents[2]   # repo root
_CFG = _ROOT / "config" / "llm_profiles.yaml"

_cache: Dict[str, Dict] = {}

def _load_yaml() -> Dict:
    global _cache
    if "yaml" in _cache:
        return _cache["yaml"]
    with _CFG.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _cache["yaml"] = data
    return data

def load_llm_profile(profile_name: str) -> Dict[str, any]:
    """
    Load LLM profile and return dict with model assignments and params.
    Returns: {"planner": "model", "draft": "model", "fact": "model", "revision": "model", "params": {...}}
    """
    data = _load_yaml()
    prof = (data.get("profiles") or {}).get(profile_name)
    if not prof:
        raise RuntimeError(f"Profile '{profile_name}' not found in {_CFG}")

    apply_all = (prof.get("apply_to_all") or "").strip() or None
    stages = prof.get("stages") or {}
    params = prof.get("params") or {}

    # Build stage map with precedence (env > stages > apply_to_all)
    model_env = {
        "planner": os.getenv("LLM_PLANNER_MODEL"),
        "draft": os.getenv("LLM_DRAFT_MODEL"),
        "fact": os.getenv("LLM_FACT_MODEL"),
        "revision": os.getenv("LLM_REVISION_MODEL"),
    }
    result = {}
    for stage in ("planner", "draft", "fact", "revision"):
        # Handle nested model structure from YAML
        stage_config = stages.get(stage)
        if isinstance(stage_config, dict):
            stage_model = stage_config.get("model")
        else:
            stage_model = stage_config
            
        result[stage] = (
            model_env[stage]
            or stage_model
            or apply_all
        )
        if not result[stage]:
            raise RuntimeError(f"No model resolved for stage '{stage}' (profile '{profile_name}')")

    return {"planner": result["planner"], "draft": result["draft"], 
            "fact": result["fact"], "revision": result["revision"], "params": params}

def get_llm_settings() -> Tuple[Dict[str,str], Dict[str,object]]:
    """
    Returns (models_by_stage, params) from the active profile.
    Order of precedence for models:
      1) Per-stage env overrides (LLM_PLANNER_MODEL, LLM_DRAFT_MODEL, LLM_FACT_MODEL, LLM_REVISION_MODEL)
      2) Profile stages mapping
      3) Profile apply_to_all
    Env var LLM_PROFILE selects a profile (default: 'default').
    """
    data = _load_yaml()
    prof_name = os.getenv("LLM_PROFILE", "default")
    prof = (data.get("profiles") or {}).get(prof_name)
    if not prof:
        raise RuntimeError(f"Profile '{prof_name}' not found in {_CFG}")

    apply_all = (prof.get("apply_to_all") or "").strip() or None
    stages = prof.get("stages") or {}
    params = prof.get("params") or {}

    # Build stage map with precedence (env > stages > apply_to_all)
    model_env = {
        "planner": os.getenv("LLM_PLANNER_MODEL"),
        "draft": os.getenv("LLM_DRAFT_MODEL"),
        "fact": os.getenv("LLM_FACT_MODEL"),
        "revision": os.getenv("LLM_REVISION_MODEL"),
    }
    result = {}
    for stage in ("planner", "draft", "fact", "revision"):
        result[stage] = (
            model_env[stage]
            or stages.get(stage)
            or apply_all
        )
        if not result[stage]:
            raise RuntimeError(f"No model resolved for stage '{stage}' (profile '{prof_name}')")

    return result, params
