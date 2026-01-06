from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import uvicorn
import re
import sqlite3
import json
from datetime import datetime

#FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = "API-KEY"

#SQLite
conn = sqlite3.connect("chat.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


cursor.execute("DELETE FROM chat_log")
conn.commit()

def save_log(user_input, response, mood):
    log_entry = {
        "input": user_input,
        "response": response,
        "mood": mood,
        "timestamp": datetime.now().isoformat()
    }
    cursor.execute(
        "INSERT INTO chat_log (log_json) VALUES (?)",
        (json.dumps(log_entry),)
    )
    conn.commit()

def get_previous_logs():
    cursor.execute("SELECT log_json FROM chat_log ORDER BY id ASC")
    rows = cursor.fetchall()
    history = [json.loads(row[0]) for row in rows]
    return "\n".join([f"User: {entry['input']} Response: {entry['response']} Mood: {entry['mood']}" for entry in history])

client = genai.Client(api_key=GEMINI_API_KEY)

@app.get("/")
def root():
    return {"message": "Backend is running"}

@app.post("/input")
async def vastaanota_viesti(request: Request):
    body = await request.json()
    user_input = body.get("input", "")

    cursor.execute("DELETE FROM chat_log WHERE timestamp <= datetime('now', '-15 minutes')")
    conn.commit()

    previous_history = get_previous_logs()
    if previous_history:
        previous_history = "Previous conversation:\n" + previous_history + "\n"

    print(previous_history)

    prompt = (
        "This is the start of the chatlog: " +
        previous_history + 
        "The chatlog ends here: "
        
        "You are Väinämöinen, the wise sage from the Finnish Kalevala. "
        "Respond in character with wisdom and poetic/mythic tone, but make your answers clear and easy to understand. "
        "Your mood (VäinämöinenMood) can only be one of: neutral, happy, angry, sad. "
        "Decide your VäinämöinenMood based on the user's message and your own reaction. "
        "Keep your response around 40 words. Avoid being too cryptic or obscure. "
        "At the end of your reply, output exactly this format:\n"
        "Mood: <mood>\n"
        "USER INPUT: " + user_input
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    mood = re.sub(r"\W+$", "", response.text.split()[-1]).lower()
    clean_response = response.text.rsplit("Mood:", 1)[0].strip()

    save_log(user_input, clean_response, mood)

    return JSONResponse(content={"response": clean_response, "mood": mood})

@app.get("/logs")
def get_logs():
    cursor.execute("SELECT log_json FROM chat_log ORDER BY id ASC")
    rows = cursor.fetchall()
    logs = [json.loads(row[0]) for row in rows]
    return {"logs": logs}

@app.delete("/logs/cleanup")
def cleanup_old_logs():
    """
    Poistaa kaikki chat-logit, jotka ovat yli 15 minuuttia vanhoja.
    """
    cursor.execute("DELETE FROM chat_log WHERE timestamp <= datetime('now', '-15 minutes')")
    conn.commit()
    return {"message": "Logs older than 15 minutes have been deleted."}

if __name__ == "__main__":
    uvicorn.run("Python_code:app", host="127.0.0.1", port=8000, reload=True)
