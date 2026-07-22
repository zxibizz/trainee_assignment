"""Product listing, filtering, and pagination."""


def test_list_returns_seeded_products(auth_client):
    resp = auth_client.get("/products", params={"limit": 200})
    assert resp.status_code == 200
    body = resp.json()
    products = body["items"]
    assert len(products) == 15
    assert set(products[0]) == {
        "id",
        "name",
        "section",
        "description",
        "discount",
        "price",
    }
    assert body["pagination"] == {
        "limit": 200,
        "offset": 0,
        "count": 15,
        "total": 15,
    }


def test_filter_by_section(auth_client):
    resp = auth_client.get("/products", params={"section": "books"})
    products = resp.json()["items"]
    assert len(products) == 3
    assert all(p["section"] == "books" for p in products)


def test_filter_by_name_substring_is_case_insensitive(auth_client):
    resp = auth_client.get("/products", params={"name": "CODE"})
    names = {p["name"] for p in resp.json()["items"]}
    assert "Clean Code" in names


def test_filter_by_price_range(auth_client):
    resp = auth_client.get("/products", params={"min_price": 50, "max_price": 100})
    products = resp.json()["items"]
    assert products
    assert all(50 <= p["price"] <= 100 for p in products)


def test_rejects_inverted_price_range(auth_client):
    resp = auth_client.get("/products", params={"min_price": 100, "max_price": 50})
    assert resp.status_code == 400


def test_filter_has_discount_true(auth_client):
    resp = auth_client.get("/products", params={"has_discount": "true", "limit": 200})
    products = resp.json()["items"]
    assert products
    assert all(p["discount"] > 0 for p in products)


def test_filter_has_discount_false(auth_client):
    resp = auth_client.get("/products", params={"has_discount": "false", "limit": 200})
    assert all(p["discount"] == 0 for p in resp.json()["items"])


def test_pagination_limit_and_offset(auth_client):
    first = auth_client.get("/products", params={"limit": 5, "offset": 0}).json()
    second = auth_client.get("/products", params={"limit": 5, "offset": 5}).json()
    assert len(first["items"]) == 5
    assert len(second["items"]) == 5
    assert first["pagination"] == {"limit": 5, "offset": 0, "count": 5, "total": 15}
    assert second["pagination"] == {"limit": 5, "offset": 5, "count": 5, "total": 15}
    first_ids = {p["id"] for p in first["items"]}
    second_ids = {p["id"] for p in second["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_pagination_rejects_out_of_range_limit(auth_client):
    assert auth_client.get("/products", params={"limit": 0}).status_code == 422
    assert auth_client.get("/products", params={"limit": 500}).status_code == 422


def test_pagination_rejects_negative_offset(auth_client):
    assert auth_client.get("/products", params={"offset": -1}).status_code == 422
