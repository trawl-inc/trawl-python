"""Fetch one sold listing in full: specifics, seller, images, description.

export TRAWL_API_KEY=sk_live_...
python examples/item_details.py 256637082114
"""

import sys

from trawl_api import NotFoundError, Trawl

client = Trawl()

if len(sys.argv) > 1:
    item_id = sys.argv[1]
else:
    # No id given: take the newest sale of a search.
    item_id = client.ebay.sold("iphone 15 pro 256gb").results[0].item_id

try:
    item = client.ebay.item(item_id)
except NotFoundError:
    # Details arrive a few minutes after a sale. A 404 is never billed.
    sys.exit(f"Details for {item_id} are not available yet.")

if item.is_removed:
    sys.exit(f"eBay has removed listing {item_id}.")

print(item.title)
print(f"  state     {item.listing_state}")
if item.sale_price is not None:
    print(f"  price     {item.currency}{item.sale_price:.2f}")
print(f"  condition {item.condition_raw}")
print(f"  location  {item.location}")
if item.seller:
    print(f"  seller    {item.seller.username} ({item.seller.feedback_percent}% positive)")
print(f"  images    {len(item.images)}")
for key, value in item.specifics.items():
    print(f"  {key}: {value}")
