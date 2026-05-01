# Migration Plan From Old Scripts

## Phase 1: Keep old behavior

- Reuse old env variable names.
- Reuse existing database models from `finance-schema`.
- Recreate old script flows as services.
- Keep endpoints small and explicit for external orchestration or manual triggers.

## Phase 2: Stabilize data contracts

- Add Pydantic response models per endpoint.
- Add tests for transforms.
- Add idempotency rules for each upsert.
- Add structured logs per sync run.

## Phase 3: Production readiness

- Add auth token for webhook endpoints.
- Add background jobs if request time is too long.
- Add job status table.
- Add retry/dead-letter handling.
- Add Dockerfile and deployment config.
