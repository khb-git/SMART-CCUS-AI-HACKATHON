"""
Streamlit chatbot UI for the SMART CCUS Class VI Review Assistant.
"""

from __future__ import annotations

import streamlit as st

from ui.api_client import (
    DEFAULT_API_URL,
    ask_api,
    build_ask_payload,
    build_markdown_review_report,
    default_report_filename,
    format_evidence_heading,
    format_similarity_score,
    review_document_api,
    status_icon,
    status_label,
)


st.set_page_config(
    page_title="SMART CCUS Class VI Review Assistant",
    page_icon="🧠",
    layout="wide",
)


st.title("SMART CCUS Class VI Review Assistant")
st.caption(
    "Ask Class VI permit review questions, inspect evidence-backed answers, "
    "or temporarily review uploaded documents for completeness."
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


ask_tab, review_tab = st.tabs(["Ask Assistant", "Review Document"])


with ask_tab:
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


with review_tab:
    st.subheader("Review uploaded document")
    st.caption(
        "Upload a Class VI document for temporary completeness review. "
        "Uploaded files are processed for this request and are not stored permanently."
    )

    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, or XLSX",
        type=["pdf", "docx", "xlsx"],
    )

    review_plan_type = st.selectbox(
        "Plan type",
        options=[
            "auto",
            "testing_monitoring",
        ],
        index=0,
        help=(
            "Use auto when the document can be classified. "
            "For now, only the Testing and Monitoring checklist is available."
        ),
    )

    col_a, col_b = st.columns(2)

    with col_a:
        review_chunk_size = st.number_input(
            "Review chunk size",
            min_value=250,
            max_value=3000,
            value=1000,
            step=250,
        )

    with col_b:
        review_chunk_overlap = st.number_input(
            "Review chunk overlap",
            min_value=0,
            max_value=500,
            value=100,
            step=25,
        )

    run_review_clicked = st.button(
        "Review uploaded document",
        type="primary",
    )

    if run_review_clicked:
        if uploaded_file is None:
            st.error("Please upload a PDF, DOCX, or XLSX file.")
            st.stop()

        try:
            with st.spinner(
                "Temporarily processing document and running checklist review..."
            ):
                review_response = review_document_api(
                    file_bytes=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    plan_type=review_plan_type,
                    chunk_size=int(review_chunk_size),
                    chunk_overlap=int(review_chunk_overlap),
                    api_url=api_url,
                )

        except Exception as exc:
            st.error("The document review request failed.")
            st.exception(exc)
            st.stop()

        report = review_response.get("report", {})
        classification = review_response.get("classification", {})
        overall_status = report.get("overall_status", "")

        st.subheader("Review result")

        metric_cols = st.columns(4)

        with metric_cols[0]:
            st.metric("Document", review_response.get("document_name", "Unknown"))

        with metric_cols[1]:
            st.metric("Detected type", review_response.get("document_type", "Unknown"))

        with metric_cols[2]:
            st.metric(
                "Classification confidence",
                review_response.get("classification_confidence", "Unknown"),
            )

        with metric_cols[3]:
            st.metric(
                "Overall status",
                f"{status_icon(overall_status)} {status_label(overall_status)}",
            )

        st.markdown("### Summary")
        st.write(report.get("summary", ""))

        storage_policy = review_response.get("storage_policy", "")
        if storage_policy:
            st.info(storage_policy)

        markdown_report = build_markdown_review_report(review_response)
        report_filename = default_report_filename(
            review_response.get("document_name", "document")
        )

        st.download_button(
            label="Download Markdown review report",
            data=markdown_report,
            file_name=report_filename,
            mime="text/markdown",
        )

        with st.expander("Classification details", expanded=False):
            st.json(classification)

        findings = report.get("findings", [])

        if not findings:
            st.warning("No checklist findings returned.")
        else:
            st.markdown("### Checklist findings")

            present_count = sum(
                1 for item in findings if item.get("status") == "present"
            )
            partial_count = sum(
                1 for item in findings if item.get("status") == "partial"
            )
            missing_count = sum(
                1 for item in findings if item.get("status") == "missing"
            )
            unclear_count = sum(
                1 for item in findings if item.get("status") == "unclear"
            )

            status_cols = st.columns(4)

            with status_cols[0]:
                st.metric("Present", present_count)

            with status_cols[1]:
                st.metric("Partial", partial_count)

            with status_cols[2]:
                st.metric("Missing", missing_count)

            with status_cols[3]:
                st.metric("Unclear", unclear_count)

            for finding in findings:
                status = finding.get("status", "")
                label = finding.get("label", finding.get("item_id", "Finding"))
                severity = finding.get("severity", "")
                requirement_level = finding.get("requirement_level", "")

                heading = (
                    f"{status_icon(status)} {status_label(status)} — "
                    f"{label} "
                    f"({requirement_level}, {severity})"
                )

                expanded = status in {"missing", "partial"}

                with st.expander(heading, expanded=expanded):
                    st.markdown("**Finding**")
                    st.write(finding.get("finding", ""))

                    matched_terms = finding.get("matched_terms", [])
                    if matched_terms:
                        st.markdown("**Matched terms**")
                        st.write(", ".join(matched_terms))

                    excerpts = finding.get("supporting_excerpts", [])
                    if excerpts:
                        st.markdown("**Supporting excerpts**")
                        for excerpt in excerpts:
                            st.write(f"- {excerpt}")

                    recommended_fix = finding.get("recommended_fix", "")
                    if recommended_fix:
                        st.markdown("**Recommended fix**")
                        st.write(recommended_fix)