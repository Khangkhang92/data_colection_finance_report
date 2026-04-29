# finance-schema

`finance-schema` la thu vien schema dung chung cho nhieu du an con. Thu vien nay gom SQLAlchemy models, Alembic migrations va CLI rieng de moi du an con chi can update package la co schema moi.

## Muc tieu

- Tap trung model database tai mot noi duy nhat.
- Tap trung Alembic migration history tai mot noi duy nhat.
- Du an con khong can copy folder `models/` va `alembic/`.
- Khi co bang/cot moi, update thu vien roi chay `finance-schema upgrade head`.

## Cai dat nhanh bang Miniconda

Tu folder `finance_schema_lib`:

```bash
conda env create -f environment.yml
conda activate finance-schema
```

Neu muon cai vao conda env dang dung:

```bash
python -m pip install -e /home/minh_chau/Documents/Finance/data_colection_finance_report/finance_schema_lib
```

## Cau hinh database

Trong root cua moi du an con, tao `.env`:

```env
USERDB=postgres
PASSWORD=postgres
SERVER=localhost
PORT=5432
DB=finance
```

Hoac dung URL truc tiep:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/finance
```

Neu muon tro den file env khac:

```bash
export FINANCE_SCHEMA_ENV_FILE=/path/to/.env
```

## Lenh thuong dung

```bash
finance-schema history
finance-schema current
finance-schema upgrade head
finance-schema downgrade -1
finance-schema revision --autogenerate -m "add new model"
```

## Cau truc tai lieu

- [docs/STRUCTURE.md](docs/STRUCTURE.md): cau truc thu vien.
- [docs/USAGE.md](docs/USAGE.md): cach dung trong du an con.
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): workflow them/sua model va tao migration.
- [docs/OPERATIONS.md](docs/OPERATIONS.md): lenh van hanh database an toan.

## Kiem tra nhanh

```bash
conda run -n finance-schema finance-schema history
conda run -n finance-schema python -c "import finance_schema.models"
```
