# run_ml_with_db_sqlite.py

import sqlite3
import torch
from transformers import AutoTokenizer, AutoModel, MarianMTModel, MarianTokenizer
import torch.nn as nn
import numpy as np
import asyncio

# --- Модель для эмбеддингов (TextEncoder) ---
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

# --- Модель перевода RU -> EN ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Глобальные переменные для модели перевода
trans_model = None
trans_tokenizer = None

def initialize_translation_model():
    """Инициализирует модель перевода при первом вызове (ленивая инициализация)."""
    global trans_model, trans_tokenizer
    if trans_model is None or trans_tokenizer is None:
        print("Initializing translation model...")
        trans_model_name = "Helsinki-NLP/opus-mt-ru-en"
        trans_tokenizer = MarianTokenizer.from_pretrained(trans_model_name)
        trans_model = MarianMTModel.from_pretrained(trans_model_name, use_safetensors=True).to(device)
        print("Translation model initialized.")

def translate_to_en(text: str):
    """Переводит русский текст на английский"""
    if not text:
        return ""
    initialize_translation_model() # Инициализировать модель при первом использовании
    inputs = trans_tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)
    translated = trans_model.generate(**inputs)
    return trans_tokenizer.decode(translated[0], skip_special_tokens=True)

# --- Веса для каждого признака ---
WEIGHTS = {
    "interests": 0.25,
    "skills": 0.25,
    "goals": 0.20,
    "bio": 0.15,
    "city": 0.10,
    "age": 0.05
}

# --- Утилиты ---
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-MiniLM-L12-v2")
text_enc = TextEncoder("sentence-transformers/paraphrase-MiniLM-L12-v2").to(device)
text_enc.eval()

def encode_texts(ru_texts):
    """
    Кодирует список русских текстов в эмбеддинги.
    Сначала переводит каждый текст на английский, затем кодирует.
    """
    if not any(ru_texts): # Если все тексты пустые
        return torch.zeros(len(ru_texts), text_enc.proj.out_features).to(device)

    # Переводим все тексты на английский
    en_texts = [translate_to_en(text) for text in ru_texts]

    # Кодируем английские тексты
    encoded_inputs = tokenizer(
        en_texts, truncation=True, padding=True, max_length=512, return_tensors="pt"
    ).to(device)
    with torch.no_grad():
        embeddings = text_enc(input_ids=encoded_inputs["input_ids"], attention_mask=encoded_inputs["attention_mask"])
    return embeddings

def calculate_similarity_for_feature(feature_texts_1, feature_texts_2):
    """Вычисляет косинусное сходство между двумя наборами текстов для одного признака."""
    emb1 = encode_texts(feature_texts_1)
    emb2 = encode_texts(feature_texts_2)
    similarities = torch.matmul(emb1, emb2.t()).cpu().numpy()
    return similarities

def calculate_similarity_for_city(city1, city2):
    """Вычисляет сходство для признака city (1/0)."""
    return 1.0 if city1 and city2 and city1 == city2 else 0.0

def calculate_similarity_for_age(age1, age2):
    """Вычисляет сходство для признака age (1/(1+разница))."""
    if age1 is None or age2 is None:
        return 0.0
    # Проверяем, что значения числовые
    try:
        age1 = int(age1)
        age2 = int(age2)
    except (ValueError, TypeError):
        return 0.0
    age_diff = abs(age1 - age2)
    return 1 / (1 + age_diff)

# --- Функция для вычисления совместимости между двумя профилями ---
def calculate_compatibility_score(profile1, profile2):
    """
    Рассчитывает общий индекс совместимости между двумя профилями.

    Args:
        profile1 (dict): Профиль пользователя 1 (ключи: bio, skills, interests, goals, city, age).
        profile2 (dict): Профиль пользователя 2 (ключи: bio, skills, interests, goals, city, age).

    Returns:
        float: Общий индекс совместимости.
    """
    total_score = 0.0

    # Сходство по текстовым признакам
    for feature in ["bio", "skills", "interests", "goals"]:
        text1 = profile1.get(feature, "")
        text2 = profile2.get(feature, "")
        if text1 and text2: # Проверяем, что оба текста не пустые
            sim_matrix = calculate_similarity_for_feature([text1], [text2])
            feature_sim = sim_matrix[0, 0] # Извлекаем значение сходства
        else:
            # Если один из текстов пустой, сходство по признаку = 0
            feature_sim = 0.0
        total_score += WEIGHTS[feature] * feature_sim

    # Сходство по не-текстовым признакам
    city_sim = calculate_similarity_for_city(profile1.get("city"), profile2.get("city"))
    total_score += WEIGHTS["city"] * city_sim

    age_sim = calculate_similarity_for_age(profile1.get("age"), profile2.get("age"))
    total_score += WEIGHTS["age"] * age_sim

    return total_score

# --- Функция для загрузки профилей из БД с помощью sqlite3 ---
def load_profiles_from_db_sqlite(db_path):
    """
    Загружает профили из таблицы profiles с помощью sqlite3.

    Args:
        db_path (str): Путь к файлу базы данных SQLite.

    Returns:
        A list of dictionaries representing profiles.
    """
    print("Fetching profiles from database using sqlite3...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Выполняем запрос
    cur.execute("SELECT user_id, bio, skills, interests, goals, city, age FROM profiles;")
    rows = cur.fetchall()

    profiles = []
    for r in rows:
        user_id, bio, skills, interests, goals, city, age = r
        # Предполагаем, что skills, interests, goals хранятся как строки
        profile_dict = {
            "user_id": user_id,
            "bio": bio or "",
            "skills": skills or "",
            "interests": interests or "",
            "goals": goals or "",
            "city": city or "",
            "age": age # age может быть None или int
        }
        profiles.append(profile_dict)

    conn.close()
    print(f"Loaded {len(profiles)} profiles from database.")
    return profiles

# --- Функция для вычисления матрицы совместимости ---
def calculate_compatibility_matrix_from_db_sqlite(db_path):
    """
    Загружает профили из БД с помощью sqlite3 и вычисляет матрицу совместимости.

    Args:
        db_path (str): Путь к файлу базы данных SQLite.

    Returns:
        A tuple containing:
        - A dictionary mapping user_id to its index in the matrix.
        - A numpy array representing the compatibility matrix.
    """
    profiles = load_profiles_from_db_sqlite(db_path)

    if not profiles:
        print("No profiles found in database.")
        return {}, np.array([])

    user_ids = [profile["user_id"] for profile in profiles]
    user_id_to_index = {uid: idx for idx, uid in enumerate(user_ids)}

    num_profiles = len(profiles)
    compatibility_matrix = np.zeros((num_profiles, num_profiles))

    print("Calculating compatibility matrix...")
    for i in range(num_profiles):
        for j in range(i, num_profiles): # Матрица симметрична
            if i == j:
                compatibility_matrix[i][j] = 1.0
            else:
                score = calculate_compatibility_score(profiles[i], profiles[j])
                compatibility_matrix[i][j] = score
                compatibility_matrix[j][i] = score # Симметрия

    print(f"Compatibility matrix shape: {compatibility_matrix.shape}")
    return user_id_to_index, compatibility_matrix

# --- Функция для поиска совпадений ---
def find_matches(matrix: np.ndarray, user_id_to_index: dict, threshold: float = 0.7) -> dict:
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
def save_recommendations_to_match_sets(db_path, matches: dict):
    """
    Сохраняет данные рекомендаций в таблицу match_sets.
    Если для пользователя уже есть запись — обновляет matched_user_ids.
    """
    print("Saving recommendations into match_sets table...")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Создаём таблицу, если её ещё нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS match_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            matched_user_ids TEXT,  -- JSON-строка, например "[1,5,10]"
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        );
    """)

    for user_id, matched_ids in matches.items():
        matched_json = json.dumps(matched_ids) if matched_ids else "[]"

        # Проверяем, есть ли уже запись
        cur.execute("SELECT id FROM match_sets WHERE user_id = ?;", (user_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE match_sets
                SET matched_user_ids = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?;
            """, (matched_json, user_id))
        else:
            cur.execute("""
                INSERT INTO match_sets (user_id, matched_user_ids)
                VALUES (?, ?);
            """, (user_id, matched_json))

    conn.commit()
    conn.close()
    print("✅ Match sets successfully saved to database.")
# --- Пример использования ---
def main():
    """
    Пример: Загрузить профили из БД, вычислить матрицу, найти совпадения.
    """
    # Путь к базе данных
    db_path = r"D:\VSCodeProjects\hackaton\hackaton\titanit.db"

    user_id_to_index, matrix = calculate_compatibility_matrix_from_db_sqlite(db_path)

    if matrix.size == 0:
        print("No profiles to process.")
        return

    print("Compatibility Matrix:")
    print(matrix)

    # Найти совпадения
    matches = find_matches(matrix, user_id_to_index, threshold=0.1) # Понизим порог для демонстрации

    print("\nMatches found:")
    for user_id, matched_ids in matches.items():
        if matched_ids: # Печатаем только если есть совпадения
            print(f"User {user_id} matched with: {matched_ids}")
            # Опционально: вывести проценты совместимости
            idx = user_id_to_index[user_id]
            for matched_id in matched_ids:
                 m_idx = user_id_to_index[matched_id]
                 print(f"  -> User {matched_id}: {matrix[idx][m_idx]:.4f}")

    save_recommendations_to_match_sets(db_path, matches)
#
if __name__ == "__main__":
    # Запускаем основную функцию (асинхронность не нужна, так как используем sqlite3)
    main()
