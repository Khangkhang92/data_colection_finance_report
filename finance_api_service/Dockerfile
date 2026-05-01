# syntax=docker/dockerfile:1.7
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG FINANCE_SCHEMA_REPO=ssh://git@github.com/Khangkhang92/schema_lib.git
ARG FINANCE_SCHEMA_REF=main

COPY . /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y git ca-certificates openssh-client \
    && mkdir -p -m 0700 /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=ssh \
    python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        "finance-schema @ git+${FINANCE_SCHEMA_REPO}@${FINANCE_SCHEMA_REF}" \
        -e /app

WORKDIR /app

EXPOSE 8000

CMD ["finance-api", "serve"]
