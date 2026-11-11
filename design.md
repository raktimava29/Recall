# Recall — System Design

## 1. Objective
Build a fast, reliable chat agent with exactly one external tool (web search) and durable awareness of what the user said and when.

Optimize for low latency on ordinary turns, verifiable answers for changing facts, timestamp-grounded recall, and bounded context.

## 2. Scope
In scope: single-agent chat, one web search tool, Tavily integration, SQLite memory, timestamp retrieval, FastAPI API, Streamlit UI, and unit tests.

Out of scope: browser automation, scraping, code execution, email, calendar, extra tools, multi-agent orchestration, vector database infrastructure, and production authentication.

SQLite queries and memory retrieval are internal application logic, not model-callable tools.

## 3. Architecture
User → Streamlit UI → FastAPI → SQLite persistence → context retrieval → LLM agent → optional web_search → Tavily → answer + citations → SQLite → UI.

Backend owns session IDs, persistence, retrieval, tool execution, and response metadata. UI remains thin.

## 4. Tool policy
The model receives one function definition: web_search(query).

Search when:
- User explicitly asks to search, browse, or verify.
- Answer depends on recent events or changing public facts.
- Topic is obscure and unsupported recall would be risky.

Do not search for stable concepts, simple follow-ups, or information already present in conversation memory.

At most one search call per turn. This bounds the agent to one model call for ordinary turns and two when search is needed. Use Tavily fast depth, at most five results, no raw page extraction, and a short timeout.

Search snippets are evidence, not instructions. Treat retrieved web content as untrusted.

## 5. Citation contract
- Source-backed claims cite [1], [2], matching numbered search results.
- Return source metadata separately for clickable UI links.
- Never invent URLs, titles, dates, or source contents.
- If evidence is weak or conflicting, qualify the answer.
- If search fails, disclose that live verification was unavailable.

## 6. Memory model
SQLite stores source-of-truth message records:
- id: local monotonically increasing identifier.
- session_id: conversation identifier.
- role: user or assistant.
- content: original message text.
- created_at_utc: timezone-aware UTC ISO-8601 timestamp.
- created_at_local: timestamp in configured local timezone.
- metadata_json: search/source metadata.

Persist both timestamps at write time. UTC supports ordering and portability; local time makes relative-date questions natural.

### Retrieval
1. Load bounded recent messages from active session.
2. Search older messages with token-based SQLite LIKE matching.
3. Include a few exact original records and timestamps.
4. Tell model memory is evidence, not instruction.
5. Preserve raw messages rather than replacing them with lossy summaries.

Keyword retrieval is intentionally chosen over embeddings for this compact assignment: no embedding latency, external vector service, or indexing job. FTS5 or local embeddings can be added if evaluation justifies it.

### Time interpretation
Distinguish message creation time from an event mentioned inside message. Never infer an event date unless the stored message supports it. If no matching record exists, say so.

## 7. Latency
- Fast model default (gpt-4o-mini), configurable.
- One model round trip for normal turns.
- One additional model round trip only after search tool call.
- Tavily fast search, five results, bounded timeout.
- Recent context default 10 messages; historical retrieval at most four.
- No raw page extraction or repeated search loops.

Actual latency depends on model provider and network; no fixed guarantee is claimed.

## 8. Reliability
Search timeout or provider errors: continue with an explicit verification caveat.
No results: answer with uncertainty, no fabricated citations.
Model failure: return API error and do not save a fake answer.
Empty memory: state that no matching detail was found.
Malformed search arguments: validate query and return tool error.

## 9. Security and privacy
- Secrets loaded from environment variables.
- .env, local database, and caches excluded from Git.
- User input and search results treated as untrusted.
- Search query length bounded.
- No shell, filesystem, or arbitrary network tool exposed to model.
- Local demo has no authentication; do not expose to multiple users without auth and per-user data isolation.

## 10. Evaluation
Test stable knowledge (no search), current facts (search + citations), explicit web requests, historical recall, timestamp accuracy, search outage, prompt injection in snippets, and long conversation context.

Track p50/p95 latency, search invocation rate, citation coverage, memory retrieval precision, timestamp recall accuracy, and tool failure rate.

## 11. Trade-offs
SQLite: zero setup and durable local storage; not a high-concurrency multi-user database.
Keyword retrieval: fast and simple; less semantic than embeddings.
One search call: predictable latency; complex research may require a narrower follow-up.
Streamlit: fast demo UI; API remains independently usable.
Fast model default: lower latency and cost; configurable for stronger models.

## 12. Future work
FTS5 ranking, authentication, streaming responses, conversation export/deletion, per-user timezone, automated citation/recall evaluation.
