import pytest

from app import app
from store import PRODUCTS, reset_state


@pytest.fixture
def client():
    reset_state()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_products_list(client):
    resp = client.get('/products')
    assert resp.status_code == 200
    body = resp.get_json()
    assert "products" in body
    assert len(body["products"]) == 3


def test_add_to_cart_allows_buying_exact_stock(client):
    resp = client.post('/cart/add', json={"product_id": 1, "quantity": 5})
    assert resp.status_code == 200


def test_cart_subtotal_uses_price_times_quantity(client):
    client.post('/cart/add', json={"product_id": 2, "quantity": 3})
    resp = client.get('/cart')
    body = resp.get_json()

    assert resp.status_code == 200
    assert body["items"][0]["subtotal"] == 75.0


def test_checkout_applies_save10_as_percent_and_8pct_tax(client):
    client.post('/cart/add', json={"product_id": 3, "quantity": 2})
    resp = client.post('/checkout', json={"coupon": "SAVE10"})
    body = resp.get_json()

    assert resp.status_code == 200
    # subtotal = 150
    # discount 10% => 135
    # tax 8% => 145.8
    assert body["total"] == 145.8


def test_checkout_clears_cart_and_updates_stock(client):
    client.post('/cart/add', json={"product_id": 2, "quantity": 4})
    resp = client.post('/checkout', json={})
    assert resp.status_code == 200

    cart_resp = client.get('/cart')
    cart_body = cart_resp.get_json()
    assert cart_body["items"] == []

    # Mouse stock should go from 20 -> 16
    assert PRODUCTS[2]["stock"] == 16


def test_invalid_quantity_rejected(client):
    resp = client.post('/cart/add', json={"product_id": 1, "quantity": 0})
    assert resp.status_code == 400
