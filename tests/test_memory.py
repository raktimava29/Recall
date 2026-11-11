from app.memory import MemoryStore


def test_message_has_utc_and_local_timestamps(tmp_path):
    store = MemoryStore(str(tmp_path / "test.db"), "Asia/Kolkata")
    saved = store.add_message("s1", "user", "My project deadline is Friday.")
    assert saved["created_at_utc"].endswith("+00:00")
    assert "+05:30" in saved["created_at_local"]
    assert saved["content"] == "My project deadline is Friday."


def test_recent_messages_are_chronological(tmp_path):
    store = MemoryStore(str(tmp_path / "test.db"))
    store.add_message("s1", "user", "First message")
    store.add_message("s1", "assistant", "First answer")
    store.add_message("s1", "user", "Second message")
    messages = store.recent_messages("s1", 2)
    assert [m["content"] for m in messages] == ["First answer", "Second message"]


def test_historical_memory_search_returns_original_record(tmp_path):
    store = MemoryStore(str(tmp_path / "test.db"))
    saved = store.add_message("s1", "user", "I chose PostgreSQL for the Recall project.")
    matches = store.search_memory("s1", "Which database did I choose for Recall?")
    assert matches
    assert matches[0]["id"] == saved["id"]
    assert "PostgreSQL" in matches[0]["content"]


def test_sessions_are_isolated(tmp_path):
    store = MemoryStore(str(tmp_path / "test.db"))
    store.add_message("a", "user", "Secret from session A")
    assert store.search_memory("b", "Secret session") == []
