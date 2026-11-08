"""CLI: uv run python -m app.seed [--file PATH] [--dry-run]"""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.seed.loader import BACKEND_DIR, DEFAULT_CATALOG, CatalogError, load_catalog, seed


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(BACKEND_DIR.parent))
    except ValueError:
        return str(path)


def main(
    argv: Sequence[str] | None = None, session_factory: Callable[[], Session] | None = None
) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.seed", description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_CATALOG, help="catalog JSON path")
    parser.add_argument("--dry-run", action="store_true", help="validate and roll back")
    args = parser.parse_args(argv)
    path: Path = args.file

    print(f"Catalog: {_display(path)}", flush=True)
    try:
        catalog = load_catalog(path)
    except CatalogError as exc:
        for err in exc.errors:
            print(f"ERROR {err}", file=sys.stderr)
        return 1

    if session_factory is None:
        from app.db import SessionLocal

        session_factory = SessionLocal

    session = session_factory()
    try:
        report = seed(session, catalog, dry_run=args.dry_run)
    except (CatalogError, SQLAlchemyError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    print(("[dry-run, rolled back] " if args.dry_run else "") + report.summary())
    if report.orphaned:
        print(f"WARNING: in DB but not in file (kept): {', '.join(report.orphaned)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
