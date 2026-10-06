"""The eBay API: sold listings, one listing in full, and category lookup."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

from ._models import CategoriesResponse, Item, SoldResponse

if TYPE_CHECKING:
    from ._client import AsyncTrawl, Trawl

Site = Literal["EBAY_US", "EBAY_GB"]
Condition = Literal["new", "used", "parts", "other"]
AttrFilter = Mapping[str, "str | Sequence[str]"] | Sequence[str] | str

_PREFIX = "/ebay/v1"
_Params = list[tuple[str, str]]


def _day(value: date | str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _joined(value: str | Sequence[str]) -> str:
    return value if isinstance(value, str) else ",".join(value)


def _attr_params(attr: AttrFilter) -> _Params:
    # The API takes one attr=Key:Value per filter, the parameter repeated.
    if isinstance(attr, str):
        return [("attr", attr)]
    if isinstance(attr, Mapping):
        params: _Params = []
        for key, value in attr.items():
            for one in [value] if isinstance(value, str) else value:
                params.append(("attr", f"{key}:{one}"))
        return params
    return [("attr", one) for one in attr]


def _sold_params(
    query: str,
    exclude: str | Sequence[str] | None,
    site: Site | None,
    category: str | int | None,
    condition: Condition | Sequence[Condition] | None,
    attr: AttrFilter | None,
    min_price: float | None,
    max_price: float | None,
    date_from: date | str | None,
    date_to: date | str | None,
    max_pages: int | None,
    details: bool,
) -> _Params:
    params: _Params = [("query", query)]
    if exclude:
        params.append(("exclude", _joined(exclude)))
    if site:
        params.append(("site", site))
    if category is not None:
        params.append(("category", str(category)))
    if condition:
        params.append(("condition", _joined(condition)))
    if attr:
        params.extend(_attr_params(attr))
    if min_price is not None:
        params.append(("min_price", str(min_price)))
    if max_price is not None:
        params.append(("max_price", str(max_price)))
    if date_from is not None:
        params.append(("date_from", _day(date_from)))
    if date_to is not None:
        params.append(("date_to", _day(date_to)))
    if max_pages is not None:
        params.append(("max_pages", str(max_pages)))
    if details:
        params.append(("details", "1"))
    return params


def _item_params(item_id: str | int, site: Site | None) -> _Params:
    params: _Params = [("item_id", str(item_id))]
    if site:
        params.append(("site", site))
    return params


def _categories_params(query: str | int, site: Site | None) -> _Params:
    params: _Params = [("query", str(query))]
    if site:
        params.append(("site", site))
    return params


class Ebay:
    def __init__(self, client: Trawl) -> None:
        self._client = client

    def sold(
        self,
        query: str,
        *,
        exclude: str | Sequence[str] | None = None,
        site: Site | None = None,
        category: str | int | None = None,
        condition: Condition | Sequence[Condition] | None = None,
        attr: AttrFilter | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        max_pages: int | None = None,
        details: bool = False,
    ) -> SoldResponse:
        """Sold listings whose title contains every word of `query`, newest first.

        Args:
            query: Words that must all appear in the listing title, in any order.
            exclude: Words that must not appear in the title.
            site: Marketplace, "EBAY_US" (the default) or "EBAY_GB".
            category: An eBay leaf category id; find ids with `categories()`.
            condition: One or several of "new", "used", "parts", "other".
            attr: Item specifics to match, e.g. `{"Brand": "Apple", "Grade": ["9", "10"]}`.
                Different keys must all match; several values for one key match any.
            min_price: Minimum sale price in the marketplace's own currency.
            max_price: Maximum sale price in the marketplace's own currency.
            date_from: Earliest sale date, inclusive (a `date` or "YYYY-MM-DD").
            date_to: Latest sale date, inclusive.
            max_pages: Pages of 100 results to return in this one response, 1-20
                (1 when omitted). Also the most credits the call can cost.
            details: Include each result's full listing details (`listing.details`).

        Costs 1 credit per page of results returned, 2 with `details=True`;
        a search that matches nothing is free.
        """
        params = _sold_params(
            query, exclude, site, category, condition, attr,
            min_price, max_price, date_from, date_to, max_pages, details,
        )  # fmt: skip
        return self._client._get(f"{_PREFIX}/sold", params, SoldResponse)

    def item(self, item_id: str | int, *, site: Site | None = None) -> Item:
        """One sold listing in full, by the `item_id` of any `sold()` result.

        Costs 1 credit. Details become available a few minutes after a sale;
        until then the call raises `NotFoundError`, which is never billed. A
        listing eBay has removed answers free, with `item.is_removed` true.
        """
        return self._client._get(f"{_PREFIX}/item", _item_params(item_id, site), Item)

    def categories(self, query: str | int, *, site: Site | None = None) -> CategoriesResponse:
        """eBay leaf categories by name, busiest first; a numeric query looks up that id.

        Costs 1 credit, nothing if no category matches. Category ids differ per
        marketplace, so pass the same `site` you will search with.
        """
        return self._client._get(
            f"{_PREFIX}/categories", _categories_params(query, site), CategoriesResponse
        )


class AsyncEbay:
    def __init__(self, client: AsyncTrawl) -> None:
        self._client = client

    async def sold(
        self,
        query: str,
        *,
        exclude: str | Sequence[str] | None = None,
        site: Site | None = None,
        category: str | int | None = None,
        condition: Condition | Sequence[Condition] | None = None,
        attr: AttrFilter | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        max_pages: int | None = None,
        details: bool = False,
    ) -> SoldResponse:
        """Sold listings matching `query`, newest first. See `Ebay.sold`."""
        params = _sold_params(
            query, exclude, site, category, condition, attr,
            min_price, max_price, date_from, date_to, max_pages, details,
        )  # fmt: skip
        return await self._client._get(f"{_PREFIX}/sold", params, SoldResponse)

    async def item(self, item_id: str | int, *, site: Site | None = None) -> Item:
        """One sold listing in full. See `Ebay.item`."""
        return await self._client._get(f"{_PREFIX}/item", _item_params(item_id, site), Item)

    async def categories(self, query: str | int, *, site: Site | None = None) -> CategoriesResponse:
        """eBay leaf categories by name or id. See `Ebay.categories`."""
        return await self._client._get(
            f"{_PREFIX}/categories", _categories_params(query, site), CategoriesResponse
        )
