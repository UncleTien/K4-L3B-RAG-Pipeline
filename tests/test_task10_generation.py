"""Offline Task 10 tests: fixtures are evidence only inside tests."""

import copy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from src import task10_generation as generation
from src.contracts import validate_generation_result


def evidence(method="hybrid", count=5):
    return [{
        "id": f"legal/policy.md::chunk-{i}",
        "content": f"Evidence paragraph {i}.",
        "score": 1.0 - i / 10,
        "metadata": {
            "title": "Policy", "source": "legal/policy.md",
            "url": "https://example.org/policy", "doc_type": "legal",
            "chunk_index": i,
        },
        "retrieval_method": method,
    } for i in range(count)]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    # Unexpected calls fail; no test can reach the unfinished retrieval or APIs.
    monkeypatch.setattr(generation, "retrieve", Mock(side_effect=AssertionError("Unexpected retrieval")))
    monkeypatch.setattr(generation, "call_llm", Mock(side_effect=AssertionError("Unexpected LLM")))


def test_reorder_is_lossless_and_independent():
    chunks = evidence()
    before = copy.deepcopy(chunks)
    reordered = generation.reorder_for_llm(chunks)
    assert reordered == [chunks[i] for i in [0, 2, 4, 3, 1]]
    assert chunks == before
    reordered[0]["metadata"]["title"] = "Changed"
    assert chunks == before
    assert generation.reorder_for_llm([]) == []
    assert generation.reorder_for_llm(chunks[:2]) == chunks[:2]


def test_context_labels_survive_reordering_and_special_ids():
    chunks = evidence()
    chunks[0]["id"] = "legal/văn bản[1].md::chunk-0"
    original = generation.format_context(chunks)
    reordered = generation.format_context(generation.reorder_for_llm(chunks))
    for chunk in chunks:
        label = generation.citation_label(chunk["id"])
        assert label in original and label in reordered
        assert chunk["content"] in reordered
    assert "Policy" in reordered and "legal/policy.md" in reordered
    assert "%5B1%5D" in reordered


def test_format_context_missing_display_metadata_does_not_mutate():
    chunks = evidence(count=1)
    chunks[0]["metadata"] = {}
    before = copy.deepcopy(chunks)
    context = generation.format_context(chunks)
    assert "Không có tiêu đề" in context
    assert "Không có thông tin nguồn" in context
    assert chunks == before


@pytest.mark.parametrize("method", ["hybrid", "pageindex"])
def test_generation_uses_public_interface_and_exact_context_sources(monkeypatch, method):
    chunks = evidence(method)
    original = copy.deepcopy(chunks)
    retriever = Mock(return_value=chunks)
    label = generation.citation_label(chunks[1]["id"])
    llm = Mock(return_value=f"Grounded answer. {label}")
    monkeypatch.setattr(generation, "retrieve", retriever)
    monkeypatch.setattr(generation, "call_llm", llm)
    output = generation.generate_with_citation("Question", top_k=5)
    retriever.assert_called_once_with("Question", top_k=5)
    validate_generation_result(output)
    assert output["retrieval_source"] == method
    assert output["sources"] == original == chunks
    prompt = llm.call_args.args[1]
    for chunk in output["sources"]:
        assert chunk["content"] in prompt
        assert generation.citation_label(chunk["id"]) in prompt
    assert prompt.index(chunks[4]["content"]) < prompt.index(chunks[1]["content"])


@pytest.mark.parametrize("query,top_k", [("", 5), ("  ", 5), ("Q", 0), ("Q", -1)])
def test_empty_request_never_retrieves_or_calls_llm(query, top_k):
    assert generation.generate_with_citation(query, top_k) == generation.safe_refusal()
    generation.retrieve.assert_not_called()
    generation.call_llm.assert_not_called()


@pytest.mark.parametrize("failure", [[], NotImplementedError(), RuntimeError("private detail")])
def test_retrieval_unavailable_refuses_without_llm(monkeypatch, failure):
    retriever = Mock(side_effect=failure) if isinstance(failure, Exception) else Mock(return_value=failure)
    monkeypatch.setattr(generation, "retrieve", retriever)
    output = generation.generate_with_citation("Q")
    validate_generation_result(output)
    assert output == generation.safe_refusal()
    generation.call_llm.assert_not_called()


@pytest.mark.parametrize("case", ["missing-title", "duplicate", "mixed", "dense", "nan"])
def test_invalid_retrieval_contract_refuses(monkeypatch, case):
    chunks = evidence(count=2)
    if case == "missing-title":
        chunks[0]["metadata"].pop("title")
    elif case == "duplicate":
        chunks[1] = copy.deepcopy(chunks[0])
    elif case == "mixed":
        chunks[1]["retrieval_method"] = "pageindex"
    elif case == "dense":
        for chunk in chunks:
            chunk["retrieval_method"] = "dense"
    else:
        chunks[0]["score"] = float("nan")
    monkeypatch.setattr(generation, "retrieve", Mock(return_value=chunks))
    assert generation.generate_with_citation("Q") == generation.safe_refusal()
    generation.call_llm.assert_not_called()


@pytest.mark.parametrize("answer", [
    "", "An uncited answer.", "Claim [source:invented]", "Claim [1]",
    generation.SAFE_REFUSAL, None,
])
def test_invalid_answer_refuses(monkeypatch, answer):
    monkeypatch.setattr(generation, "retrieve", Mock(return_value=evidence()))
    monkeypatch.setattr(generation, "call_llm", Mock(return_value=answer))
    assert generation.generate_with_citation("Q") == generation.safe_refusal()


@pytest.mark.parametrize("suffix", [
    " https://invented.example", " [source:unknown]",
    "\n\nAn uncited extra paragraph.", " <a href='bad'>Source</a>",
])
def test_mixed_valid_and_invalid_citations_refuse(monkeypatch, suffix):
    chunks = evidence()
    answer = "Claim " + generation.citation_label(chunks[0]["id"]) + suffix
    monkeypatch.setattr(generation, "retrieve", Mock(return_value=chunks))
    monkeypatch.setattr(generation, "call_llm", Mock(return_value=answer))
    assert generation.generate_with_citation("Q") == generation.safe_refusal()


def test_provider_error_is_safe_and_does_not_log_secret(monkeypatch, caplog):
    monkeypatch.setattr(generation, "retrieve", Mock(return_value=evidence()))
    monkeypatch.setattr(generation, "call_llm", Mock(side_effect=RuntimeError("secret-key")))
    assert generation.generate_with_citation("Q") == generation.safe_refusal()
    assert "secret-key" not in caplog.text
    assert "RuntimeError" in caplog.text


# Keep the actual adapter reference before the autouse fixture replaces it.
_REAL_CALL_LLM = generation.call_llm


@pytest.mark.parametrize("provider", ["openai", "gemini", "anthropic"])
def test_provider_dispatch_returns_plain_text_without_network(monkeypatch, provider):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_MODEL", "configured-model")
    key = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[provider]
    monkeypatch.setenv(key, "test-only-key")
    create = Mock()
    client = SimpleNamespace(
        responses=SimpleNamespace(create=create),
        models=SimpleNamespace(generate_content=create),
        messages=SimpleNamespace(create=create),
    )
    context = Mock()
    context.__enter__ = Mock(return_value=client)
    context.__exit__ = Mock(return_value=False)
    constructor = Mock(return_value=context)
    if provider == "openai":
        module = ModuleType("openai")
        module.OpenAI = constructor
        create.return_value = SimpleNamespace(output_text=" plain text ")
        monkeypatch.setitem(sys.modules, "openai", module)
    elif provider == "gemini":
        google = ModuleType("google")
        genai = ModuleType("google.genai")
        genai.Client = constructor
        genai.types = SimpleNamespace(HttpOptions=lambda **kw: kw, GenerateContentConfig=lambda **kw: kw)
        google.genai = genai
        monkeypatch.setitem(sys.modules, "google", google)
        monkeypatch.setitem(sys.modules, "google.genai", genai)
        create.return_value = SimpleNamespace(text=" plain text ")
    else:
        module = ModuleType("anthropic")
        module.Anthropic = constructor
        monkeypatch.setitem(sys.modules, "anthropic", module)
        create.return_value = SimpleNamespace(content=[
            SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=" plain text "),
        ])
    assert _REAL_CALL_LLM("system", "question") == "plain text"
    assert create.call_args.kwargs["model"] == "configured-model"
    assert constructor.call_args.kwargs["api_key"] == "test-only-key"
    context.__exit__.assert_called_once()


@pytest.mark.parametrize("provider,model,key", [
    ("unknown", "model", "key"), ("openai", "", "key"), ("openai", "model", ""),
])
def test_bad_provider_configuration_fails_before_sdk(monkeypatch, provider, model, key):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_MODEL", model)
    monkeypatch.setenv("OPENAI_API_KEY", key)
    with pytest.raises(ValueError):
        _REAL_CALL_LLM("system", "question")


def test_ui_persists_and_rerenders_sources(monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    chunks = evidence(count=1)
    output = {
        "answer": "Answer " + generation.citation_label(chunks[0]["id"]),
        "sources": chunks, "retrieval_source": "hybrid",
    }
    mock = Mock(return_value=output)
    monkeypatch.setattr(generation, "generate_with_citation", mock)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.chat_input[0].set_value("Question").run()
    assert not app.exception
    assert app.session_state["messages"][-1]["result"] == output
    assert any("Policy" in item.value for item in app.text)
    app.run()
    assert not app.exception
    assert any("Policy" in item.value for item in app.text)
    mock.assert_called_once_with("Question", top_k=5)


@pytest.mark.parametrize("case", ["refusal", "error", "missing-metadata"])
def test_ui_handles_refusal_errors_and_missing_metadata(monkeypatch, case):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    output = generation.safe_refusal()
    if case == "missing-metadata":
        chunks = evidence(count=1)
        chunks[0]["metadata"] = {}
        output = {"answer": "Answer", "sources": chunks, "retrieval_source": "hybrid"}
    mock = Mock(side_effect=RuntimeError("secret")) if case == "error" else Mock(return_value=output)
    monkeypatch.setattr(generation, "generate_with_citation", mock)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.chat_input[0].set_value("Question").run()
    assert not app.exception
    app.run()
    assert not app.exception
    assert app.session_state["messages"][-1]["result"] == output