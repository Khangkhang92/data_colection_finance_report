from __future__ import annotations

from business_logic.clients import ApiClient
from business_logic.repositories.new_posts_content import NewPostsContentRepository
from common.config.finance_api import Settings
from common.orm.schemas import NewPostsContentSyncRequest, SyncResponse
from loguru import logger
from sqlalchemy.orm import Session


class NewPostsContentService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.repository = NewPostsContentRepository(session)

    def sync(self, request: NewPostsContentSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        offset = 0
        errors: list[str] = []

        while fetched < request.total:
            limit = min(request.step, request.total - fetched)
            params = {"offset": offset, "limit": limit, **request.params}
            try:
                rows = self.client.get_json(request.url, params=params)
            except Exception as exc:
                errors.append(str(exc))
                logger.exception(
                    "new_posts_content sync batch failed menu={menu} offset={offset} limit={limit}",
                    menu=request.menu_name,
                    offset=offset,
                    limit=limit,
                )
                break

            if not isinstance(rows, list) or not rows:
                break

            saved += self.repository.save_rows(request.menu_name, rows)
            fetched += len(rows)
            offset += len(rows)

            if len(rows) < limit:
                break

        return SyncResponse(
            service="new_posts_content",
            status="ok" if not errors else "error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={"menu_name": request.menu_name, "url": request.url},
        )
