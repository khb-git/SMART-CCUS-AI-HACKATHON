from api.main import app


def route_exists(path: str, method: str) -> bool:
    return any(
        getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
        for route in app.routes
    )


def test_review_package_route_is_registered_once():
    matching_routes = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/review-package"
        and "POST" in getattr(route, "methods", set())
    ]

    assert len(matching_routes) == 1


def test_expected_api_routes_are_registered():
    assert route_exists("/health", "GET")
    assert route_exists("/ask", "POST")
    assert route_exists("/review-document", "POST")
    assert route_exists("/review-package", "POST")
    assert route_exists("/demo/maip-package", "GET")
    assert route_exists("/demo/maip-package/report", "GET")
    assert route_exists("/demo/maip-package/final-packet", "GET")