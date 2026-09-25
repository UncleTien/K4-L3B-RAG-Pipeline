"""Streamlit interaction checks; generation fixtures exist only in tests."""
from pathlib import Path
from unittest.mock import Mock
import pytest
from src import task10_generation as generation

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_top_k_and_history_are_snapshots(monkeypatch):
    output = {
        "answer": "Grounded answer.",
        "sources": [{
            "id": "chunk-a", "content": "Evidence", "score": 0.12,
            "metadata": {"title": "Original title", "source": "policy.md",
                         "url": "https://example.org/original"},
            "retrieval_method": "hybrid",
        }],
        "retrieval_source": "hybrid",
    }
    mock = Mock(return_value=output)
    monkeypatch.setattr(generation, "generate_with_citation", mock)
    app = AppTest.from_file(APP).run()
    app.slider[0].set_value(1).run()
    app.chat_input[0].set_value("  Question  ").run()
    assert not app.exception
    mock.assert_called_once_with("Question", top_k=1)
    message = app.session_state["messages"][-1]
    assert message["query"] == "Question"
    assert message["top_k"] == 1
    assert message["result"] == output
    output["sources"][0]["metadata"]["title"] = "Changed externally"
    app.slider[0].set_value(8).run()
    assert not app.exception
    assert any(item.value == "Original title" for item in app.text)
    assert app.session_state["messages"][-1]["top_k"] == 1
    mock.assert_called_once()


def test_whitespace_query_is_not_submitted(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(generation, "generate_with_citation", mock)
    app = AppTest.from_file(APP).run()
    app.chat_input[0].set_value("   ").run()
    assert not app.exception
    assert app.session_state["messages"] == []
    mock.assert_not_called()


def test_source_links_are_only_from_metadata(monkeypatch):
    output = {
        "answer": "Text mentioning https://invented.example/answer",
        "sources": [{
            "id": "real-id", "content": "Evidence", "score": 1.0,
            "metadata": {"url": "https://example.org/real"},
            "retrieval_method": "pageindex",
        }],
        "retrieval_source": "pageindex",
    }
    monkeypatch.setattr(generation, "generate_with_citation", Mock(return_value=output))
    app = AppTest.from_file(APP).run()
    app.chat_input[0].set_value("Question").run()
    assert not app.exception
    links = app.get("link_button")
    assert len(links) == 1
    assert links[0].proto.url == "https://example.org/real"
    assert any("Không có tiêu đề" in item.value for item in app.text)
    assert any("Không có thông tin nguồn" in item.value for item in app.text)
    assert any("pageindex" in item.value for item in app.caption)