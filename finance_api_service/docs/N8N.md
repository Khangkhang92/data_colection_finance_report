# n8n Integration

## Basic HTTP Request node

Method:

```text
POST
```

URL:

```text
http://localhost:8000/fireant_data/webhooks/posts/sync
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
  "job_id": "uuid",
  "job_name": "posts_sync",
  "status": "queued",
  "deduplicated": false,
  "message": "Posts sync job accepted"
}
```

## Recommended workflow

1. Cron node triggers schedule.
2. HTTP Request node calls one sync endpoint.
3. Save `job_id` from response.
4. HTTP Request node calls `GET /fireant_data/jobs/{job_id}`.
5. IF node checks `status == "completed"` hoac `status == "partial_error"`.

## Endpoint examples

Sync finance statements:

Khong can body. Goi:

```text
POST http://localhost:8000/fireant_data/webhooks/finance-statements/sync
```

Sync company details:

```json
{
  "include_holders": true,
  "include_subsidiaries": true
}
```

Sync market mentions:

Khong can body. Goi:

```text
POST http://localhost:8000/fireant_data/webhooks/market-mentions/sync
```

Sync session quotes:

Khong can body. Goi:

```text
POST http://localhost:8000/fireant_data/webhooks/session-quotes/sync
```

Sync history prices:

Khong can body. Goi:

```text
POST http://localhost:8000/fireant_data/webhooks/history-prices/sync
```
