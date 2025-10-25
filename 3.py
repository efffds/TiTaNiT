import sqlite3

db = r"D:\Hack RND\titanit.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

# Дефолтные фиктивные значения для обязательных полей
new_profiles = [
    {"user_id": 9991, "name": "Temp1", "interests": "hacking, reverse engineering"},
    {"user_id": 9992, "name": "Temp2", "interests": "AI research, data science"},
    {"user_id": 9993, "name": "Temp3", "interests": "dark humor, coffee, sleep deprivation"}
]

for p in new_profiles:
    cur.execute(
        "INSERT INTO profiles (user_id, name, interests) VALUES (?, ?, ?)",
        (p["user_id"], p["name"], p["interests"])
    )

conn.commit()
conn.close()
print("Добавлено 3 строки с обязательными полями в таблицу profiles.")
