"""The API's documented sample answers (trawl.dev/docs)."""

SOLD = {
    "site": "EBAY_US",
    "currency": "USD",
    "query": ["iphone", "13", "pro"],
    "filters": {"condition": ["used"]},
    "max_pages": 5,
    "count": 385,
    "credits_charged": 4,
    "took_ms": 41,
    "results": [
        {
            "title": "Apple iPhone 13 Pro 256GB Graphite Unlocked",
            "sale_price": 525.00,
            "shipping_price": 0,
            "currency": "$",
            "condition": "used",
            "condition_raw": "Pre-Owned",
            "date_sold": "2026-07-18T00:00:00.000Z",
            "buying_format": "Buy It Now",
            "bids": None,
            "best_offer_available": True,
            "location": "United States",
            "item_id": "256637082114",
            "epid": "13051890211",
            "categoryId": "9355",
            "item_link": "https://www.ebay.com/itm/256637082114",
            "image_url": "https://i.ebayimg.com/images/g/abc/s-l500.webp",
        },
    ],
}

ITEM = {
    "site": "EBAY_US",
    "item_id": "256637082114",
    "title": "Apple iPhone 13 Pro 256GB Graphite Unlocked",
    "condition": "used",
    "condition_raw": "Pre-Owned",
    "condition_description": "Light scratches on the frame, screen flawless.",
    "grading": None,
    "listing_state": "sold",
    "sold_at": "2026-07-18T21:14:00.000Z",
    "last_updated": None,
    "sale_price": 525.00,
    "currency": "US$",
    "buying_format": "Buy It Now",
    "bids": None,
    "best_offer_available": True,
    "best_offer_accepted": False,
    "shipping_service": "USPS Ground Advantage",
    "returns_text": "30 days returns. Buyer pays for return shipping.",
    "seller_accepts_returns": True,
    "location": "Austin, Texas",
    "location_country": "United States",
    "epid": "13051890211",
    "categoryId": "9355",
    "item_link": "https://www.ebay.com/itm/256637082114",
    "images": [
        "https://i.ebayimg.com/images/g/abc/s-l1600.webp",
        "https://i.ebayimg.com/images/g/def/s-l1600.webp",
    ],
    "attributes": [
        {"key": "Brand", "value": "Apple", "values": ["Apple"]},
        {"key": "Model", "value": "Apple iPhone 13 Pro", "values": ["Apple iPhone 13 Pro"]},
        {"key": "Storage Capacity", "value": "256 GB", "values": ["256 GB"]},
        {"key": "Network", "value": "Unlocked", "values": ["Unlocked"]},
    ],
    "description_url": "https://itm.ebaydesc.com/itmdesc/256637082114",
    "description_text": "Fully unlocked, battery health 91%. Comes with the original box.",
    "seller": {
        "username": "phone-depot",
        "feedback_percent": 99.6,
        "feedback_count": 6864,
        "items_sold": 12480,
    },
    "feedback": [
        {
            "username": "b***y",
            "rating": "positive",
            "comment": "Exactly as described, fast shipping",
            "age_text": "Past month",
        },
    ],
    "sales": [
        {
            "date_sold": "2026-07-18T00:00:00.000Z",
            "sale_price": 525.00,
            "shipping_price": 0,
            "currency": "$",
            "condition": "Pre-Owned",
        },
    ],
    "credits_charged": 1,
}

REMOVED_ITEM = {"site": "EBAY_US", "item_id": "256637082114", "listing_state": "removed"}

CATEGORIES = {
    "site": "EBAY_US",
    "total": 38,
    "count": 2,
    "categories": [
        {
            "categoryId": "261328",
            "name": "Trading Card Singles",
            "group": "Sports Mem, Cards & Fan Shop",
        },
        {"categoryId": "183050", "name": "Trading Card Singles", "group": "Collectibles"},
    ],
    "credits_charged": 1,
}
