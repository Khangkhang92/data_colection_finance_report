# Phat Trien Thu Vien

## Nguyen tac

- Them/sua model trong `finance_schema/models/`.
- Luon import model moi trong `finance_schema/models/__init__.py`.
- Tao migration moi trong `finance_schema/migrations/versions/`.
- Khong sua migration da chay production, tru khi database chua tung apply revision do.
- Moi du an con chi chay migration tu package nay.

## Them model moi

1. Tao file model moi trong `finance_schema/models/`.
2. Ke thua `CommonModel`.
3. Import model trong `finance_schema/models/__init__.py`.
4. Tao migration autogenerate.

Vi du:

```python
from sqlalchemy import Column, Integer, String

from finance_schema.models.base import CommonModel


class ExampleTable(CommonModel):
    __tablename__ = "example_table"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
```

Import trong `finance_schema/models/__init__.py`:

```python
from .example_table import ExampleTable
```

Tao migration:

```bash
conda activate finance-schema
finance-schema revision --autogenerate -m "add example table"
```

Kiem tra file migration vua tao trong:

```text
finance_schema/migrations/versions/
```

Apply vao database dev:

```bash
finance-schema upgrade head
```

## Sua model hien co

1. Sua class model.
2. Chay autogenerate.
3. Doc migration file vua sinh ra.
4. Neu Alembic khong detect dung thay doi, sua migration bang tay.
5. Test tren database dev truoc.

```bash
finance-schema revision --autogenerate -m "alter update quote"
finance-schema upgrade head
```

## Kiem tra package

```bash
python -m compileall -q finance_schema
finance-schema history
python -c "from finance_schema.models.base import CommonModel; import finance_schema.models; print(CommonModel.metadata.tables.keys())"
```

## Tang version

Khi release schema moi, tang version trong:

```text
finance_schema/__init__.py
pyproject.toml
```

Vi du `0.1.0` -> `0.2.0`.
