from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.features.open_api.auth import ensure_default_open_api_key  # noqa: E402


def main() -> None:
    result = ensure_default_open_api_key()
    print(f"name={result['name']}")
    print(f"source={result['source']}")
    print(f"key={result['key']}")


if __name__ == "__main__":
    main()
