from ui.rag_status import (
    ASK_ASSISTANT_RAG_GUIDANCE,
    ASK_ASSISTANT_RAG_NOTICE,
)


def test_ask_assistant_rag_notice_sets_correct_expectation():
    assert "Ask Assistant requires a populated RAG index" in ASK_ASSISTANT_RAG_NOTICE
    assert "Review Document" in ASK_ASSISTANT_RAG_NOTICE
    assert "Review Package" in ASK_ASSISTANT_RAG_NOTICE
    assert "current demo" in ASK_ASSISTANT_RAG_NOTICE


def test_ask_assistant_rag_guidance_points_to_deterministic_workflows():
    assert "retrieval-augmented Q&A" in ASK_ASSISTANT_RAG_GUIDANCE
    assert "no RAG index has been built" in ASK_ASSISTANT_RAG_GUIDANCE
    assert "deterministic checklist review" in ASK_ASSISTANT_RAG_GUIDANCE
    assert "regulatory citations" in ASK_ASSISTANT_RAG_GUIDANCE
    assert "reviewer confirmations" in ASK_ASSISTANT_RAG_GUIDANCE