PRODUCTS = {
    "iphone": {"price": 1000, "stock": 5, "weight": 0.5},
    "macbook": {"price": 2000, "stock": 2, "weight": 1.5},
}

DISCOUNTS = {
    "WINNER": 10,
    "STUDENT": 15,
}


def check_stock(item_name: str) -> str:
    item = item_name.lower().strip()

    if item not in PRODUCTS:
        return f"{item_name} is not found."

    stock = PRODUCTS[item]["stock"]
    return f"{item} has {stock} items in stock."


def get_discount(coupon_code: str) -> str:
    code = coupon_code.strip().upper()

    if code not in DISCOUNTS:
        return "Discount is 0%."

    return f"Discount is {DISCOUNTS[code]}%."
