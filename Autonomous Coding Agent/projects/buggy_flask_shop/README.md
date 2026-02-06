# Buggy Flask Shop (Practice Project)

This is a small online shopping Flask app intentionally containing multiple bugs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run app

```bash
python app.py
```

## Run tests

```bash
pytest -q
```

Some tests should fail at first. Your goal is to fix the app until all tests pass.

## API

- `GET /health`
- `GET /products`
- `POST /cart/add` with JSON `{ "product_id": 1, "quantity": 2 }`
- `GET /cart`
- `POST /checkout` with JSON `{ "coupon": "SAVE10" }`
