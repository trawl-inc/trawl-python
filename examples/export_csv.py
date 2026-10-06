"""Export sold listings to a CSV file.

export TRAWL_API_KEY=sk_live_...
python examples/export_csv.py "charizard base set holo" sold.csv
"""

import csv
import sys

from trawl_api import Trawl

query = sys.argv[1] if len(sys.argv) > 1 else "charizard base set holo"
path = sys.argv[2] if len(sys.argv) > 2 else "sold.csv"

COLUMNS = [
    "date_sold",
    "title",
    "sale_price",
    "shipping_price",
    "currency",
    "condition",
    "buying_format",
    "bids",
    "location",
    "item_id",
    "item_link",
]

client = Trawl()
sold = client.ebay.sold(query, max_pages=10)  # up to 1,000 sales, and at most 10 credits

with open(path, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=COLUMNS)
    writer.writeheader()
    for listing in sold.results:
        writer.writerow(listing.model_dump(mode="json", include=set(COLUMNS)))

print(f"Wrote {sold.count} sales to {path} ({sold.credits_charged} credit(s) charged)")

# With pandas instead:
#   import pandas as pd
#   frame = pd.DataFrame(listing.model_dump() for listing in sold.results)
