FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG FINANCE_SCHEMA_REPO=https://github.com/Khangkhang92/schema_lib.git
ARG FINANCE_SCHEMA_REF=main

COPY . /app

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        "finance-schema @ git+${FINANCE_SCHEMA_REPO}@${FINANCE_SCHEMA_REF}" \
        -e /app

WORKDIR /app

EXPOSE 8000

CMD ["finance-api", "serve"]
