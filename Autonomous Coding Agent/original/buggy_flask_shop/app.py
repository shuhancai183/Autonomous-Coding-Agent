from flask import Flask, jsonify, request

from store import add_to_cart, calculate_total, checkout, get_cart_items, list_products

app = Flask(__name__)


@app.get('/health')
def health():
    return jsonify({"status": "ok"}), 200


@app.get('/products')
def products():
    return jsonify({"products": list_products()}), 200


@app.post('/cart/add')
def cart_add():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if product_id is None or quantity is None:
        return jsonify({"error": "product_id and quantity are required"}), 400

    try:
        ok, message = add_to_cart(int(product_id), int(quantity))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid payload types"}), 400

    if not ok:
        return jsonify({"error": message}), 400

    return jsonify({"message": message}), 200


@app.get('/cart')
def cart_view():
    items = get_cart_items()
    return jsonify({"items": items, "total": calculate_total()}), 200


@app.post('/checkout')
def checkout_route():
    data = request.get_json(silent=True) or {}
    coupon = data.get("coupon")

    ok, message, total = checkout(coupon)
    if not ok:
        return jsonify({"error": message}), 400

    return jsonify({"message": message, "total": total}), 200


if __name__ == '__main__':
    app.run(debug=True)
