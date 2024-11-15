from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_url():
    user = os.getenv("USERDB")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    port = os.getenv("PORT")
    db = os.getenv("DB")
    db_url = f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{db}"
    print(db_url)
    return db_url


SQLALCHEMY_DATABASE_URI = get_url()


def get_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    return engine
