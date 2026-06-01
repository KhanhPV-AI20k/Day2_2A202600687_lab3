from src.tools.calculator import calculator
from src.tools.ecommerce import check_stock, get_discount
from src.tools.search_tool import browse_url, search_web


TOOLS = [
    {
        "name": "calculator",
        "description": "Calculate ecommerce totals or discounts. Input example: 1000 * 0.9.",
        "function": calculator,
    },
    {
        "name": "check_stock",
        "description": "Check product stock. Input is a product name, for example: iphone.",
        "function": check_stock,
    },
    {
        "name": "get_discount",
        "description": "Get discount percentage from a coupon code. Input example: WINNER.",
        "function": get_discount,
    },
    {
        "name": "search_web",
        "description": "Search ecommerce demo products. Input is a product query, for example: iphone price.",
        "function": search_web,
    },
    {
        "name": "browse_url",
        "description": "Browse ecommerce demo product pages. Input is a product URL, for example: https://shop.example.com/iphone.",
        "function": browse_url,
    },
]
