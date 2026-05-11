from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)
    conversation_id: str = Field(default="default", min_length=1, max_length=128)
    user_id: str | None = Field(default=None, min_length=1, max_length=128)


class RagSource(BaseModel):
    chunk_id: int
    score: float
    content: str


class RagQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[RagSource]


class RagChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str = Field(default="default", min_length=1, max_length=128)
    user_id: str | None = Field(default=None, min_length=1, max_length=128)
    top_k: int = Field(default=3, ge=1, le=10)


class RagChatMessage(BaseModel):
    id: int
    conversation_id: str
    user_id: str | None = None
    role: str
    content: str
    sources: list[dict] | None = None
    metadata_json: dict | None = None
    created_at: str


class RagChatHistoryResponse(BaseModel):
    conversation_id: str
    messages: list[RagChatMessage]


class ChunkCheckRequest(BaseModel):
    table: str = Field(..., description="Supported table name except posts")
    filters: dict[str, str | int | float] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=200)
    keyword: str | None = None
    cursor: str | None = Field(default=None, description="Opaque cursor returned by previous page")


class ChunkCheckResponse(BaseModel):
    table: str
    count: int
    chunks: list[str]
    next_cursor: str | None = None
