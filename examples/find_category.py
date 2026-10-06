"""Find an eBay category id by name, then search inside it.

export TRAWL_API_KEY=sk_live_...
python examples/find_category.py "trading card singles" "charizard"
"""

import sys

from trawl_api import Trawl

category_query = sys.argv[1] if len(sys.argv) > 1 else "trading card singles"
query = sys.argv[2] if len(sys.argv) > 2 else "charizard"

client = Trawl()

# Category ids differ per marketplace: look them up on the one you will search.
found = client.ebay.categories(category_query, site="EBAY_US")
if not found.categories:
    sys.exit(f"No category matches {category_query!r}.")

for category in found.categories:
    print(f"{category.category_id:>8}  {category.name}  ({category.group})")

best = found.categories[0]
sold = client.ebay.sold(query, category=best.category_id, site="EBAY_US")
print(f"\n{sold.count} sales of {query!r} in {best.name}:")
for listing in sold.results[:10]:
    print(f"  {listing.currency}{listing.sale_price:>9.2f}  {listing.title}")
