"""
CLI seed generator for a mixed-industry 5-project portfolio.

Usage:
    cd backend
    .venv/Scripts/python scripts/seed_industry_portfolio.py --user-email test1@test.com
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import warnings
from datetime import date
from pathlib import Path
from uuid import UUID

from sqlalchemy.exc import SAWarning

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal
from scripts.seeding.builders import render_seed_result, seed_industry_portfolio

warnings.filterwarnings(
    "ignore",
    message=r"Identity map already had an identity for .*app\.models\.task\.Task.*",
    category=SAWarning,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed mixed-industry portfolio projects for dashboard/testing."
    )
    parser.add_argument("--user-email", required=True, help="Existing user email")
    parser.add_argument(
        "--org-id",
        type=UUID,
        default=None,
        help="Target organization UUID (optional; defaults to user's first org)",
    )
    parser.add_argument(
        "--scenario-pack",
        default="mixed-industry",
        choices=["mixed-industry"],
        help="Scenario pack to generate",
    )
    parser.add_argument(
        "--seed-key",
        default="v1",
        help="Idempotency/version key stored in project.settings.seed_meta",
    )
    parser.add_argument(
        "--base-date",
        type=date.fromisoformat,
        default=None,
        help="Base date in YYYY-MM-DD (defaults to today)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan and expected counts without writing data",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    async with AsyncSessionLocal() as db:
        result = await seed_industry_portfolio(
            db,
            user_email=args.user_email,
            org_id=args.org_id,
            scenario_pack=args.scenario_pack,
            seed_key=args.seed_key,
            base_date=args.base_date,
            dry_run=args.dry_run,
        )
        print(render_seed_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
