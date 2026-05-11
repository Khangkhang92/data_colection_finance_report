# syntax=docker/dockerfile:1.7
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


COPY . /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y git ca-certificates openssh-client \
    && mkdir -p -m 0700 /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=ssh \
    python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        -e /app/app

WORKDIR /app

EXPOSE 8000

CMD ["finance-api", "serve"]
