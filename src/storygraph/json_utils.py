import json
from typing import Any, Dict


def coerce_json(data: Any) -> Dict:
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        return json.loads(data)
    raise ValueError("Unsupported JSON input")
