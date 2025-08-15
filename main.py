from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3, random, string, os
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

# SQLite database setup
conn = sqlite3.connect('linkdrop.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT NOT NULL,
    link_code TEXT NOT NULL UNIQUE,
    description TEXT
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_code TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip TEXT
)
''')
conn.commit()

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("frontend.html", {"request": request, "message": ""})

@app.post("/create", response_class=HTMLResponse)
def create_link(request: Request, url: str = Form(...), desc: str = Form("")):
    code = generate_code()
    c.execute("INSERT INTO links (original_url, link_code, description) VALUES (?, ?, ?)", (url, code, desc))
    conn.commit()
    message = f"Your LinkDrop link: <a href='/l/{code}' target='_blank'>/l/{code}</a>"
    return templates.TemplateResponse("frontend.html", {"request": request, "message": message})

@app.get("/l/{code}")
def redirect_link(code: str, request: Request):
    c.execute("SELECT original_url FROM links WHERE link_code=?", (code,))
    row = c.fetchone()
    if row:
        c.execute("INSERT INTO clicks (link_code, user_agent, ip) VALUES (?, ?, ?)", 
                  (code, str(request.headers.get('user-agent')), request.client.host))
        conn.commit()
        return RedirectResponse(row[0])
    return "Link not found"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
