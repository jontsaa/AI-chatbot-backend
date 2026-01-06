This is a FastAPI-based backend for a chatbot that responds as Väinämöinen, the wise sage from the Finnish Kalevala. The bot uses Google's Gemini AI to generate responses and tracks mood for each message. Chat history is stored in a local SQLite database and automatically prunes entries older than 15 minutes.

Features

- FastAPI backend with CORS enabled for local frontend development.
- Gemini AI integration for generating character-driven responses.
- SQLite-based chat history logging with automatic cleanup of old logs.
- Mood detection (`neutral`, `happy`, `angry`, `sad`) for each bot response.
- Endpoints:
  - `GET /` – check backend status.
  - `POST /input` – send user message and receive Väinämöinen's response.
  - `GET /logs` – retrieve all chat logs.
  - `DELETE /logs/cleanup` – remove logs older than 15 minutes.
