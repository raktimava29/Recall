import os
import uuid
import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Recall", page_icon="🧠", layout="centered")
st.title("🧠 Recall")
st.caption("Fast answers. Live web evidence. Memory that remembers when.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Conversation")
    st.caption(f"Session: {st.session_state.session_id[:8]}")
    if st.button("New conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("One external tool: web search")
    st.caption("Persistent memory: SQLite")

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item.get("sources"):
            with st.expander("Sources"):
                for index, source in enumerate(item["sources"], 1):
                    st.markdown(f"[{index}. {source['title']}]({source['url']})")
        if item.get("created_at"):
            st.caption(item["created_at"])

prompt = st.chat_input("Ask something, or ask Recall what you said earlier…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                response = httpx.post(
                    f"{API_BASE}/chat",
                    json={"session_id": st.session_state.session_id, "message": prompt},
                    timeout=90,
                )
                response.raise_for_status()
                data = response.json()
                st.markdown(data["answer"])
                if data.get("sources"):
                    with st.expander("Sources"):
                        for index, source in enumerate(data["sources"], 1):
                            st.markdown(f"[{index}. {source['title']}]({source['url']})")
                st.caption(("Web search used · " if data.get("search_used") else "Memory / knowledge · ") + data["created_at"])
                st.session_state.messages.append({
                    "role": "assistant", "content": data["answer"],
                    "sources": data.get("sources", []), "created_at": data.get("created_at"),
                })
            except httpx.HTTPError as exc:
                st.error(f"Could not reach Recall API: {exc}")
