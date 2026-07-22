"""Product create, read, update, delete, and batch update."""


def test_get_product_by_id(auth_client):
    resp = auth_client.get("/products/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_get_missing_product_returns_404(auth_client):
    assert auth_client.get("/products/9999").status_code == 404


def test_create_product(auth_client):
    payload = {
        "name": "Test Widget",
        "section": "misc",
        "description": "a widget",
        "discount": 5,
        "price": 9.99,
    }
    resp = auth_client.post("/products", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"]
    assert created["name"] == "Test Widget"

    fetched = auth_client.get(f"/products/{created['id']}").json()
    assert fetched["price"] == 9.99


def test_create_product_rejects_invalid_discount(auth_client):
    resp = auth_client.post(
        "/products",
        json={"name": "Bad", "section": "misc", "price": 1, "discount": 150},
    )
    assert resp.status_code == 422


def test_create_product_rejects_negative_price(auth_client):
    resp = auth_client.post(
        "/products",
        json={"name": "Bad", "section": "misc", "price": -1},
    )
    assert resp.status_code == 422


def test_create_product_rejects_missing_price(auth_client):
    resp = auth_client.post(
        "/products",
        json={"name": "Bad", "section": "misc"},
    )
    assert resp.status_code == 422


def test_update_product_fields(auth_client):
    resp = auth_client.patch("/products/1", json={"discount": 33, "price": 19.5})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["discount"] == 33
    assert updated["price"] == 19.5

    fetched = auth_client.get("/products/1").json()
    assert fetched["discount"] == 33


def test_update_missing_product_returns_404(auth_client):
    assert auth_client.patch("/products/9999", json={"discount": 10}).status_code == 404


def test_delete_product(admin_client):
    assert admin_client.delete("/products/1").status_code == 204
    assert admin_client.get("/products/1").status_code == 404


def test_delete_missing_product_returns_404(admin_client):
    assert admin_client.delete("/products/9999").status_code == 404


def test_delete_product_forbidden_for_non_admin(auth_client):
    assert auth_client.delete("/products/1").status_code == 403
    # The product must still exist after a denied delete.
    assert auth_client.get("/products/1").status_code == 200
