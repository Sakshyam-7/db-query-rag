import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.llm.base import LLMProvider
from app.models.document_chunk import ChunkSourceType, DocumentChunk


async def sync_document_chunks(
    db: Session,
    source_type: ChunkSourceType,
    source_id: uuid.UUID,
    chunk_data: list[dict],
    embedder: LLMProvider,
) -> dict:
    """
    Syncs document chunks for a specific entity using content hashing.
    chunk_data format: [{"content": "...", "parent_content": "..."}, ...]
    """
    new_state = []
    for index, data in enumerate(chunk_data):
        content = data["content"]
        new_state.append({
            "chunk_index": index,
            "content": content,
            "parent_content": data.get("parent_content"),
            "content_hash": DocumentChunk.generate_hash(content),
        })

    new_hashes = {item["content_hash"] for item in new_state}

    stmt = select(DocumentChunk).where(
        DocumentChunk.source_type == source_type,
        DocumentChunk.source_id == source_id,
    )
    existing_chunks = db.execute(stmt).scalars().all()

    existing_hashes = {chunk.content_hash for chunk in existing_chunks}
    existing_chunk_map = {chunk.content_hash: chunk for chunk in existing_chunks}

    hashes_to_delete = existing_hashes - new_hashes
    hashes_to_add = new_hashes - existing_hashes
    hashes_to_keep = existing_hashes & new_hashes

    try:
        if hashes_to_delete:
            del_stmt = delete(DocumentChunk).where(
                DocumentChunk.source_type == source_type,
                DocumentChunk.source_id == source_id,
                DocumentChunk.content_hash.in_(hashes_to_delete),
            )
            db.execute(del_stmt)

        for item in new_state:
            if item["content_hash"] in hashes_to_keep:
                existing_chunk = existing_chunk_map[item["content_hash"]]
                if existing_chunk.chunk_index != item["chunk_index"]:
                    existing_chunk.chunk_index = item["chunk_index"]

        items_to_embed = [item for item in new_state if item["content_hash"] in hashes_to_add]

        if items_to_embed:
            texts_to_embed = [item["content"] for item in items_to_embed]
            embeddings = [await embedder.embed(text) for text in texts_to_embed]

            new_db_chunks = [
                DocumentChunk(
                    source_type=source_type,
                    source_id=source_id,
                    content=item["content"],
                    parent_content=item["parent_content"],
                    content_hash=item["content_hash"],
                    chunk_index=item["chunk_index"],
                    embedding=embedding,
                )
                for item, embedding in zip(items_to_embed, embeddings)
            ]
            db.add_all(new_db_chunks)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "deleted": len(hashes_to_delete),
        "kept_and_reordered": len(hashes_to_keep),
        "embedded_and_added": len(hashes_to_add),
    }