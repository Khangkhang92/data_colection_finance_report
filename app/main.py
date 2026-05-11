from __future__ import annotations

import argparse

import uvicorn

from common.config.finance_api import get_settings


def serve() -> None:
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        app_dir="app/gateway_api",
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="finance-api")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("serve", help="Start the FastAPI server")

    args = parser.parse_args()
    if args.command in {None, "serve"}:
        serve()


if __name__ == "__main__":
    main()
