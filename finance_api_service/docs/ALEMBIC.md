# Chay Alembic De Tao Bang Tren Database

Tai lieu nay huong dan cach apply migration de tao cac bang trong database cho
project hien tai, voi:

- database PostgreSQL chay bang Docker
- models va migrations nam trong package `finance-schema`
- file cau hinh database nam trong `finance_api_service/.env`
- moi truong Python dung Miniconda env `module1`

## 1. Dieu kien can co

Can dam bao:

- container `finance-postgres` dang chay
- env `module1` da ton tai
- `finance-schema` va `finance_api_service` da duoc cai vao env

Kiem tra nhanh:

```bash
docker ps
/home/khangst92/miniconda3/bin/conda env list
```

## 2. Cai package vao env `module1`

Chay lan luot:

```bash
cd /home/khangst92/Documents/finance/data_colection_finance_report/finance_schema_lib
/home/khangst92/miniconda3/bin/conda run -n module1 python -m pip install -r requirements.txt
```

```bash
cd /home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service
/home/khangst92/miniconda3/bin/conda run -n module1 python -m pip install -r requirements.txt
/home/khangst92/miniconda3/bin/conda run -n module1 python -m pip install -e .
```

Trong mono-repo local, `finance_api_service/requirements.txt` cai editable
`../finance_schema_lib`. Neu `finance-schema` da duoc publish rieng, co the dung
`finance_api_service/requirements.release.txt`.

## 3. Kiem tra file `.env`

Project dang doc database config tu:

```text
finance_api_service/.env
```

Gia tri dang dung hien tai:

```env
DATABASE_URL=postgresql+psycopg2://finance:finance@localhost:5432/finance
```

Neu muon Alembic doc dung file nay, can set bien:

```bash
export FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env
```

Neu khong muon `export`, co the prefix truc tiep vao tung lenh nhu cac vi du ben
duoi.

## 4. Xem lich su migration

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema history
```

Xem revision hien tai cua database:

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema current -v
```

## 5. Tao bang tren database

Lenh chinh de apply tat ca migration:

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema upgrade head
```

Lenh nay se:

- doc migrations trong package `finance-schema`
- ket noi toi database khai bao trong `.env`
- tao bang `alembic_version`
- tao toan bo bang business theo migration chain

Voi database local hien tai, sau khi chay xong se len revision:

```text
3e9b5d4b1a2c (head)
```

## 6. Kiem tra bang da duoc tao

Kiem tra revision sau migration:

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema current -v
```

Kiem tra danh sach bang:

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 python -c "from sqlalchemy import inspect; from finance_schema.db import get_engine; insp=inspect(get_engine()); print('\n'.join(sorted(insp.get_table_names())))"
```

Mot so bang chinh se xuat hien:

```text
alembic_version
daily_market
data
finance_report
history_data_processing
history_price
major_holder
market
market_mentions
post_groups
post_sources
posts
score
session_quote
subsidiaries
symbol
tagged_symbols
update_quote
```

## 7. Lenh rollback va stamp

Rollback 1 revision:

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema downgrade -1
```

Danh dau database dang o `head` ma khong chay SQL:

```bash
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema stamp head
```

Chi dung `stamp` khi chac chan schema trong database da trung voi migration head.

## 8. Loi thuong gap

Neu gap loi:

```text
Missing database configuration
```

Hay kiem tra:

- file `finance_api_service/.env` co ton tai khong
- bien `FINANCE_SCHEMA_ENV_FILE` co tro dung file khong
- `DATABASE_URL` hoac cac bien `USERDB`, `PASSWORD`, `SERVER`, `PORT`, `DB`

Neu gap loi ket noi PostgreSQL, kiem tra:

```bash
docker ps
docker logs finance-postgres --tail 50
```

## 9. Quy trinh ngan gon de dung hang ngay

Neu da setup xong moi truong, moi lan can tao hoac cap nhat bang chi can:

```bash
cd /home/khangst92/Documents/finance/data_colection_finance_report
FINANCE_SCHEMA_ENV_FILE=/home/khangst92/Documents/finance/data_colection_finance_report/finance_api_service/.env \
/home/khangst92/miniconda3/bin/conda run -n module1 finance-schema upgrade head
```
