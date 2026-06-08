"""
Streamlit chatbot UI for the SMART CCUS Class VI Review Assistant.
"""

from __future__ import annotations

import streamlit as st

from ui.api_client import (
    DEFAULT_API_URL,
    ask_api,
    build_ask_payload,
    build_markdown_package_report,
    build_markdown_review_report,
    default_package_report_filename,
    default_report_filename,
    format_evidence_heading,
    format_similarity_score,
    review_document_api,
    review_package_api,
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


def finding_status_counts(findings: list[dict]) -> dict[str, int]:
    """Count checklist finding statuses for UI display."""
    counts = {
        "present": 0,
        "evidence_found": 0,
        "missing": 0,
        "unclear": 0,
    }

    for finding in findings:
        status = finding.get("status", "")
        if status in counts:
            counts[status] += 1

    return counts


def render_finding_summary_metrics(findings: list[dict]) -> None:
    """Render compact finding-count metrics."""
    counts = finding_status_counts(findings)
    metric_cols = st.columns(4)

    with metric_cols[0]:
        st.metric("Present", counts["present"])

    with metric_cols[1]:
        st.metric("Evidence found", counts["evidence_found"])

    with metric_cols[2]:
        st.metric("Missing", counts["missing"])

    with metric_cols[3]:
        st.metric("Unclear", counts["unclear"])


def render_package_findings(
    findings: list[dict],
    key_prefix: str,
    default_show: bool = False,
) -> None:
    """Render package checklist findings with reviewer-friendly details."""
    show_findings = st.checkbox(
        "Show checklist findings",
        value=default_show,
        key=f"show_findings_{key_prefix}",
    )

    if not show_findings:
        return

    for finding in findings:
        status = finding.get("status", "")
        label = finding.get("label", finding.get("item_id", "Finding"))
        matched_groups = finding.get("matched_evidence_group_names", []) or []
        excerpts = finding.get("supporting_excerpts", []) or []

        st.markdown(
            f"**{status_icon(status)} {status_label(status)} — {label}**"
        )
        st.write(finding.get("finding", ""))

        if matched_groups:
            st.caption(
                "Matched evidence groups: "
                + ", ".join(f"`{group}`" for group in matched_groups)
            )

        if excerpts:
            with st.expander("Supporting excerpts", expanded=False):
                for excerpt in excerpts:
                    st.write(f"- {excerpt}")

        recommended_fix = finding.get("recommended_fix", "")
        if recommended_fix:
            st.caption(f"Recommended fix: {recommended_fix}")


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


ask_tab, review_tab, package_tab = st.tabs(
    ["Ask Assistant", "Review Document", "Review Package"]
)


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
            "pre_operational_testing",
            "pisc_site_closure",
            "emergency_remedial_response",
            "well_construction",
            "aor_corrective_action",
            "financial_responsibility",
            "site_operating",
            "site_geologic_characterization",
            "injection_well_plugging",
            "project_narrative",
        ],
        index=0,
        help=(
            "Use auto when the document can be classified, or manually select a checklist."
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

            render_finding_summary_metrics(findings)

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

                expanded = status in {"missing", "evidence_found"}

                with st.expander(heading, expanded=expanded):
                    st.markdown("**Finding**")
                    st.write(finding.get("finding", ""))

                    matched_terms = finding.get("matched_terms", [])
                    if matched_terms:
                        st.markdown("**Matched terms**")
                        st.write(", ".join(matched_terms))

                    matched_groups = (
                        finding.get("matched_evidence_group_names", []) or []
                    )
                    if matched_groups:
                        st.markdown("**Matched evidence groups**")
                        st.write(", ".join(f"`{group}`" for group in matched_groups))

                    excerpts = finding.get("supporting_excerpts", [])
                    if excerpts:
                        st.markdown("**Supporting excerpts**")
                        for excerpt in excerpts:
                            st.write(f"- {excerpt}")

                    recommended_fix = finding.get("recommended_fix", "")
                    if recommended_fix:
                        st.markdown("**Recommended fix**")
                        st.write(recommended_fix)


with package_tab:
    st.subheader("Review uploaded document package")
    st.caption(
        "Upload multiple Class VI documents for temporary package-level review. "
        "Uploaded files are processed for this request and are not stored permanently."
    )

    package_files = st.file_uploader(
        "Upload package documents",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        help="Upload multiple PDF, DOCX, or XLSX files from the same Class VI application package.",
    )

    package_name = st.text_input(
        "Package name",
        value="uploaded_package",
    )

    pkg_col_a, pkg_col_b = st.columns(2)

    with pkg_col_a:
        package_chunk_size = st.number_input(
            "Package review chunk size",
            min_value=250,
            max_value=3000,
            value=1000,
            step=250,
        )

    with pkg_col_b:
        package_chunk_overlap = st.number_input(
            "Package review chunk overlap",
            min_value=0,
            max_value=500,
            value=100,
            step=25,
        )

    run_package_review_clicked = st.button(
        "Review uploaded package",
        type="primary",
    )

    if run_package_review_clicked:
        if not package_files:
            st.error("Please upload at least one PDF, DOCX, or XLSX file.")
            st.stop()

        try:
            file_payload = [
                (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                )
                for uploaded_file in package_files
            ]

            with st.spinner(
                "Temporarily processing package documents and running package review..."
            ):
                package_response = review_package_api(
                    files=file_payload,
                    package_name=package_name,
                    chunk_size=int(package_chunk_size),
                    chunk_overlap=int(package_chunk_overlap),
                    api_url=api_url,
                )

        except Exception as exc:
            st.error("The package review request failed.")
            st.exception(exc)
            st.stop()

        package_report = package_response.get("report", {})
        package_status = package_report.get("overall_status", "")

        st.subheader("Package review result")

        package_metric_cols = st.columns(4)

        with package_metric_cols[0]:
            st.metric("Package", package_response.get("package_name", "Unknown"))

        with package_metric_cols[1]:
            st.metric(
                "Overall status",
                f"{status_icon(package_status)} {status_label(package_status)}",
            )

        with package_metric_cols[2]:
            st.metric(
                "Detected document types",
                len(package_report.get("detected_plan_types", []) or []),
            )

        with package_metric_cols[3]:
            st.metric(
                "Missing required",
                len(package_report.get("missing_required_plan_types", []) or []),
            )

        st.markdown("### Summary")
        st.write(package_report.get("summary", ""))

        storage_policy = package_response.get("storage_policy", "")
        if storage_policy:
            st.info(storage_policy)

        package_markdown_report = build_markdown_package_report(package_response)
        package_report_filename = default_package_report_filename(
            package_response.get("package_name", "uploaded_package")
        )

        st.download_button(
            label="Download Markdown package review report",
            data=package_markdown_report,
            file_name=package_report_filename,
            mime="text/markdown",
        )

        st.markdown("### Package coverage")

        coverage_cols = st.columns(5)

        with coverage_cols[0]:
            st.markdown("**Detected document types**")
            detected = package_report.get("detected_plan_types", []) or []
            if detected:
                for plan_type in detected:
                    st.write(f"✅ `{plan_type}`")
            else:
                st.write("None detected.")

        with coverage_cols[1]:
            st.markdown("**Missing required**")
            missing_required = (
                package_report.get("missing_required_plan_types", []) or []
            )
            if missing_required:
                for plan_type in missing_required:
                    st.write(f"🔴 `{plan_type}`")
            else:
                st.write("No required document types missing.")

        with coverage_cols[2]:
            st.markdown("**Duplicate document types**")
            duplicates = package_report.get("duplicate_plan_types", []) or []
            if duplicates:
                for plan_type in duplicates:
                    st.write(f"🟠 `{plan_type}`")
            else:
                st.write("No duplicates detected.")

        with coverage_cols[3]:
            st.markdown("**Unknown documents**")
            unknown_documents = package_report.get("unknown_documents", []) or []
            if unknown_documents:
                for document_name in unknown_documents:
                    st.write(f"⚪ `{document_name}`")
            else:
                st.write("No unknown documents.")

        with coverage_cols[4]:
            st.markdown("**Supporting documents**")
            supporting_documents = package_report.get("supporting_documents", []) or []
            if supporting_documents:
                for document_name in supporting_documents:
                    st.write(f"🧩 `{document_name}`")
            else:
                st.write("No supporting documents.")

        with st.expander("Expected package document types", expanded=False):
            expected = package_report.get("expected_plan_types", []) or []
            for plan_type in expected:
                st.write(f"- `{plan_type}`")

        st.markdown("### Per-document reviews")

        document_reviews = package_report.get("document_reviews", []) or []

        if not document_reviews:
            st.warning("No document reviews returned.")
        else:
            for document_review in document_reviews:
                document_name = document_review.get("document_name", "Unknown document")
                document_type = document_review.get("document_type", "unknown")
                confidence = document_review.get(
                    "classification_confidence",
                    "unknown",
                )
                document_report = document_review.get("report") or {}

                document_status = document_report.get("overall_status", "")

                heading = (
                    f"{document_name} — `{document_type}` "
                    f"({confidence})"
                )

                if document_status:
                    heading += (
                        f" — {status_icon(document_status)} "
                        f"{status_label(document_status)}"
                    )

                with st.expander(heading, expanded=False):
                    document_role = document_review.get("document_role", "main")
                    supporting_type = document_review.get(
                        "supporting_document_type",
                        "",
                    )
                    covered_plan_types = (
                        document_review.get("covered_plan_types", []) or []
                    )
                    checklist_reports = (
                        document_review.get("checklist_reports", {}) or {}
                    )
                    error = document_review.get("error", "")

                    role_cols = st.columns(3)

                    with role_cols[0]:
                        st.metric("Document role", document_role)

                    with role_cols[1]:
                        st.metric("Covered plan types", len(covered_plan_types))

                    with role_cols[2]:
                        st.metric("Checklist reports", len(checklist_reports))

                    if supporting_type:
                        st.info(f"Supporting document type: `{supporting_type}`")

                    if covered_plan_types:
                        st.markdown("**Covered plan types**")
                        st.write(
                            ", ".join(
                                f"`{plan_type}`"
                                for plan_type in covered_plan_types
                            )
                        )

                    if error:
                        if document_role == "supporting":
                            st.info(error)
                        else:
                            st.error(error)

                    classification = document_review.get("classification", {})
                    with st.expander("Classification details", expanded=False):
                        st.json(classification)

                    if checklist_reports:
                        st.markdown("**Checklist reports by covered plan type**")

                        for plan_type, checklist_report in checklist_reports.items():
                            checklist_status = checklist_report.get(
                                "overall_status",
                                "",
                            )
                            checklist_findings = (
                                checklist_report.get("findings", []) or []
                            )

                            checklist_heading = (
                                f"{plan_type} — "
                                f"{status_icon(checklist_status)} "
                                f"{status_label(checklist_status)}"
                            )

                            with st.expander(checklist_heading, expanded=False):
                                st.write(checklist_report.get("summary", ""))

                                render_finding_summary_metrics(checklist_findings)

                                render_package_findings(
                                    checklist_findings,
                                    key_prefix=f"{document_name}_{plan_type}",
                                    default_show=False,
                                )

                    elif document_report:
                        st.markdown("**Document review summary**")
                        st.write(document_report.get("summary", ""))

                        findings = document_report.get("findings", []) or []

                        render_finding_summary_metrics(findings)

                        render_package_findings(
                            findings,
                            key_prefix=document_name,
                            default_show=False,
                        )