# Changelog

This project follows [Semantic Versioning](https://semver.org).

## 0.1.2 (2026-10-06)

- README and `examples/item_details.py`: the item tutorial picks a listing whose details are
  ready, instead of the newest sale, whose details can still be a few minutes away.

## 0.1.1 (2026-10-06)

- README: the item tutorial takes its `item_id` from a search instead of a placeholder id.
- A rate-limited request waits the API's `Retry-After` plus a little jitter, so concurrent
  callers do not retry at the same instant.

## 0.1.0 (2026-10-06)

- First release: `Trawl` and `AsyncTrawl` clients with `ebay.sold`, `ebay.item` and
  `ebay.categories`, typed responses, typed errors and automatic retries.
