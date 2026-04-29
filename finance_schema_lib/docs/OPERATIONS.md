# Van Hanh Migration

## Lenh co ban

Xem revision hien tai cua database:

```bash
finance-schema current
```

Xem lich su migration:

```bash
finance-schema history
```

Apply tat ca migration moi:

```bash
finance-schema upgrade head
```

Rollback mot revision:

```bash
finance-schema downgrade -1
```

Gan database vao revision ma khong chay SQL:

```bash
finance-schema stamp head
```

## Quy trinh de xuat cho production

1. Backup database truoc khi migrate.
2. Chay `finance-schema current` de biet revision hien tai.
3. Chay migration tren staging/dev truoc.
4. Review SQL trong migration file neu migration co drop/alter cot lon.
5. Chay `finance-schema upgrade head` tren production.
6. Chay lai `finance-schema current` de xac nhan.

## Khi database da co bang san

Neu database da ton tai schema dung voi migration head nhung chua co bang `alembic_version`, dung:

```bash
finance-schema stamp head
```

Chi dung `stamp` khi chac chan database da dung schema. Neu khong, hay chay migration binh thuong.

## Loi cau hinh database

Neu gap loi thieu config:

```text
Missing database configuration
```

Hay kiem tra `.env` trong root du an con hoac set:

```bash
export FINANCE_SCHEMA_ENV_FILE=/path/to/.env
```

## Luu y downgrade

Khong phai migration nao cung rollback an toan. Truoc khi downgrade production, doc ham `downgrade()` trong migration file lien quan va backup database.
