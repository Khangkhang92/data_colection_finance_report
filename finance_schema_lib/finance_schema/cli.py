from __future__ import annotations

import argparse
from importlib import resources
from pathlib import Path

from alembic import command
from alembic.config import Config


def make_config() -> Config:
    ini_path = resources.files("finance_schema").joinpath("alembic.ini")
    migrations_path = resources.files("finance_schema").joinpath("migrations")

    config = Config(str(ini_path))
    config.set_main_option("script_location", str(migrations_path))
    return config


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="finance-schema",
        description="Run shared finance Alembic migrations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    upgrade = subparsers.add_parser("upgrade")
    upgrade.add_argument("revision", nargs="?", default="head")

    downgrade = subparsers.add_parser("downgrade")
    downgrade.add_argument("revision")

    stamp = subparsers.add_parser("stamp")
    stamp.add_argument("revision")

    current = subparsers.add_parser("current")
    current.add_argument("--verbose", "-v", action="store_true")

    history = subparsers.add_parser("history")
    history.add_argument("--verbose", "-v", action="store_true")

    revision = subparsers.add_parser("revision")
    revision.add_argument("-m", "--message")
    revision.add_argument("--autogenerate", action="store_true")

    args = parser.parse_args()
    config = make_config()

    if args.command == "upgrade":
        command.upgrade(config, args.revision)
    elif args.command == "downgrade":
        command.downgrade(config, args.revision)
    elif args.command == "stamp":
        command.stamp(config, args.revision)
    elif args.command == "current":
        command.current(config, verbose=args.verbose)
    elif args.command == "history":
        command.history(config, verbose=args.verbose)
    elif args.command == "revision":
        command.revision(
            config,
            message=args.message,
            autogenerate=args.autogenerate,
        )
    else:
        parser.error(f"Unsupported command: {args.command}")
