from src.tools.calculator import calculator
from src.tools.search_tool import browse_url, extract_product_info, search_web


TOOLS = [
    {
        "name": "calculator",
        "description": "Calculate ecommerce totals or discounts. Input example: 1000 * 0.9.",
        "function": calculator,
    },
    {
        "name": "search_web",
        "description": "Search the live web with Tavily for ecommerce product information. Input is a product query, for example: iphone price.",
        "function": search_web,
    },
    {
        "name": "browse_url",
        "description": "Extract page content with Tavily. Input is a product URL from search results.",
        "function": browse_url,
    },
    {
        "name": "extract_product_info",
        "description": "Extract product title, price, and availability from a product URL using Tavily.",
        "function": extract_product_info,
    },
]
