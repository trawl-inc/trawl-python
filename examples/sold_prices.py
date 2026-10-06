"""Print the latest sold prices for a product.

export TRAWL_API_KEY=sk_live_...
python examples/sold_prices.py "iphone 15 pro 256gb"
"""

import sys

from trawl_api import Trawl

query = sys.argv[1] if len(sys.argv) > 1 else "iphone 15 pro 256gb"

client = Trawl()
sold = client.ebay.sold(query, condition="used", exclude=["case", "cracked"])

for listing in sold.results[:20]:
    price = f"{listing.currency}{listing.sale_price:.2f}"
    print(f"{listing.date_sold:%Y-%m-%d}  {price:>10}  {listing.title}")

print(f"\n{sold.count} results, {sold.credits_charged} credit(s) charged")
