# upload_photo_example.py

import requests

# --- Настройки ---
# URL вашего бэкенда
BASE_URL = "http://127.0.0.1:8000"
# Эндпоинт для загрузки фото (см. routers/photos.py)
UPLOAD_PHOTO_ENDPOINT = "/profile/photos"
# Путь к вашему файлу изображения
IMAGE_FILE_PATH = r"C:/Users/Woonick/Pictures/ДГТУ.jpg" # !!! Замените на реальный путь !!!

# Ваш JWT токен (полученный после логина)
# Пример: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
YOUR_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzYxNDQ2MTA0fQ.tlNDIAjpHXxnt-BDY5IreuS0r4AT0sfXGz0W5wgHMBc" # !!! Замените на реальный токен !!!

# --- Формирование запроса ---
url = f"{BASE_URL}{UPLOAD_PHOTO_ENDPOINT}"

# Заголовки с токеном авторизации
headers = {
    "Authorization": f"Bearer {YOUR_JWT_TOKEN}"
}

# Файл для загрузки
# Ключ в словаре 'files' ('file') должен совпадать с именем параметра в FastAPI (file: UploadFile = File(...))
try:
    with open(IMAGE_FILE_PATH, 'rb') as image_file:
        files = {'file': image_file} # 'file' - имя поля файла в форме

        print(f"Uploading {IMAGE_FILE_PATH} to {url}...")
        # Отправка POST-запроса
        response = requests.post(url, headers=headers, files=files)

    # --- Обработка ответа ---
    if response.status_code == 200:
        try:
            data = response.json()
            print("✅ Photo uploaded successfully!")
            print(f"   Response data: {data}")
            # Пример вывода: {'id': 5, 'photo_path': 'uploads/abc123_image.jpg', 'message': 'Photo uploaded successfully'}
        except requests.exceptions.JSONDecodeError:
            print("⚠️  Received non-JSON response:")
            print(response.text)
    else:
        print(f"❌ Upload failed with status code {response.status_code}")
        print(f"   Response text: {response.text}")

except FileNotFoundError:
    print(f"❌ Error: File '{IMAGE_FILE_PATH}' not found.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
