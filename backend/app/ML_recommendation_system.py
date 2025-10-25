import torch
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn

# ----------------- Модель -----------------
class TextEncoder(nn.Module):
    def __init__(self, model_name="sentence-transformers/paraphrase-MiniLM-L12-v2", out_dim=384):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden = self.backbone.config.hidden_size
        self.proj = nn.Linear(hidden, out_dim)
        nn.init.normal_(self.proj.weight, std=0.02)

    def forward(self, input_ids, attention_mask):
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        last = out.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(last.size()).float()
        summed = torch.sum(last * mask, dim=1)
        lengths = torch.clamp(mask.sum(dim=1), min=1e-9)
        mean_pooled = summed / lengths
        emb = self.proj(mean_pooled)
        emb = nn.functional.normalize(emb, p=2, dim=1)
        return emb

# ----------------- Setup -----------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-MiniLM-L12-v2")
text_enc = TextEncoder("sentence-transformers/paraphrase-MiniLM-L12-v2").to(device)
text_enc.eval()

# ----------------- Функция similarity -----------------
def text_similarity(text1: str, text2: str):
    encoded1 = tokenizer(text1, truncation=True, padding="max_length", max_length=128, return_tensors="pt").to(device)
    encoded2 = tokenizer(text2, truncation=True, padding="max_length", max_length=128, return_tensors="pt").to(device)
    with torch.no_grad():
        emb1 = text_enc(input_ids=encoded1["input_ids"], attention_mask=encoded1["attention_mask"])
        emb2 = text_enc(input_ids=encoded2["input_ids"], attention_mask=encoded2["attention_mask"])
        sim = torch.matmul(emb1, emb2.t()).item()
    return sim

# ----------------- Примеры -----------------
profiles = [
    "I love reading books and going for walks in nature.",
    "Reading books and hiking are my favorite activities.",
    "I hate reading books and prefer watching TV shows.",
    "Sports and outdoor activities are my passion.",
    "I love cooking and experimenting with recipes.",
    "I enjoy cooking, especially new dishes."
]

# ----------------- Сравнение всех анкет -----------------
for i in range(len(profiles)):
    for j in range(i+1, len(profiles)):
        sim = text_similarity(profiles[i], profiles[j])
        print(f"Similarity between [{i}] and [{j}]: {sim:.4f}")
