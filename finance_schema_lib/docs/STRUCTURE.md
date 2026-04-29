# Cau Truc Thu Vien

```text
finance_schema_lib/
├── .gitignore
├── README.md
├── environment.yml
├── pyproject.toml
├── docs/
│   ├── STRUCTURE.md
│   ├── USAGE.md
│   ├── DEVELOPMENT.md
│   └── OPERATIONS.md
└── finance_schema/
    ├── __init__.py
    ├── alembic.ini
    ├── cli.py
    ├── config.py
    ├── db.py
    ├── models/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── symbol.py
    │   ├── report.py
    │   ├── market.py
    │   ├── update_quote.py
    │   └── ...
    └── migrations/
        ├── env.py
        ├── script.py.mako
        └── versions/
            └── *.py
```

## Vai tro tung phan

`pyproject.toml`: khai bao package `finance-schema`, dependencies va command line script `finance-schema`.

`environment.yml`: tao conda env rieng bang Miniconda.

`finance_schema/models/`: noi dat SQLAlchemy models dung chung. Tat ca model can duoc import trong `finance_schema/models/__init__.py` de Alembic autogenerate thay duoc metadata.

`finance_schema/migrations/`: Alembic migration history dung chung. Day la noi Alembic doc revisions khi chay `finance-schema upgrade head`.

`finance_schema/migrations/env.py`: cau hinh Alembic runtime. File nay load `.env`, lay database URL va gan `target_metadata = CommonModel.metadata`.

`finance_schema/alembic.ini`: cau hinh Alembic dong goi trong package. Nguoi dung khong can tao `alembic.ini` rieng trong du an con.

`finance_schema/cli.py`: CLI wrapper cho Alembic. CLI resolve dung migration folder ben trong package, nen co the chay tu bat ky du an con nao.

`finance_schema/config.py`: doc config database tu `.env`, `DATABASE_URL`, `FINANCE_DATABASE_URL`, hoac `FINANCE_SCHEMA_ENV_FILE`.

`finance_schema/db.py`: helper tao SQLAlchemy engine va session neu du an con muon import dung chung.

## File sinh ra khong phai source

Nhung file/folder sau co the xuat hien sau khi cai dat hoac chay Python va khong nen commit:

```text
finance_schema.egg-info/
__pycache__/
*.pyc
build/
dist/
```
