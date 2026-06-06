from rag.types import Chunk, ChunkMetadata, Collection, DocumentType, RetrievalResult


def make_result(collection, source_document, text):
    document_type = (
        DocumentType.EPA_GUIDANCE
        if collection == Collection.REFERENCE
        else DocumentType.PERMIT_APPLICATION
    )

    metadata = ChunkMetadata(
        source_document=source_document,
        document_type=document_type,
        page_number=10,
        chunk_index=1,
        section_id="8",
        schema_section_id="8",
        schema_section_title="Testing and Monitoring Plan",
        content_type="text",
        plan_type="testing_monitoring",
        online_link="https://example.com/doc.pdf",
        source_page="https://example.com/source",
    )

    return RetrievalResult(
        chunk=Chunk(
            text=text,
            metadata=metadata,
            chunk_id=f"{source_document}:1",
        ),
        score=0.8,
        collection=collection,
    )


def test_ask_question_retrieves_packages_and_builds_answer(monkeypatch):
    import rag.ask as ask_module

    calls = {}

    class FakeEmbeddings:
        def __init__(self, model_name):
            calls["model_name"] = model_name

    class FakeVectorStore:
        def __init__(self, persist_directory):
            calls["persist_directory"] = persist_directory

    class FakeRetriever:
        def __init__(self, embeddings, store):
            calls["retriever_created"] = True

        def retrieve_reference_diversified(
            self,
            query_text,
            section_id="",
            k=5,
            fetch_k=30,
            max_per_source=1,
        ):
            calls["reference_query"] = query_text
            calls["reference_section_id"] = section_id
            calls["reference_k"] = k
            calls["reference_fetch_k"] = fetch_k
            calls["reference_max_per_source"] = max_per_source

            return [
                make_result(
                    Collection.REFERENCE,
                    "implementation_manual.pdf",
                    "Reference evidence about monitoring.",
                )
            ]

        def retrieve_permits_diversified(
            self,
            query_text,
            section_id="",
            k=5,
            fetch_k=30,
            max_per_source=1,
        ):
            calls["permit_query"] = query_text
            calls["permit_section_id"] = section_id
            calls["permit_k"] = k
            calls["permit_fetch_k"] = fetch_k
            calls["permit_max_per_source"] = max_per_source

            return [
                make_result(
                    Collection.PERMITS,
                    "One_Earth_Testing_and_Monitoring_Plan.pdf",
                    "Permit evidence about injection pressure.",
                )
            ]

    monkeypatch.setattr(ask_module, "Embeddings", FakeEmbeddings)
    monkeypatch.setattr(ask_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(ask_module, "Retriever", FakeRetriever)

    answer = ask_module.ask_question(
        question="Review injection pressure monitoring against EPA expectations.",
        persist_directory="fake_chroma",
        model_name="fake-model",
        section_id="8",
        k_reference=2,
        k_permits=3,
        fetch_k=20,
        max_per_source=1,
        intent="auto",
    )

    assert calls["model_name"] == "fake-model"
    assert calls["persist_directory"] == "fake_chroma"
    assert calls["reference_query"] == "Review injection pressure monitoring against EPA expectations."
    assert calls["permit_query"] == "Review injection pressure monitoring against EPA expectations."
    assert calls["reference_section_id"] == "8"
    assert calls["permit_section_id"] == "8"
    assert calls["reference_k"] == 2
    assert calls["permit_k"] == 3
    assert calls["reference_fetch_k"] == 20
    assert calls["permit_fetch_k"] == 20

    assert answer.question == "Review injection pressure monitoring against EPA expectations."
    assert len(answer.evidence_items) == 2
    assert answer.evidence_items[0].evidence_id == "E1"
    assert answer.evidence_items[0].collection == Collection.REFERENCE
    assert answer.evidence_items[1].evidence_id == "E2"
    assert answer.evidence_items[1].collection == Collection.PERMITS


def test_ask_main_prints_formatted_answer(monkeypatch, capsys):
    import rag.ask as ask_module

    class FakeArgs:
        query = "What monitoring is required?"
        persist_directory = "fake_chroma"
        model_name = "fake-model"
        section_id = "8"
        k_reference = 1
        k_permits = 1
        fetch_k = 10
        max_per_source = 1
        intent = "auto"

    def fake_parse_args():
        return FakeArgs()

    def fake_ask_question(**kwargs):
        return ask_module.build_template_answer(
            question=kwargs["question"],
            evidence_items=[],
        )

    monkeypatch.setattr(ask_module, "parse_args", fake_parse_args)
    monkeypatch.setattr(ask_module, "ask_question", fake_ask_question)

    ask_module.main()

    output = capsys.readouterr().out

    assert "Question:" in output
    assert "What monitoring is required?" in output
    assert "Answer:" in output
    assert "Insufficient context" in output

def test_ask_question_reference_intent_only_queries_reference(monkeypatch):
    import rag.ask as ask_module

    calls = {
        "reference_called": False,
        "permits_called": False,
    }

    class FakeEmbeddings:
        def __init__(self, model_name):
            pass

    class FakeVectorStore:
        def __init__(self, persist_directory):
            pass

    class FakeRetriever:
        def __init__(self, embeddings, store):
            pass

        def retrieve_reference_diversified(
            self,
            query_text,
            section_id="",
            k=5,
            fetch_k=30,
            max_per_source=1,
        ):
            calls["reference_called"] = True
            return [
                make_result(
                    Collection.REFERENCE,
                    "implementation_manual.pdf",
                    "Reference evidence.",
                )
            ]

        def retrieve_permits_diversified(
            self,
            query_text,
            section_id="",
            k=5,
            fetch_k=30,
            max_per_source=1,
        ):
            calls["permits_called"] = True
            return []

    monkeypatch.setattr(ask_module, "Embeddings", FakeEmbeddings)
    monkeypatch.setattr(ask_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(ask_module, "Retriever", FakeRetriever)

    answer = ask_module.ask_question(
        question="What does Class VI require for testing and monitoring?",
        intent="regulatory_requirement",
    )

    assert calls["reference_called"]
    assert not calls["permits_called"]
    assert len(answer.evidence_items) == 1
    assert answer.evidence_items[0].collection == Collection.REFERENCE


def test_ask_question_permit_intent_only_queries_permits(monkeypatch):
    import rag.ask as ask_module

    calls = {
        "reference_called": False,
        "permits_called": False,
    }

    class FakeEmbeddings:
        def __init__(self, model_name):
            pass

    class FakeVectorStore:
        def __init__(self, persist_directory):
            pass

    class FakeRetriever:
        def __init__(self, embeddings, store):
            pass

        def retrieve_reference_diversified(
            self,
            query_text,
            section_id="",
            k=5,
            fetch_k=30,
            max_per_source=1,
        ):
            calls["reference_called"] = True
            return []

        def retrieve_permits_diversified(
            self,
            query_text,
            section_id="",
            k=5,
            fetch_k=30,
            max_per_source=1,
        ):
            calls["permits_called"] = True
            return [
                make_result(
                    Collection.PERMITS,
                    "One_Earth_Testing_and_Monitoring_Plan.pdf",
                    "Permit evidence.",
                )
            ]

    monkeypatch.setattr(ask_module, "Embeddings", FakeEmbeddings)
    monkeypatch.setattr(ask_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(ask_module, "Retriever", FakeRetriever)

    answer = ask_module.ask_question(
        question="How do applicants monitor injection pressure?",
        intent="permit_precedent",
    )

    assert not calls["reference_called"]
    assert calls["permits_called"]
    assert len(answer.evidence_items) == 1
    assert answer.evidence_items[0].collection == Collection.PERMITS