"""Streamlit chat UI; all displayed evidence comes from GenerationResult."""

import copy
import logging
from urllib.parse import urlsplit

import streamlit as st

from src.task10_generation import (
    citation_label,
    generate_with_citation,
    safe_refusal,
)


def render_result(result: dict) -> None:
    st.markdown(result["answer"])
    route = result.get("retrieval_source", "none")
    st.caption(f"Nguồn truy xuất: {route}")
    sources = result.get("sources") or []
    if not sources:
        return
    with st.expander(f"Tài liệu làm căn cứ ({len(sources)})"):
        for item in sources:
            metadata = item.get("metadata") or {}
            st.text(metadata.get("title") or "Không có tiêu đề")
            st.text(citation_label(item["id"]))
            st.text(f"Nguồn: {metadata.get('source') or 'Không có thông tin nguồn'}")
            url = metadata.get("url")
            if isinstance(url, str):
                try:
                    parsed = urlsplit(url)
                    if parsed.scheme in {"http", "https"} and parsed.netloc:
                        st.text(f"URL: {url}")
                        st.link_button("Mở nguồn gốc", url)
                except ValueError:
                    pass
            st.caption(
                f"Score: {item.get('score', '—')} | "
                f"Phương pháp: {item.get('retrieval_method', '—')}"
            )
            st.text(item.get("content", ""))
            st.divider()


st.set_page_config(page_title="RAG Chatbot", layout="wide")
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Tra cứu và trả lời từ tài liệu của nhóm.")
    top_k = st.slider("Số đoạn tài liệu tham khảo", 1, 10, 5)

st.title("RAG Chatbot")
st.caption("Đặt câu hỏi và xem tài liệu làm căn cứ bên dưới câu trả lời.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "result" in message:
            render_result(message["result"])
        else:
            st.markdown(message["content"])

query = st.chat_input("Nhập câu hỏi...")
if query and (query := query.strip()):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm tài liệu và soạn câu trả lời..."):
            try:
                result = copy.deepcopy(generate_with_citation(query, top_k=top_k))
            except Exception as error:
                logging.getLogger(__name__).warning(
                    "Generation unavailable (%s)", type(error).__name__
                )
                result = safe_refusal()
        render_result(result)
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "query": query,
        "top_k": top_k,
        "result": result,
    })