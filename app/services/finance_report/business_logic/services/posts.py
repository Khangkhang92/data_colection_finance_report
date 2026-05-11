from __future__ import annotations

from business_logic.clients import ApiClient
from common.config.finance_api import Settings
from business_logic.repositories.posts import PostsRepository
from common.orm.schemas import PostsSyncRequest, SyncResponse
from loguru import logger
from sqlalchemy.orm import Session


class PostsService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.repository = PostsRepository(session)

    def sync(self, request: PostsSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        offset = 0
        errors: list[str] = []
        logger.info(
            "Posts sync started total={total} step={step} post_type={post_type}",
            total=request.total,
            step=request.step,
            post_type=request.post_type,
        )

        while fetched < request.total:
            limit = min(request.step, request.total - fetched)
            params = {
                "type": request.post_type,
                "offset": offset,
                "limit": limit,
                **request.params,
            }
            try:
                rows = self.client.get_json(self.settings.post_url or "", params=params)
            except Exception as exc:
                errors.append(str(exc))
                logger.exception(
                    "Posts sync batch failed offset={offset} limit={limit}",
                    offset=offset,
                    limit=limit,
                )
                break

            if not rows:
                logger.info(
                    "Posts sync stopped because API returned no rows offset={offset}",
                    offset=offset,
                )
                break

            saved += self.repository.save_posts(rows)
            fetched += len(rows)
            offset += len(rows)
            logger.info(
                "Posts sync batch saved rows={rows} fetched={fetched} saved={saved}",
                rows=len(rows),
                fetched=fetched,
                saved=saved,
            )

            if len(rows) < limit:
                logger.info(
                    "Posts sync reached final page rows={rows} limit={limit}",
                    rows=len(rows),
                    limit=limit,
                )
                break

        logger.info(
            "Posts sync finished status={status} fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="posts",
            status="ok" if not errors else "error",
            fetched=fetched,
            saved=saved,
            errors=errors,
        )
