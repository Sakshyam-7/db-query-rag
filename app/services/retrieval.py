from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Assuming you have a Ticket model with an owner_id
from app.models.ticket import Ticket 

async def retrieve_context(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    query_embedding: list[float], 
    limit: int = 5
) -> list[str]:
    
    # STEP 1: Fetch allowed source IDs via standard relational queries
    allowed_stmt = select(Ticket.id).where(Ticket.owner_id == user_id)
    allowed_result = await db.execute(allowed_stmt)
    allowed_ids = [row[0] for row in allowed_result.fetchall()]

    if not allowed_ids:
        return []

    # STEP 2: Vector search strictly within the allowed IDs (Maintains HNSW performance)
    vector_stmt = (
        select(DocumentChunk)
        .where(
            DocumentChunk.source_type == ChunkSourceType.TICKET,
            DocumentChunk.source_id.in_(allowed_ids)
        )
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    
    chunks = (await db.execute(vector_stmt)).scalars().all()
    
    # STEP 3: Re-order logically by index before returning
    ordered_chunks = sorted(chunks, key=lambda c: (c.source_id, c.chunk_index))
    
    # STEP 4: Return parent_content if it exists, otherwise fallback to content
    return [c.parent_content or c.content for c in ordered_chunks]