# Recall — Fast, Web-Grounded Chat Agent

Recall combines fast conversational answers, evidence-backed web research, and timestamp-aware memory.

## Features
- OpenAI-compatible chat model with exactly one external agent tool: web search.
- Tavily search, invoked only for current, obscure, uncertain, or explicitly requested web facts.
- Inline numbered citations and clickable source links.
- SQLite persistence for every user and assistant message, with UTC and local timestamps.
- Bounded recent context plus keyword retrieval of older messages.
- FastAPI backend, Streamlit UI, and memory tests.

SQLite is internal application storage, not an agent tool. The only external tool callable by the model is web_search.

## Architecture
Streamlit UI → FastAPI → SQLite memory + context retrieval → LLM agent → optional single web_search call → cited answer.

See design.md for architecture, memory policy, latency choices, and trade-offs.

## Setup
1. Python 3.11+
2. Create and activate a virtual environment.
3. Install dependencies: pip install -r requirements.txt
4. Copy .env.example to .env and add OPENAI_API_KEY and TAVILY_API_KEY.
5. Start API: uvicorn app.main:app --reload
6. Start UI in another terminal: streamlit run ui.py
7. Tests: pytest -q

API docs: http://127.0.0.1:8000/docs

## Environment
- OPENAI_API_KEY: required model provider key.
- OPENAI_BASE_URL: optional OpenAI-compatible endpoint.
- OPENAI_MODEL: defaults to gpt-4o-mini.
- TAVILY_API_KEY: required web search key.
- DATABASE_PATH: defaults to ./data/recall.db.
- API_BASE_URL: UI backend URL, defaults to localhost.
- MAX_CONTEXT_MESSAGES: defaults to 10.
- SEARCH_TIMEOUT_SECONDS: defaults to 8.
- LOCAL_TIMEZONE: defaults to UTC; example Asia/Kolkata.

Get a Tavily key at https://tavily.com/.

## API
POST /chat accepts:
{"session_id":"optional-session-id","message":"What did I ask yesterday?"}

GET /health — health check.
GET /sessions — recent sessions.
GET /sessions/{session_id}/messages — session history.

## Privacy
Conversation data stays in local SQLite. Never commit .env or database files. This demo has no authentication; add authentication and per-user isolation before public deployment.

## Project structure
app/agent.py, app/config.py, app/main.py, app/memory.py, app/search.py
tests/test_memory.py
design.md, ui.py, requirements.txt, .env.example

## License
MIT
