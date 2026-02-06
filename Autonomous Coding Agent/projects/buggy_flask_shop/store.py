from copy import deepcopy

INITIAL_PRODUCTS = {
    1: {"name": "Laptop", "price": 1200.0, "stock": 5},
    2: {"name": "Mouse", "price": 25.0, "stock": 20},
    3: {"name": "Keyboard", "price": 75.0, "stock": 10},
}

PRODUCTS = deepcopy(INITIAL_PRODUCTS)
CART = {}


def reset_state():
    PRODUCTS.clear()
    PRODUCTS.update(deepcopy(INITIAL_PRODUCTS))
    CART.clear()


def list_products():
    return [
        {
            "id": product_id,
            "name": data["name"],
            "price": data["price"],
            "stock": data["stock"],
        }
        for product_id, data in PRODUCTS.items()
    ]


def add_to_cart(product_id: int, quantity: int):
    if quantity <= 0:
        return False, "Quantity must be positive"

    product = PRODUCTS.get(product_id)
    if not product:
        return False, "Product not found"

    if quantity > product["stock"]:
        return False, "Not enough stock"

    CART[product_id] = CART.get(product_id, 0) + quantity
    return True, "Added"


def get_cart_items():
    items = []
    for product_id, quantity in CART.items():
        p = PRODUCTS[product_id]
        subtotal = p["price"] * quantity
        items.append(
            {
                "product_id": product_id,
                "name": p["name"],
                "price": p["price"],
                "quantity": quantity,
                "subtotal": round(subtotal, 2),
            }
        )
    return items


def calculate_total(coupon: str | None = None):
    subtotal = sum(item["subtotal"] for item in get_cart_items())

    # Apply coupon discount as 10% off if coupon is SAVE10
    if coupon == "SAVE10":
        subtotal *= 0.9  # 10% discount

    # Apply 8% tax
    total = subtotal * 1.08

    return round(total, 2)


def checkout(coupon: str | None = None):
    if not CART:
        return False, "Cart is empty", None

    # Check stock availability before checkout
    for product_id, quantity in CART.items():
        if quantity > PRODUCTS[product_id]["stock"]:
            return False, f"Not enough stock for product {product_id}", None

    total = calculate_total(coupon)

    for product_id, quantity in CART.items():
        PRODUCTS[product_id]["stock"] -= quantity

    CART.clear()

    return True, "Order placed", total
