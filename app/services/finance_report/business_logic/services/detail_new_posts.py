from __future__ import annotations

from business_logic.clients import ApiClient
from business_logic.repositories.detail_new_posts import DetailNewPostsRepository
from common.config.finance_api import Settings
from common.orm.schemas import DetailNewPostsSyncRequest, SyncResponse
from loguru import logger
from sqlalchemy.orm import Session


class DetailNewPostsService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.repository = DetailNewPostsRepository(session)

    def sync(self, request: DetailNewPostsSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        errors: list[str] = []

        targets = self.repository.fetch_targets(
            limit=request.limit,
            menu_name=request.menu_name,
            only_missing_detail=request.only_missing_detail,
        )

        for new_post_content_id, post_id in targets:
            url = f"{request.detail_base_url.rstrip('/')}/{post_id}"
            try:
                row = self.client.get_json(url)
                fetched += 1
                if isinstance(row, dict):
                    self.repository.upsert_detail(
                        new_post_content_id=new_post_content_id,
                        fireant_post_id=post_id,
                        detail_row=row,
                    )
                    saved += 1
                else:
                    errors.append(f"unexpected response type for post_id={post_id}")
            except Exception as exc:
                errors.append(f"post_id={post_id}: {exc}")
                logger.exception(
                    "detail_new_posts sync failed post_id={post_id}",
                    post_id=post_id,
                )

        return SyncResponse(
            service="detail_new_posts",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={
                "limit": request.limit,
                "menu_name": request.menu_name,
                "only_missing_detail": request.only_missing_detail,
            },
        )
