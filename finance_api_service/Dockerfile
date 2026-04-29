FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY finance_schema_lib /app/finance_schema_lib
COPY finance_api_service /app/finance_api_service

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        -e /app/finance_schema_lib \
        -e /app/finance_api_service

WORKDIR /app/finance_api_service

EXPOSE 8000

CMD ["finance-api", "serve"]
