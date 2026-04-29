from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    env_file = os.getenv("FINANCE_SCHEMA_ENV_FILE")
    if env_file:
        load_dotenv(Path(env_file).expanduser(), override=False)
        return

    load_dotenv(Path.cwd() / ".env", override=False)


def get_database_url() -> str:
    load_project_env()

    url = os.getenv("FINANCE_DATABASE_URL") or os.getenv("DATABASE_URL")
    if url:
        return url

    user = os.getenv("USERDB")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    port = os.getenv("PORT")
    database = os.getenv("DB")

    missing = [
        name
        for name, value in {
            "USERDB": user,
            "PASSWORD": password,
            "SERVER": server,
            "PORT": port,
            "DB": database,
        }.items()
        if not value
    ]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            "Missing database configuration. Set DATABASE_URL or these variables: "
            f"{names}"
        )

    return f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{database}"
