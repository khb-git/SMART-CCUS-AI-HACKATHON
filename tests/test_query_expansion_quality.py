def test_query_expansion_strengthens_annular_pressure_query():
    from rag.query_expansion import expand_query

    expanded = expand_query(
        "How do applicants monitor annular pressure?",
        enabled=True,
    ).lower()

    assert "annular pressure" in expanded
    assert "annulus pressure" in expanded
    assert "annulus" in expanded
    assert "monitoring" in expanded


def test_query_expansion_strengthens_plume_pressure_front_query():
    from rag.query_expansion import expand_query

    expanded = expand_query(
        "How do applicants track plume and pressure front movement?",
        enabled=True,
    ).lower()

    assert "plume" in expanded
    assert "pressure front" in expanded
    assert "monitoring" in expanded
    assert any(
        term in expanded
        for term in [
            "computational modeling",
            "subsurface monitoring",
            "area of review",
            "aor",
        ]
    )


def test_query_expansion_strengthens_pisc_site_closure_query():
    from rag.query_expansion import expand_query

    expanded = expand_query(
        "How do applicants describe post-injection site care and site closure?",
        enabled=True,
    ).lower()

    assert "post-injection site care" in expanded
    assert "site closure" in expanded
    assert "pisc" in expanded
    assert "non-endangerment" in expanded


def test_query_expansion_strengthens_financial_responsibility_query():
    from rag.query_expansion import expand_query

    expanded = expand_query(
        "How do applicants demonstrate financial responsibility?",
        enabled=True,
    ).lower()

    assert "financial responsibility" in expanded
    assert "financial assurance" in expanded
    assert "cost estimate" in expanded
    assert any(
        term in expanded
        for term in [
            "letter of credit",
            "surety bond",
            "financial instrument",
            "coverage amount",
        ]
    )


def test_query_expansion_strengthens_well_construction_query():
    from rag.query_expansion import expand_query

    expanded = expand_query(
        "What should be included in a well construction plan?",
        enabled=True,
    ).lower()

    assert "well construction" in expanded
    assert "casing" in expanded
    assert "cement" in expanded
    assert "tubing" in expanded
    assert "packer" in expanded


def test_phrase_expansion_handles_hyphen_normalization():
    from rag.query_expansion import get_query_expansion_terms

    terms = get_query_expansion_terms(
        "How is post-injection site care handled?"
    )

    assert "PISC" in terms
    assert "site closure" in terms
    assert "non-endangerment demonstration" in terms