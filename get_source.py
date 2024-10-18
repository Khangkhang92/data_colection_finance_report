from models import PostSource, PostGroup
from getdata.base import Base
from common.db import ScopedSession
import os


def post_source():
    POST_SOURCE = os.getenv("POST_SOURCE")
    base_call_api = Base(POST_SOURCE)
    list_source = base_call_api.fetch_posts()

    with ScopedSession() as session:
        for source in list_source:
            post_source_id = source["postSourceID"]
            existing_source = (
                session.query(PostSource)
                .filter_by(fireant_post_source_id=post_source_id)
                .first()
            )

            if existing_source:
                # Update existing record
                existing_source.name = source["name"]
                existing_source.url = source["url"]
                session.add(existing_source)
            else:
                # Create new record
                new_source = PostSource(
                    fireant_post_source_id=post_source_id,
                    name=source["name"],
                    url=source["url"],
                )
                session.add(new_source)

        session.commit()


def post_group():
    SOURCE_GROUP = os.getenv("SOURCE_GROUP")
    base_call_api = Base(SOURCE_GROUP)
    list_source = base_call_api.fetch_posts()

    with ScopedSession() as session:
        for source in list_source:
            post_group_id = source["postGroupID"]
            existing_group = (
                session.query(PostGroup)
                .filter_by(fireant_post_group_id=post_group_id)
                .first()
            )

            if existing_group:
                # Update existing record
                existing_group.name = source["name"]
                existing_group.description = source["description"]
                session.add(existing_group)
            else:
                # Create new record
                new_group = PostGroup(
                    fireant_post_group_id=post_group_id,
                    name=source["name"],
                    description=source["description"],
                )
                session.add(new_group)

        session.commit()


post_group()
