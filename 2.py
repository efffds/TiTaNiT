import sqlite3

db = r"D:\VSCodeProjects\hackaton\hackaton\titanit.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT interests FROM profiles;")
rows = cur.fetchall()

for r in rows:
    print(r[0])

conn.close()
