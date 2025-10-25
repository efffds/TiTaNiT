import torch
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Profile # Импортируем модель Profile из вашего пакета
import pickle
import numpy as np # Для удобной работы с матрицами
from typing import Dict, List, Tuple
import asyncio

# --- Модель (скопирована из файла коллеги) ---
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

# --- Утилиты для работы с текстом ---
def combine_profile_fields(profile: Profile) -> str:
    """Объединяет текстовые поля профиля в одну строку для обработки моделью."""
    parts = []
    if profile.bio:
        parts.append(profile.bio)
    if profile.skills:
        parts.append(" ".join(profile.skills))
    if profile.interests:
        parts.append(" ".join(profile.interests))
    # Добавьте другие текстовые поля, если нужно (goals, name, city?)
    return " ".join(parts)

# --- Функция для вычисления совместимости ---
async def calculate_compatibility_matrix(db_session: AsyncSession) -> Tuple[Dict[int, int], np.ndarray]:
    """
    Извлекает профили из БД, вычисляет матрицу совместимости.

    Returns:
        A tuple containing:
        - A dictionary mapping user_id to its index in the matrix.
        - A numpy array representing the compatibility matrix.
    """
    print("Fetching profiles from database...")
    # Получаем все профили
    result = await db_session.execute(select(Profile))
    profiles = result.scalars().all()

    if not profiles:
        print("No profiles found in database.")
        return {}, np.array([])

    user_ids = [profile.user_id for profile in profiles]
    user_id_to_index = {uid: idx for idx, uid in enumerate(user_ids)}

    # Подготовим тексты
    texts = [combine_profile_fields(profile) for profile in profiles]

    print(f"Processing {len(texts)} profiles...")

    # --- Загрузка модели (лучше загружать один раз при старте приложения) ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-MiniLM-L12-v2")
    text_enc = TextEncoder("sentence-transformers/paraphrase-MiniLM-L12-v2").to(device)
    text_enc.eval()

    # --- Векторизация текстов ---
    print("Encoding texts...")
    encoded_inputs = tokenizer(
        texts, truncation=True, padding=True, max_length=512, return_tensors="pt"
    ).to(device) # Увеличил max_length

    with torch.no_grad():
        embeddings = text_enc(input_ids=encoded_inputs["input_ids"], attention_mask=encoded_inputs["attention_mask"])

    # --- Вычисление матрицы совместимости (косинусное сходство) ---
    print("Calculating compatibility matrix...")
    similarity_matrix = torch.matmul(embeddings, embeddings.t()).cpu().numpy()

    print(f"Compatibility matrix shape: {similarity_matrix.shape}")
    return user_id_to_index, similarity_matrix

# --- Функция для сохранения матрицы ---
def save_compatibility_matrix(user_id_to_index: Dict[int, int], matrix: np.ndarray, filename: str = "compatibility_matrix.pkl"):
    """Сохраняет матрицу совместимости и сопоставление ID в файл."""
    data_to_save = {
        'user_id_to_index': user_id_to_index,
        'matrix': matrix
    }
    with open(filename, 'wb') as f:
        pickle.dump(data_to_save, f)
    print(f"Compatibility matrix saved to {filename}")

# --- Функция для загрузки матрицы ---
def load_compatibility_matrix(filename: str = "compatibility_matrix.pkl") -> Tuple[Dict[int, int], np.ndarray]:
    """Загружает матрицу совместимости и сопоставление ID из файла."""
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    return data['user_id_to_index'], data['matrix']

# --- Функция для поиска совпадений ---
def find_matches(matrix: np.ndarray, user_id_to_index: Dict[int, int], threshold: float = 0.7) -> Dict[int, List[int]]:
    """
    Находит пользователей с совместимостью выше порога для каждого пользователя.

    Returns:
        A dictionary mapping user_id to a list of matched user_ids.
    """
    print(f"Finding matches with threshold {threshold}...")
    matches = {}
    for user_id, idx in user_id_to_index.items():
        # Получаем строку матрицы для текущего пользователя
        compatibility_scores = matrix[idx]
        # Находим индексы, где совместимость > threshold и не является самим собой (idx != idx)
        matched_indices = np.where((compatibility_scores > threshold) & (np.arange(len(compatibility_scores)) != idx))[0]
        # Преобразуем индексы обратно в user_id
        matched_user_ids = [list(user_id_to_index.keys())[i] for i in matched_indices]
        matches[user_id] = matched_user_ids

    print(f"Found matches for {len(matches)} users.")
    return matches

# --- Модель для таблицы совпадений (добавить в models.py) ---
# from sqlalchemy import Column, Integer, JSON # Уже импортировано где-то
# from .db import Base # Уже импортировано где-то

# class Match(Base):
#     __tablename__ = "matches"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, nullable=False, index=True)
#     matched_user_ids = Column(JSON) # Массив ID совпавших пользователей

# --- Функция для сохранения совпадений в БД ---
async def save_matches_to_db(db_session: AsyncSession, matches: Dict[int, List[int]]):
    """Сохраняет словарь совпадений в таблицу `match_sets`."""
    from sqlalchemy.dialects.sqlite import insert # Используем upsert для SQLite
    from .models import MatchSet # Импортируем модель MatchSet (бывший Match для набора совпадений)

    print("Saving matches to database...")
    for user_id, matched_ids in matches.items():
        # Для SQLite используем INSERT ... ON CONFLICT (upsert)
        stmt = insert(MatchSet).values(user_id=user_id, matched_user_ids=matched_ids)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=dict(matched_user_ids=stmt.excluded.matched_user_ids)
        )
        await db_session.execute(stmt)

    await db_session.commit()
    print("Matches saved successfully.")

# --- Основная функция для запуска процесса ---
async def run_ml_pipeline(db_session: AsyncSession):
    """
    Основная функция: загружает профили, вычисляет матрицу, находит совпадения, сохраняет в БД.
    """
    # 1. Вычислить матрицу
    user_id_to_index, matrix = await calculate_compatibility_matrix(db_session)

    if matrix.size == 0:
        print("No profiles to process, exiting pipeline.")
        return

    # 2. Сохранить матрицу (опционально)
    save_compatibility_matrix(user_id_to_index, matrix)

    # 3. Найти совпадения
    matches = find_matches(matrix, user_id_to_index, threshold=0.7)

    # 4. Сохранить совпадения в БД
    await save_matches_to_db(db_session, matches)

# --- Пример использования (запускать внутри асинхронной функции, например, в lifespan или отдельной задаче) ---
# async def example():
#     # Предполагается, что у вас есть асинхронная сессия db
#     # async with get_async_session() as session:
#     #     await run_ml_pipeline(session)

if __name__ == "__main__":
    # Этот блок не будет работать напрямую, так как требует асинхронной сессии БД.
    # Его нужно вызывать внутри асинхронной среды FastAPI.
    print("This script should be run within the FastAPI application context.")
    # asyncio.run(example()) # Пример, если бы была функция example с сессией
