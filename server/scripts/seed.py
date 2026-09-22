"""Re-run seed only (tables must exist)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal  # noqa: E402
from scripts.seed_data import seed_all  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        seed_all(db)
        print("OK: seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
