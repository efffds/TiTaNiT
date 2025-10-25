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
import json # Для десериализации JSON-полей из БД

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

# --- Веса для каждого признака ---
WEIGHTS = {
    "bio": 0.15,
    "skills": 0.25,
    "interests": 0.25,
    "goals": 0.2,
    "city": 0.10,
    "age": 0.05 # Важно: этот вес для *численного* расстояния по возрасту
}

# --- Функция для получения текста из поля (обрабатывает строки и списки строк) ---
def get_text_from_field(field_value):
    """Преобразует значение поля (строка или список строк) в одну строку."""
    if not field_value:
        return ""
    if isinstance(field_value, list):
        return " ".join(field_value)
    return field_value

# --- Функция для вычисления совместимости ---
# --- Функция для вычисления совместимости ---
async def calculate_compatibility_matrix(db_session: AsyncSession) -> Tuple[Dict[int, int], np.ndarray]:
    """
    Извлекает профили из БД, вычисляет матрицу совместимости на основе
    взвешенного суммирования сходства по отдельным признакам.
    
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

    # Подготовим списки данных для каждого признака
    bios = [profile.bio or "" for profile in profiles] # Если bio None, используем пустую строку
    # skills, interests, goals теперь просто строки, не нужно десериализовывать
    skills_texts = [profile.skills or "" for profile in profiles]
    interests_texts = [profile.interests or "" for profile in profiles]
    goals_texts = [profile.goals or "" for profile in profiles]

    cities = [profile.city or "" for profile in profiles]
    ages = [profile.age for profile in profiles] # Список чисел

    print(f"Processing {len(profiles)} profiles...")

    # --- Загрузка модели (лучше загружать один раз при старте приложения) ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-MiniLM-L12-v2")
    text_enc = TextEncoder("sentence-transformers/paraphrase-MiniLM-L12-v2").to(device)
    text_enc.eval()

    num_profiles = len(profiles)
    # Инициализируем матрицу сходства
    compatibility_matrix = np.zeros((num_profiles, num_profiles))

    # --- Векторизация текстов для каждого признака отдельно ---
    def encode_texts(texts):
        if not any(texts): # Если все тексты пустые
             return torch.zeros(len(texts), text_enc.proj.out_features).to(device)
        encoded_inputs = tokenizer(
            texts, truncation=True, padding=True, max_length=512, return_tensors="pt"
        ).to(device)
        with torch.no_grad():
            embeddings = text_enc(input_ids=encoded_inputs["input_ids"], attention_mask=encoded_inputs["attention_mask"])
        return embeddings

    print("Encoding 'bio'...")
    bio_embeddings = encode_texts(bios)
    print("Encoding 'skills'...")
    skills_embeddings = encode_texts(skills_texts)
    print("Encoding 'interests'...")
    interests_embeddings = encode_texts(interests_texts)
    print("Encoding 'goals'...")
    goals_embeddings = encode_texts(goals_texts)

    # --- Вычисление матрицы совместимости ---
    print("Calculating compatibility matrix...")
    for i in range(num_profiles):
        for j in range(i, num_profiles): # Матрица симметрична, можно вычислять только верхний треугольник
            if i == j:
                compatibility_matrix[i][j] = 1.0 # Совпадение с самим собой
                continue

            # Сходство по текстовым признакам (косинусное)
            bio_sim = torch.matmul(bio_embeddings[i].unsqueeze(0), bio_embeddings[j].unsqueeze(0).t()).cpu().numpy().item()
            skills_sim = torch.matmul(skills_embeddings[i].unsqueeze(0), skills_embeddings[j].unsqueeze(0).t()).cpu().numpy().item()
            interests_sim = torch.matmul(interests_embeddings[i].unsqueeze(0), interests_embeddings[j].unsqueeze(0).t()).cpu().numpy().item()
            goals_sim = torch.matmul(goals_embeddings[i].unsqueeze(0), goals_embeddings[j].unsqueeze(0).t()).cpu().numpy().item()

            # Сходство по не-текстовым признакам
            city_match = 1.0 if cities[i] and cities[j] and cities[i] == cities[j] else 0.0
            # Сходство по возрасту: уменьшается с увеличением разницы (например, 1 / (1 + разница))
            age_diff = abs(ages[i] - ages[j]) if ages[i] is not None and ages[j] is not None else float('inf')
            if age_diff == float('inf'):
                age_sim = 0.0
            else:
                age_sim = 1 / (1 + age_diff) # Простая функция схожести по возрасту

            # Взвешенная сумма
            total_similarity = (
                WEIGHTS["bio"] * bio_sim +
                WEIGHTS["skills"] * skills_sim +
                WEIGHTS["interests"] * interests_sim +
                WEIGHTS["goals"] * goals_sim +
                WEIGHTS["city"] * city_match +
                WEIGHTS["age"] * age_sim
            )

            # Нормализация (опционально, если веса уже в сумме дают 1.0)
            # total_similarity = total_similarity / sum(WEIGHTS.values())

            compatibility_matrix[i][j] = total_similarity
            compatibility_matrix[j][i] = total_similarity # Симметрия

    print(f"Compatibility matrix shape: {compatibility_matrix.shape}")
    return user_id_to_index, compatibility_matrix
# --- (Остальные функции остаются без изменений, если не используют combine_profile_fields) ---
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

# --- Функция для сохранения совпадений в БД ---
async def save_matches_to_db(db_session: AsyncSession, matches: Dict[int, List[int]]):
    """Сохраняет словарь совпадений в таблицу `matches`."""
    from sqlalchemy.dialects.sqlite import insert # Используем upsert для SQLite
    from .models import Match # Импортируем модель Match

    print("Saving matches to database...")
    for user_id, matched_ids in matches.items():
        # Для SQLite используем INSERT ... ON CONFLICT (upsert)
        stmt = insert(Match).values(user_id=user_id, matched_user_ids=matched_ids)
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
