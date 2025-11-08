#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
pip install -r requirements.txt
python - <<'PY'
from pathlib import Path
Path('data/sources').mkdir(parents=True, exist_ok=True)
Path('data/runs').mkdir(parents=True, exist_ok=True)
print('Scaffold ready')
PY