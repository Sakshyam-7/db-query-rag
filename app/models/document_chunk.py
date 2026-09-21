import enum
import hashlib
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, Enum as SAEnum, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base


class ChunkSourceType(str, enum.Enum):
    PROJECT = "project"
    TICKET = "ticket"
    DOCUMENT = "document"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    source_type: Mapped[ChunkSourceType] = mapped_column(
        SAEnum(ChunkSourceType, name="chunk_source_type")
    )
    
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), index=True
    )

    chunk_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict
    )

    chunk_index: Mapped[int] = mapped_column(default=0)

    content_hash: Mapped[str] = mapped_column(String(64))

    content: Mapped[str] = mapped_column(Text)

    # The `| None` automatically translates to nullable=True
    parent_content: Mapped[str | None] = mapped_column(Text)

    fts_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
    )

    embedding: Mapped[list[float]] = mapped_column(Vector(settings.EMBEDDING_DIM))

    # func.now() pushes timestamp generation directly to the Postgres engine
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_document_chunks_fts", "fts_vector", postgresql_using="gin"),
        Index("ix_source_lookup", "source_type", "source_id"),
        Index("ix_chunk_update_check", "source_id", "content_hash"),
    )

    @staticmethod
    def generate_hash(text: str) -> str:
        """Helper to hash content before insertion."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()