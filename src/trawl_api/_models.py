from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


@dataclass(frozen=True)
class RateLimit:
    """The account's allowance, read from the response's X-RateLimit-* headers."""

    limit: int | None
    """Credits included in the plan per month."""
    remaining: int | None
    """Credits left in this billing window."""
    reset: datetime | None
    """When the window resets (the billing period's end)."""


def rate_limit_from_headers(headers: Mapping[str, str]) -> RateLimit | None:
    def number(name: str) -> int | None:
        try:
            return int(headers[name])
        except (KeyError, ValueError):
            return None

    limit = number("x-ratelimit-limit")
    remaining = number("x-ratelimit-remaining")
    reset_at = number("x-ratelimit-reset")
    if limit is None and remaining is None and reset_at is None:
        return None
    reset = None
    if reset_at is not None:
        # A Unix timestamp; read milliseconds as well as seconds.
        seconds = reset_at / 1000 if reset_at > 100_000_000_000 else reset_at
        reset = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return RateLimit(limit=limit, remaining=remaining, reset=reset)


class _Model(BaseModel):
    # extra="allow": a field the API adds later is kept on the object instead of
    # breaking every installed version of the package.
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class APIResponse(_Model):
    credits_charged: int = 0
    """Credits this call cost. 0 for a search that matched nothing."""

    _rate_limit: RateLimit | None = PrivateAttr(default=None)

    @property
    def rate_limit(self) -> RateLimit | None:
        """The account's allowance after this call, when the API sent it."""
        return self._rate_limit


class Grading(_Model):
    graded: bool | None = None
    grader: str | None = None
    grade: str | None = None
    condition: str | None = None


class Attribute(_Model):
    key: str
    value: str
    values: list[str] = Field(default_factory=list)


class Seller(_Model):
    username: str
    feedback_percent: float | None = None
    feedback_count: int | None = None
    items_sold: int | None = None


class Feedback(_Model):
    username: str | None = None
    rating: str | None = None
    comment: str | None = None
    age_text: str | None = None


class Sale(_Model):
    date_sold: datetime
    sale_price: float
    shipping_price: float | None = None
    currency: str | None = None
    condition: str | None = None


class Item(APIResponse):
    """One listing in full, as GET /item answers it.

    A listing eBay has removed carries only `site`, `item_id` and
    `listing_state == "removed"`; every other field is then empty.
    """

    site: str | None = None
    item_id: str | None = None
    title: str | None = None
    condition: str | None = None
    condition_raw: str | None = None
    condition_description: str | None = None
    grading: Grading | None = None
    listing_state: str | None = None
    sold_at: datetime | None = None
    last_updated: datetime | None = None
    sale_price: float | None = None
    currency: str | None = None
    buying_format: str | None = None
    bids: int | None = None
    best_offer_available: bool | None = None
    best_offer_accepted: bool | None = None
    shipping_service: str | None = None
    returns_text: str | None = None
    seller_accepts_returns: bool | None = None
    location: str | None = None
    location_country: str | None = None
    epid: str | None = None
    category_id: str | None = Field(default=None, alias="categoryId")
    item_link: str | None = None
    images: list[str] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    description_url: str | None = None
    description_text: str | None = None
    seller: Seller | None = None
    feedback: list[Feedback] = Field(default_factory=list)
    sales: list[Sale] = Field(default_factory=list)

    @property
    def is_removed(self) -> bool:
        return self.listing_state == "removed"

    @property
    def specifics(self) -> dict[str, str]:
        """The item specifics as a dict: `item.specifics["Brand"]`."""
        return {attribute.key: attribute.value for attribute in self.attributes}


class SoldListing(_Model):
    title: str
    sale_price: float
    shipping_price: float | None = None
    currency: str | None = None
    condition: str | None = None
    condition_raw: str | None = None
    date_sold: datetime
    buying_format: str | None = None
    bids: int | None = None
    best_offer_available: bool | None = None
    location: str | None = None
    item_id: str
    epid: str | None = None
    category_id: str | None = Field(default=None, alias="categoryId")
    item_link: str | None = None
    image_url: str | None = None
    details: Item | None = None
    """The listing's full /item data. Only with `details=True`."""
    listing_state: str | None = None
    """"removed" when eBay has taken the listing down. Only with `details=True`."""


class SoldResponse(APIResponse):
    site: str
    currency: str | None = None
    query: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    max_pages: int | None = None
    count: int = 0
    took_ms: int | None = None
    results: list[SoldListing] = Field(default_factory=list)


class Category(_Model):
    category_id: str = Field(alias="categoryId")
    name: str
    group: str | None = None


class CategoriesResponse(APIResponse):
    site: str
    total: int | None = None
    count: int = 0
    categories: list[Category] = Field(default_factory=list)
