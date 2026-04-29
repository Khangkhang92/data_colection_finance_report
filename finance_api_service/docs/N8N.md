# n8n Integration

## Basic HTTP Request node

Method:

```text
POST
```

URL:

```text
http://localhost:8000/api/v1/webhooks/posts/sync
```

Body:

```json
{
  "total": 100,
  "post_type": 1,
  "step": 50
}
```

Expected response:

```json
{
  "service": "posts",
  "status": "ok",
  "fetched": 100,
  "saved": 100,
  "errors": []
}
```

## Recommended workflow

1. Cron node triggers schedule.
2. HTTP Request node calls one sync endpoint.
3. IF node checks `status == "ok"`.
4. On success, continue downstream workflow.
5. On error, send notification with `errors`.

## Endpoint examples

Sync finance statements:

```json
{
  "symbols": ["A32", "AAA"],
  "report_types": [1, 2],
  "year": 2024,
  "quarter": 3,
  "limit": 1
}
```

Sync company details:

```json
{
  "symbols": ["AAA"],
  "include_holders": true,
  "include_subsidiaries": true
}
```

Sync history prices:

```json
{
  "symbols": ["AAA"],
  "start_date": "2026-01-01",
  "end_date": "2026-04-23",
  "limit": 100
}
```
