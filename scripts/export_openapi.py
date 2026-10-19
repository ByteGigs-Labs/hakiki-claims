import json
import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://contract@localhost/contract")
os.environ.setdefault("HMAC_KEY", "contract")

from api.main import app  # noqa: E402

SNAPSHOT = Path(__file__).resolve().parent.parent / "docs" / "openapi.json"


def current_spec() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    SNAPSHOT.write_text(current_spec())
