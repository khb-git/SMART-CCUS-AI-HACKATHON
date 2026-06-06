from rag.types import Collection


def test_classify_query_intent_routes_requirements_to_reference():
    from rag.query_intent import QueryIntent, classify_query_intent

    route = classify_query_intent(
        "What does Class VI require for testing and monitoring?"
    )

    assert route.intent == QueryIntent.REGULATORY_REQUIREMENT
    assert route.collections == [Collection.REFERENCE]
    assert route.uses_reference()
    assert not route.uses_permits()


def test_classify_query_intent_routes_applicant_examples_to_permits():
    from rag.query_intent import QueryIntent, classify_query_intent

    route = classify_query_intent(
        "How do applicants monitor injection pressure and flow rate?"
    )

    assert route.intent == QueryIntent.PERMIT_PRECEDENT
    assert route.collections == [Collection.PERMITS]
    assert route.uses_permits()
    assert not route.uses_reference()


def test_classify_query_intent_routes_comparison_to_both():
    from rag.query_intent import QueryIntent, classify_query_intent

    route = classify_query_intent(
        "Compare the applicant monitoring plan against EPA requirements."
    )

    assert route.intent == QueryIntent.CROSS_CHECK
    assert route.collections == [Collection.REFERENCE, Collection.PERMITS]
    assert route.uses_reference()
    assert route.uses_permits()


def test_classify_query_intent_defaults_to_general_review():
    from rag.query_intent import QueryIntent, classify_query_intent

    route = classify_query_intent("Tell me about pressure monitoring.")

    assert route.intent == QueryIntent.GENERAL_REVIEW
    assert route.collections == [Collection.REFERENCE, Collection.PERMITS]