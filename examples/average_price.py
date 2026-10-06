"""Average and median sold price over the last 90 days.

export TRAWL_API_KEY=sk_live_...
python examples/average_price.py "nintendo switch oled"
"""

import sys
from datetime import date, timedelta
from statistics import mean, median

from trawl_api import Trawl

query = sys.argv[1] if len(sys.argv) > 1 else "nintendo switch oled"

client = Trawl()
sold = client.ebay.sold(
    query,
    condition="used",
    date_from=date.today() - timedelta(days=90),
    max_pages=5,  # up to 500 sales, and at most 5 credits
)

prices = [listing.sale_price for listing in sold.results]
if not prices:
    sys.exit(f"No sales of {query!r} in the last 90 days.")

print(f"{query}: {len(prices)} sales in the last 90 days ({sold.currency})")
print(f"  average {mean(prices):.2f}")
print(f"  median  {median(prices):.2f}")
print(f"  range   {min(prices):.2f} to {max(prices):.2f}")
print(f"{sold.credits_charged} credit(s) charged")
