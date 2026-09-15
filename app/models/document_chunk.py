import enum
import hashlib
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, Enum as SAEnum, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base


class ChunkSourceType(str, enum.Enum):
    PROJECT = "project"
    TICKET = "ticket"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    source_type: Mapped[ChunkSourceType] = mapped_column(
        SAEnum(ChunkSourceType, name="chunk_source_type"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )

    chunk_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )

    # 1. Chunk Index for reassembling context logically before LLM injection
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 2. Content Hash for avoiding duplicate embedding costs on updates
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Target for vector embedding (e.g., 1-2 dense sentences)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 3. Small-to-Big Retrieval: Contains surrounding context to feed the LLM
    parent_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    fts_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
    )

    embedding: Mapped[list[float]] = mapped_column(Vector(settings.EMBEDDING_DIM))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
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
        # Composite index to quickly check if a specific chunk update is already embedded
        Index("ix_chunk_update_check", "source_id", "content_hash"),
    )

    @staticmethod
    def generate_hash(text: str) -> str:
        """Helper to hash content before insertion."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()