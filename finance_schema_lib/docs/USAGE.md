# Huong Dan Su Dung Trong Du An Con

## 1. Cai thu vien

Neu dung env rieng da tao:

```bash
conda activate finance-schema
```

Neu du an con co env rieng:

```bash
python -m pip install -e /home/minh_chau/Documents/Finance/data_colection_finance_report/finance_schema_lib
```

Sau nay neu thu vien duoc dua len git, du an con co the cai bang git URL:

```bash
python -m pip install "git+ssh://git@your-git-server/finance-schema.git"
```

## 2. Tao `.env` trong du an con

Dat `.env` tai root cua du an con:

```env
USERDB=postgres
PASSWORD=postgres
SERVER=localhost
PORT=5432
DB=finance
```

Hoac:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/finance
```

Thu tu uu tien:

1. `FINANCE_SCHEMA_ENV_FILE`
2. `FINANCE_DATABASE_URL`
3. `DATABASE_URL`
4. `USERDB`, `PASSWORD`, `SERVER`, `PORT`, `DB`

## 3. Chay migration

Tai root cua du an con:

```bash
finance-schema current
finance-schema history
finance-schema upgrade head
```

## 4. Import model trong code du an con

```python
from finance_schema.models import Symbol, UpdateQuote
from finance_schema.db import scoped_session

with scoped_session() as session:
    symbols = session.query(Symbol).limit(10).all()
```

## 5. Update schema moi

Neu package duoc cai editable tu folder local, chi can pull/update source `finance_schema_lib`, sau do:

```bash
finance-schema upgrade head
```

Neu package duoc cai non-editable:

```bash
python -m pip install --upgrade /path/to/finance_schema_lib
finance-schema upgrade head
```
