"""Handle the API's errors and keep track of credits.

export TRAWL_API_KEY=sk_live_...
python examples/errors_and_credits.py
"""

import trawl_api
from trawl_api import Trawl

client = Trawl(max_retries=3, timeout=30)

try:
    sold = client.ebay.sold("rolex submariner", min_price=2000, max_pages=3)
except trawl_api.BadRequestError as error:
    # A parameter failed validation; the message names the field and the rule.
    print(f"Bad request: {error}")
except trawl_api.AuthenticationError:
    print("The API key is missing, invalid or deleted.")
except trawl_api.InsufficientCreditsError as error:
    # The month's credits are spent, or too few remain for this max_pages.
    print(f"Not enough credits: {error}")
except trawl_api.RateLimitError as error:
    # Raised only after the client's own retries; wait this long and try again.
    print(f"Rate limited, retry in {error.retry_after}s")
except trawl_api.APIConnectionError:
    print("Could not reach the API.")
except trawl_api.APIStatusError as error:
    print(f"The API answered {error.status_code}: {error}")
else:
    print(f"{sold.count} results for {sold.credits_charged} credit(s)")
    if sold.rate_limit:
        print(f"{sold.rate_limit.remaining} of {sold.rate_limit.limit} credits left")
        print(f"The allowance resets on {sold.rate_limit.reset:%Y-%m-%d}")
