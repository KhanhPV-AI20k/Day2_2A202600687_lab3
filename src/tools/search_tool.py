SEARCH_DATA = {
    "iphone": "Search result: iphone, demo price $1000, product page https://shop.example.com/iphone.",
    "iphone price": "Search result: iphone, demo price $1000, product page https://shop.example.com/iphone.",
    "macbook": "Search result: macbook, demo price $2000, product page https://shop.example.com/macbook.",
    "macbook price": "Search result: macbook, demo price $2000, product page https://shop.example.com/macbook.",
}

BROWSE_DATA = {
    "https://shop.example.com/iphone": "Product page: iphone, demo price $1000, in stock.",
    "https://shop.example.com/macbook": "Product page: macbook, demo price $2000, in stock.",
}


def search_web(query: str) -> str:
    query = query.lower().strip()

    for keyword, result in SEARCH_DATA.items():
        if keyword in query:
            return result

    return "No ecommerce search result found in demo data."


def browse_url(url: str) -> str:
    url = url.strip()

    if url in BROWSE_DATA:
        return BROWSE_DATA[url]

    return "No ecommerce page found in demo browse data."
