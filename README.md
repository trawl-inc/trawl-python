# trawl-api: Python eBay scraper API for sold listings and prices

[![PyPI](https://img.shields.io/pypi/v/trawl-api)](https://pypi.org/project/trawl-api/)
[![Python](https://img.shields.io/pypi/pyversions/trawl-api)](https://pypi.org/project/trawl-api/)

The official Python client for [trawl](https://trawl.dev), a data API for eBay. Search 300+
million completed eBay sales on the US and UK marketplaces and get each one back as typed
Python objects: final price, sale date, condition, shipping, seller, item specifics, images
and description. One API key, no proxies, no HTML parsing, no browser to run.

```bash
pip install trawl-api
```

Requires Python 3.10 or newer. [Create a free account](https://trawl.dev/signup) to get an
API key; the free plan needs no card.

## Quickstart

```python
from trawl_api import Trawl

client = Trawl()  # reads the TRAWL_API_KEY environment variable

sold = client.ebay.sold("iphone 15 pro 256gb", condition="used")

for listing in sold.results[:5]:
    print(listing.date_sold.date(), listing.sale_price, listing.title)

print(f"{sold.count} results, {sold.credits_charged} credit(s) charged")
```

The key can also be passed directly: `Trawl(api_key="sk_live_...")`. Keep it on your server
and out of source control.

## What you can ask

| Method | Answers | Costs |
|---|---|---|
| `client.ebay.sold(query, ...)` | Sold listings matching a query, newest first, up to 2,000 in one response | 1 credit per page of 100 results (2 with `details=True`); free when nothing matches |
| `client.ebay.item(item_id)` | One sold listing in full: specifics, seller, every image, description, recorded sales | 1 credit |
| `client.ebay.categories(query)` | eBay categories by name or id, for the `category` filter | 1 credit; free when nothing matches |

The full parameter and field reference is at [trawl.dev/docs](https://trawl.dev/docs).

## Tutorials

Each of these is a complete script in
[`examples/`](https://github.com/trawl-inc/trawl-python/tree/main/examples).

### Get the sold prices of a product

```python
from trawl_api import Trawl

client = Trawl()
sold = client.ebay.sold(
    "iphone 15 pro 256gb",
    condition="used",
    exclude=["case", "cracked"],  # words that must not be in the title
)

for listing in sold.results:
    print(
        f"{listing.date_sold:%Y-%m-%d}  {listing.currency}{listing.sale_price:.2f}  {listing.title}"
    )
```

### Average sold price over the last 90 days

`max_pages` sets how many pages of 100 results come back in the one response, and is also the
most credits the call can cost.

```python
from datetime import date, timedelta
from statistics import mean, median

from trawl_api import Trawl

client = Trawl()
sold = client.ebay.sold(
    "nintendo switch oled",
    condition="used",
    date_from=date.today() - timedelta(days=90),
    max_pages=5,
)

prices = [listing.sale_price for listing in sold.results]
print(
    f"{len(prices)} sales, average {mean(prices):.2f}, median {median(prices):.2f} {sold.currency}"
)
```

### Filter by price, marketplace and item specifics

```python
sold = client.ebay.sold(
    "charizard",
    site="EBAY_GB",  # ebay.co.uk; prices are then in GBP
    min_price=100,
    max_price=2000,
    attr={"Set": "Base Set", "Grade": ["9", "10"]},  # Grade 9 or 10, from Base Set
)
```

### Export sold listings to CSV or pandas

```python
import csv

from trawl_api import Trawl

COLUMNS = ["date_sold", "title", "sale_price", "currency", "condition", "item_id", "item_link"]

client = Trawl()
sold = client.ebay.sold("charizard base set holo", max_pages=10)

with open("sold.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=COLUMNS)
    writer.writeheader()
    for listing in sold.results:
        writer.writerow(listing.model_dump(mode="json", include=set(COLUMNS)))
```

For pandas: `pd.DataFrame(listing.model_dump() for listing in sold.results)`.

### Get one listing's full details

```python
from trawl_api import NotFoundError, Trawl

client = Trawl()

# The item_id of any sold() result; here, the newest sale of a search.
item_id = client.ebay.sold("iphone 15 pro 256gb").results[0].item_id

try:
    item = client.ebay.item(item_id)
except NotFoundError:
    # Details arrive a few minutes after a sale. A 404 is never billed.
    raise SystemExit("Details are not available yet.")

print(item.title, item.sale_price, item.currency)
print(item.specifics.get("Brand"))  # item specifics as a dict
if item.seller:
    print(item.seller.username, item.seller.feedback_percent)
print(len(item.images), "images")
```

To get the details of every result of a search in one call, pass `details=True` to `sold()`
and read `listing.details`.

### Find a category and search inside it

```python
found = client.ebay.categories("trading card singles", site="EBAY_US")
for category in found.categories:
    print(category.category_id, category.name, category.group)

sold = client.ebay.sold("charizard", category=found.categories[0].category_id)
```

Category ids differ per marketplace, so look them up with the same `site` you search with.

## Credits

Every answer says what it cost, and how much of the month's allowance is left:

```python
sold = client.ebay.sold("rolex submariner", max_pages=3)

sold.credits_charged  # 3 when three pages came back, 0 when nothing matched
sold.rate_limit.remaining  # credits left in this billing window
sold.rate_limit.reset  # when the allowance resets
```

Errors are never billed.

## Errors

```python
import trawl_api

try:
    sold = client.ebay.sold("rolex submariner", min_price=2000)
except trawl_api.BadRequestError as error:
    print(error)  # the API names the field and the rule it broke
except trawl_api.InsufficientCreditsError as error:
    print(error)  # the month's credits are spent, or too few remain
except trawl_api.RateLimitError as error:
    print(error.retry_after)  # seconds to wait
except trawl_api.APIStatusError as error:
    print(error.status_code, error)
```

| Exception | When |
|---|---|
| `BadRequestError` | 400, a parameter failed validation |
| `AuthenticationError` | 403, the key is missing, invalid or deleted |
| `NotFoundError` | 404, e.g. an item whose details are not available yet |
| `RateLimitError` | 429 with `Retry-After`, the plan's per-second rate was exceeded |
| `InsufficientCreditsError` | 429 without `Retry-After`, not enough credits for the request |
| `ServerError` | 5xx, a failure on trawl's side |
| `APIConnectionError`, `APITimeoutError` | the request got no answer |

All of them inherit from `trawl_api.TrawlError`. Connection errors, 5xx answers and
per-second rate limits are retried twice with backoff before they are raised; change that
with `Trawl(max_retries=...)`. The per-second rate belongs to the account, so keep concurrent
calls within [your plan's rate](https://trawl.dev/docs#plans).

## Async

```python
import asyncio

from trawl_api import AsyncTrawl


async def main():
    async with AsyncTrawl() as client:
        sold = await client.ebay.sold("iphone 15 pro 256gb")
        print(sold.count)


asyncio.run(main())
```

## Configuration

```python
client = Trawl(
    api_key="sk_live_...",  # default: the TRAWL_API_KEY environment variable
    timeout=60.0,  # seconds
    max_retries=2,
)
```

Responses are [pydantic](https://docs.pydantic.dev) models: `model_dump()` gives a dict,
`model_dump_json()` a JSON string, and fields the API adds later are kept on the object.

## Links

- [Documentation](https://trawl.dev/docs)
- [Pricing](https://trawl.dev/pricing)
- [Changelog](https://github.com/trawl-inc/trawl-python/blob/main/CHANGELOG.md)

trawl is an independent service and is not affiliated with or endorsed by eBay Inc.
