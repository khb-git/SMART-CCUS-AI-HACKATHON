from rag.types import Chunk, ChunkMetadata, Collection, DocumentType, RetrievalResult


def make_result(collection=Collection.PERMITS, text="Monitoring text."):
    metadata = ChunkMetadata(
        source_document="One_Earth_Testing_and_Monitoring_Plan.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
        page_number=63,
        chunk_index=12,
        section_id="8",
        schema_section_id="8",
        schema_section_title="Testing and Monitoring Plan",
        content_type="text",
        plan_type="testing_monitoring",
        online_link="https://example.com/one_earth_tm.pdf",
        source_page="https://example.com/docket",
    )

    return RetrievalResult(
        chunk=Chunk(
            text=text,
            metadata=metadata,
            chunk_id="chunk-123",
        ),
        score=0.7047,
        collection=collection,
    )


def test_source_label_for_collection():
    from rag.evidence import source_label_for_collection

    assert source_label_for_collection(Collection.REFERENCE) == "REGULATORY REFERENCE"
    assert source_label_for_collection(Collection.PERMITS) == "PERMIT PRECEDENT"


def test_make_excerpt_trims_long_text():
    from rag.evidence import make_excerpt

    text = " ".join(["monitoring"] * 100)
    excerpt = make_excerpt(text, max_chars=40)

    assert len(excerpt) <= 40
    assert excerpt.endswith("...")


def test_package_evidence_preserves_metadata():
    from rag.evidence import package_evidence

    result = make_result()
    evidence = package_evidence([result])

    assert len(evidence) == 1

    item = evidence[0]

    assert item.evidence_id == "E1"
    assert item.collection == Collection.PERMITS
    assert item.source_label == "PERMIT PRECEDENT"
    assert item.source_document == "One_Earth_Testing_and_Monitoring_Plan.pdf"
    assert item.page_number == 63
    assert item.chunk_index == 12
    assert item.score == 0.7047
    assert item.content_type == "text"
    assert item.plan_type == "testing_monitoring"
    assert item.schema_section_id == "8"
    assert item.schema_section_title == "Testing and Monitoring Plan"
    assert item.online_link == "https://example.com/one_earth_tm.pdf"
    assert item.source_page == "https://example.com/docket"
    assert item.chunk_id == "chunk-123"


def test_package_evidence_start_index():
    from rag.evidence import package_evidence

    result = make_result()
    evidence = package_evidence([result], start_index=4)

    assert evidence[0].evidence_id == "E4"


def test_format_evidence_context_includes_citation_fields():
    from rag.evidence import format_evidence_context, package_evidence

    result = make_result(
        text="Flow will be monitored with a mass flowmeter at the well head."
    )

    evidence = package_evidence([result])
    context = format_evidence_context(evidence)

    assert "[E1] PERMIT PRECEDENT" in context
    assert "One_Earth_Testing_and_Monitoring_Plan.pdf" in context
    assert "Page: 63" in context
    assert "Section: 8 Testing and Monitoring Plan" in context
    assert "Flow will be monitored" in context
    assert "https://example.com/one_earth_tm.pdf" in context


def test_format_evidence_context_handles_empty_list():
    from rag.evidence import format_evidence_context

    assert format_evidence_context([]) == "No evidence retrieved."


def test_evidence_item_to_dict_is_serializable():
    from rag.evidence import package_evidence

    item = package_evidence([make_result()])[0]
    data = item.to_dict()

    assert data["evidence_id"] == "E1"
    assert data["collection"] == "permits"
    assert data["source_label"] == "PERMIT PRECEDENT"
    assert data["schema_section_id"] == "8"