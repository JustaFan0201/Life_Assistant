import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
import faiss
import numpy as np
from database.db import SessionLocal
from database.models import Memory


class MemoryManager:
    def __init__(self, model_name='intfloat/multilingual-e5-base'):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)

        self.dimension = 768  # base=768, large=1024
        self.index = faiss.IndexFlatIP(self.dimension)

        self.memories = []  # 存 text

    # ===== embedding =====
    def average_pool(self, last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def embed(self, texts):
        batch = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**batch)
            embeddings = self.average_pool(outputs.last_hidden_state, batch['attention_mask'])
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy()

    # ===== 新增記憶 =====
    def add_memory(self, text):
        with SessionLocal() as db:
            memory = Memory(
                user_id=user_id,
                message_text=message_text,
                vector=vec.tolist(),
                metadata=metadata
            )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        vec = self.embed([f"passage: {text}"])
        self.index.add(vec)
        self.memories.append(text)

    # ===== 搜尋記憶 =====
    def search(self, query, k=3):
        if len(self.memories) == 0:
            return []

        qvec = self.embed([f"query: {query}"])
        D, I = self.index.search(qvec, k)

        results = []
        for idx in I[0]:
            if idx < len(self.memories):
                results.append(self.memories[idx])

        return results

    # ===== 主流程（給 Discord 用）=====
    def process_message(self, message_text, k=3):
        # 1. 找相關記憶
        related = self.search(message_text, k=k)

        # 2. 存這句話
        self.add_memory(message_text)

        return related