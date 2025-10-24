from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import aiofiles
import uvicorn
import os

APP_DIR = Path(__file__).parent
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Simple Upload (FastAPI)")

# Раздаём статические файлы (если нужно)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Upload demo</title>
  </head>
  <body>
    <h2>Загрузить файл</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
      <input type="file" name="file"/>
      <button type="submit">Загрузить</button>
    </form>

    <h3>Файлы в папке uploads</h3>
    <ul>
    {files}
    </ul>
  </body>
</html>
"""

def render_index():
    items = []
    for p in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.name):
        if p.is_file():
            url = f"/uploads/{p.name}"
            items.append(f'<li><a href="{url}" target="_blank">{p.name}</a> — {p.stat().st_size} bytes</li>')
    files_html = "\n".join(items) if items else "<li>(пусто)</li>"
    return INDEX_HTML.format(files=files_html)

@app.get("/", response_class=HTMLResponse)
async def index():
    return render_index()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # сохраняем безопасно (берём только имя файла)
    filename = Path(file.filename).name
    if not filename:
        raise HTTPException(status_code=400, detail="No filename")
    target = UPLOAD_DIR / filename

    try:
        async with aiofiles.open(target, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Cannot save file")

    return RedirectResponse("/", status_code=303)

# (опционально) прямой скач/просмотр файлов handled by StaticFiles mounted above

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
