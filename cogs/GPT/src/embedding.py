import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

class EmbeddingModel:
    def __init__(self, model_name="intfloat/multilingual-e5-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)

    def average_pool(self, last_hidden_states, attention_mask):
        last_hidden = last_hidden_states.masked_fill(
            ~attention_mask[..., None].bool(), 0.0
        )
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
            emb = self.average_pool(
                outputs.last_hidden_state,
                batch["attention_mask"]
            )
            emb = F.normalize(emb, p=2, dim=1)

        return emb.cpu().numpy()