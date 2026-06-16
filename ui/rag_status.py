"""User-facing status copy for the Ask Assistant / RAG workflow."""

from __future__ import annotations


ASK_ASSISTANT_RAG_NOTICE = (
    "Ask Assistant requires a populated RAG index before it should be used "
    "for evidence-backed Q&A. The deterministic Review Document and Review "
    "Package workflows are active and should be used for the current demo."
)


ASK_ASSISTANT_RAG_GUIDANCE = (
    "The Ask Assistant tab is designed for retrieval-augmented Q&A over "
    "indexed reference materials and permit precedents. If no RAG index has "
    "been built, answers may be empty or incomplete. Use the Review Document "
    "and Review Package tabs for deterministic checklist review, evidence "
    "locations, regulatory citations, reviewer confirmations, and exports."
)