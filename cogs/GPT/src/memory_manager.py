from database.models import Memory
from GPT.src.embedding import EmbeddingModel
from sqlalchemy import func
from database.db_utils import with_db_decorator

class MemoryManager:
    def __init__(self):
        self.embed_model = EmbeddingModel()

    @with_db_decorator
    def add_memory(self, db, user_id: int, text: str, metadata: dict = {}):

        vector = self.embed_model.embed(
            [f"passage: {text}"]
        )[0].tolist()

        mem = Memory(
            user_id=user_id,
            message_text=text,
            vector=vector,
            metadata=metadata
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)

        return mem.id

    @with_db_decorator
    def search_memory(self, db, user_id: int, query: str, k: int = 5):

        query_vec = self.embed_model.embed(
            [f"query: {query}"]
        )[0].tolist()

        results = (
            db.query(Memory)
            .order_by(Memory.vector.op("<=>")(query_vec))
            .limit(k)
            .all()
        )

        return [
            {
                "id": r.id,
                "text": r.message_text,
                "metadata": r.metadata
            }
            for r in results
        ]
    
    @with_db_decorator
    def get_recent_chat(self, db, user_id, limit=10):
        rows = (
            db.query(Memory)
            .order_by(Memory.created_at.desc())
            .limit(limit)
            .all()
        )

        rows.reverse()

        return [
            {"role": r.role, "content": r.content}
            for r in rows
        ]

    # 更新使用時間
    @with_db_decorator
    def touch(self, db, memory_id: int):
        mem = db.query(Memory).filter(Memory.id == memory_id).first()
        if mem:
            mem.last_used_at = func.now()
            db.commit()