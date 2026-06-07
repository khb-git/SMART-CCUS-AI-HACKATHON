"""
Streamlit chatbot UI for the SMART CCUS Class VI Review Assistant.
"""

from __future__ import annotations

import streamlit as st

from ui.api_client import (
    DEFAULT_API_URL,
    ask_api,
    build_ask_payload,
    format_evidence_heading,
    format_similarity_score,
)


st.set_page_config(
    page_title="SMART CCUS Class VI Review Assistant",
    page_icon="🧠",
    layout="wide",
)


st.title("SMART CCUS Class VI Review Assistant")
st.caption(
    "Ask Class VI permit review questions and inspect evidence-backed answers."
)


with st.sidebar:
    st.header("Backend Settings")

    api_url = st.text_input(
        "FastAPI URL",
        value=DEFAULT_API_URL,
        help="Run the backend with: python -m uvicorn api.main:app --reload",
    )

    persist_directory = st.text_input(
        "Chroma persist directory",
        value="chroma_data",
    )

    st.header("Retrieval Settings")

    section_id = st.text_input(
        "Section ID",
        value="8",
        help="Use 8 for Testing and Monitoring Plan.",
    )

    intent = st.selectbox(
        "Intent",
        options=[
            "auto",
            "regulatory_requirement",
            "permit_precedent",
            "cross_check",
            "general_review",
        ],
        index=0,
    )

    k_reference = st.slider(
        "Reference evidence count",
        min_value=0,
        max_value=10,
        value=3,
    )

    k_permits = st.slider(
        "Permit evidence count",
        min_value=0,
        max_value=10,
        value=5,
    )

    fetch_k = st.slider(
        "Raw candidates before diversification",
        min_value=5,
        max_value=100,
        value=30,
        step=5,
    )

    max_per_source = st.slider(
        "Max evidence items per source",
        min_value=1,
        max_value=5,
        value=1,
    )

    expand_retrieval_query = st.checkbox(
        "Use query expansion",
        value=True,
    )

    use_reranking = st.checkbox(
        "Use local reranking",
        value=True,
    )

    st.caption(
        "Similarity scores reflect retrieval similarity, not correctness probability."
    )


default_question = "How do applicants monitor injection pressure and flow rate?"

query = st.text_area(
    "Review question",
    value=default_question,
    height=100,
)

ask_clicked = st.button("Ask review assistant", type="primary")


if ask_clicked:
    if not query.strip():
        st.error("Please enter a review question.")
        st.stop()

    payload = build_ask_payload(
        query=query,
        persist_directory=persist_directory,
        section_id=section_id,
        intent=intent,
        k_reference=k_reference,
        k_permits=k_permits,
        fetch_k=fetch_k,
        max_per_source=max_per_source,
        expand_retrieval_query=expand_retrieval_query,
        use_reranking=use_reranking,
    )

    try:
        with st.spinner("Retrieving evidence and building answer..."):
            response = ask_api(
                payload=payload,
                api_url=api_url,
            )

    except Exception as exc:
        st.error("The backend request failed.")
        st.exception(exc)
        st.stop()

    st.subheader("Answer")
    st.markdown(response.get("answer", ""))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Reviewer interpretation")
        st.write(response.get("reviewer_interpretation", ""))

    with col2:
        st.subheader("Potential follow-up")
        st.write(response.get("potential_follow_up", ""))

    with st.expander("Evidence summary", expanded=False):
        st.text(response.get("evidence_summary", ""))

    st.subheader("Evidence items")

    evidence_items = response.get("evidence_items", [])

    if not evidence_items:
        st.info("No evidence items returned.")
    else:
        for item in evidence_items:
            heading = format_evidence_heading(item)

            with st.expander(heading, expanded=False):
                left, right = st.columns([2, 1])

                with left:
                    st.markdown("**Excerpt**")
                    st.write(item.get("excerpt", ""))

                with right:
                    st.markdown("**Metadata**")
                    st.write(f"Collection: `{item.get('collection', '')}`")
                    st.write(f"Content type: `{item.get('content_type', '')}`")
                    st.write(f"Plan type: `{item.get('plan_type', '')}`")
                    st.write(
                        "Similarity score: "
                        f"`{format_similarity_score(item.get('score'))}`"
                    )
                    st.write(f"Page: `{item.get('page_number', '')}`")
                    st.write(f"Chunk index: `{item.get('chunk_index', '')}`")
                    st.write(
                        "Section: "
                        f"`{item.get('schema_section_id', '')} "
                        f"{item.get('schema_section_title', '')}`"
                    )

                    online_link = item.get("online_link", "")
                    source_page = item.get("source_page", "")

                    if online_link:
                        st.link_button("Open source document", online_link)

                    if source_page:
                        st.link_button("Open source page", source_page)
else:
    st.info("Enter a question and click **Ask review assistant**.")