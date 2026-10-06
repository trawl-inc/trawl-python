from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date, datetime, timezone

import httpx
import pytest
import samples

import trawl_api
from trawl_api import (
    APIConnectionError,
    APIResponseValidationError,
    AsyncTrawl,
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    ServerError,
    Trawl,
    TrawlError,
)

Handler = Callable[[httpx.Request], httpx.Response]


def client_for(handler: Handler, **options) -> Trawl:
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return Trawl("sk_test", http_client=http, **options)


def answering(*responses: httpx.Response) -> tuple[Handler, list[httpx.Request]]:
    """A handler that gives each response in turn (the last one repeats)."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return responses[min(len(seen), len(responses)) - 1]

    return handler, seen


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr("trawl_api._client.time.sleep", slept.append)
    return slept


def test_requires_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRAWL_API_KEY", raising=False)
    with pytest.raises(TrawlError, match="TRAWL_API_KEY"):
        Trawl()


def test_reads_the_key_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAWL_API_KEY", "sk_env")
    assert Trawl().api_key == "sk_env"


def test_sold_sends_the_documented_request() -> None:
    handler, seen = answering(httpx.Response(200, json=samples.SOLD))
    client_for(handler).ebay.sold(
        "iphone 13 pro",
        exclude=["case", "cracked"],
        site="EBAY_GB",
        category=9355,
        condition=["new", "used"],
        attr={"Brand": "Apple", "Grade": ["9", "10"]},
        min_price=50,
        max_price=500.5,
        date_from=date(2026, 1, 1),
        date_to=datetime(2026, 6, 30, 12, 0),
        max_pages=5,
        details=True,
    )
    request = seen[0]
    assert request.method == "GET"
    assert request.url.path == "/ebay/v1/sold"
    assert request.url.host == "api.trawl.dev"
    assert request.headers["x-api-key"] == "sk_test"
    assert request.headers["user-agent"] == f"trawl-python/{trawl_api.__version__}"
    assert request.url.params.multi_items() == [
        ("query", "iphone 13 pro"),
        ("exclude", "case,cracked"),
        ("site", "EBAY_GB"),
        ("category", "9355"),
        ("condition", "new,used"),
        ("attr", "Brand:Apple"),
        ("attr", "Grade:9"),
        ("attr", "Grade:10"),
        ("min_price", "50"),
        ("max_price", "500.5"),
        ("date_from", "2026-01-01"),
        ("date_to", "2026-06-30"),
        ("max_pages", "5"),
        ("details", "1"),
    ]


def test_sold_sends_only_what_was_asked() -> None:
    handler, seen = answering(httpx.Response(200, json=samples.SOLD))
    client_for(handler).ebay.sold("iphone 13 pro")
    assert seen[0].url.params.multi_items() == [("query", "iphone 13 pro")]


def test_sold_reads_the_answer() -> None:
    headers = {
        "X-RateLimit-Limit": "10000",
        "X-RateLimit-Remaining": "9996",
        "X-RateLimit-Reset": "1790000000",
        "X-Credits-Charged": "4",
    }
    handler, _ = answering(httpx.Response(200, json=samples.SOLD, headers=headers))
    sold = client_for(handler).ebay.sold("iphone 13 pro")

    assert sold.count == 385
    assert sold.credits_charged == 4
    assert sold.query == ["iphone", "13", "pro"]
    listing = sold.results[0]
    assert listing.sale_price == 525.0
    assert listing.date_sold == datetime(2026, 7, 18, tzinfo=timezone.utc)
    assert listing.category_id == "9355"
    assert listing.bids is None
    assert listing.details is None

    assert sold.rate_limit is not None
    assert sold.rate_limit.limit == 10000
    assert sold.rate_limit.remaining == 9996
    assert sold.rate_limit.reset == datetime.fromtimestamp(1790000000, tz=timezone.utc)


def test_sold_with_details_nests_the_item() -> None:
    row = {**samples.SOLD["results"][0], "details": samples.ITEM}
    removed = {
        **samples.SOLD["results"][0],
        "details": samples.REMOVED_ITEM,
        "listing_state": "removed",
    }
    body = {**samples.SOLD, "results": [row, removed]}
    handler, _ = answering(httpx.Response(200, json=body))
    sold = client_for(handler).ebay.sold("iphone 13 pro", details=True)

    details = sold.results[0].details
    assert details is not None
    assert details.specifics["Storage Capacity"] == "256 GB"
    assert sold.results[1].listing_state == "removed"
    assert sold.results[1].details is not None
    assert sold.results[1].details.is_removed


def test_fields_added_later_are_kept() -> None:
    row = {**samples.SOLD["results"][0], "new_field": "x"}
    body = {**samples.SOLD, "results": [row], "another": 1}
    handler, _ = answering(httpx.Response(200, json=body))
    sold = client_for(handler).ebay.sold("iphone 13 pro")
    assert sold.model_extra == {"another": 1}
    assert sold.results[0].model_extra == {"new_field": "x"}


def test_item() -> None:
    handler, seen = answering(httpx.Response(200, json=samples.ITEM))
    item = client_for(handler).ebay.item(256637082114, site="EBAY_US")

    assert seen[0].url.path == "/ebay/v1/item"
    assert seen[0].url.params.multi_items() == [("item_id", "256637082114"), ("site", "EBAY_US")]
    assert item.title == "Apple iPhone 13 Pro 256GB Graphite Unlocked"
    assert item.sold_at == datetime(2026, 7, 18, 21, 14, tzinfo=timezone.utc)
    assert item.seller is not None and item.seller.feedback_percent == 99.6
    assert item.specifics == {
        "Brand": "Apple",
        "Model": "Apple iPhone 13 Pro",
        "Storage Capacity": "256 GB",
        "Network": "Unlocked",
    }
    assert item.sales[0].sale_price == 525.0
    assert len(item.images) == 2
    assert not item.is_removed
    assert item.credits_charged == 1


def test_a_removed_item_is_an_answer() -> None:
    handler, _ = answering(httpx.Response(200, json=samples.REMOVED_ITEM))
    item = client_for(handler).ebay.item("256637082114")
    assert item.is_removed
    assert item.title is None
    assert item.credits_charged == 0


def test_categories() -> None:
    handler, seen = answering(httpx.Response(200, json=samples.CATEGORIES))
    found = client_for(handler).ebay.categories("trading cards", site="EBAY_GB")

    assert seen[0].url.path == "/ebay/v1/categories"
    assert seen[0].url.params.multi_items() == [("query", "trading cards"), ("site", "EBAY_GB")]
    assert found.total == 38
    assert [c.category_id for c in found.categories] == ["261328", "183050"]
    assert found.categories[0].group == "Sports Mem, Cards & Fan Shop"


@pytest.mark.parametrize(
    ("status", "error"),
    [(400, BadRequestError), (403, AuthenticationError), (404, NotFoundError)],
)
def test_client_errors_are_raised_at_once(status: int, error: type[Exception]) -> None:
    message = "min_price must be <= max_price"
    handler, seen = answering(httpx.Response(status, json={"error": message}))
    with pytest.raises(error) as raised:
        client_for(handler).ebay.sold("iphone")
    assert str(raised.value) == message
    assert raised.value.status_code == status  # type: ignore[attr-defined]
    assert len(seen) == 1


def test_spent_credits_are_not_retried() -> None:
    handler, seen = answering(httpx.Response(429, json={"error": "monthly limit reached"}))
    with pytest.raises(InsufficientCreditsError, match="monthly limit reached"):
        client_for(handler).ebay.sold("iphone")
    assert len(seen) == 1


def test_a_rate_limit_waits_and_retries(no_sleep: list[float]) -> None:
    limited = httpx.Response(429, json={"error": "rate limit"}, headers={"Retry-After": "1"})
    handler, seen = answering(limited, httpx.Response(200, json=samples.SOLD))
    sold = client_for(handler).ebay.sold("iphone")
    assert sold.count == 385
    assert len(seen) == 2
    assert no_sleep == [1.0]


def test_a_rate_limit_that_outlasts_the_retries_is_raised() -> None:
    limited = httpx.Response(429, json={"error": "rate limit"}, headers={"Retry-After": "1"})
    handler, seen = answering(limited)
    with pytest.raises(RateLimitError) as raised:
        client_for(handler, max_retries=1).ebay.sold("iphone")
    assert raised.value.retry_after == 1.0
    assert len(seen) == 2


def test_server_errors_are_retried_then_raised() -> None:
    handler, seen = answering(httpx.Response(503, json={"error": "search unavailable"}))
    with pytest.raises(ServerError, match="search unavailable"):
        client_for(handler).ebay.sold("iphone")
    assert len(seen) == 3


def test_max_retries_zero_asks_once() -> None:
    handler, seen = answering(httpx.Response(503, text="bad gateway"))
    with pytest.raises(ServerError, match="bad gateway"):
        client_for(handler, max_retries=0).ebay.sold("iphone")
    assert len(seen) == 1


def test_connection_errors_are_retried_then_raised() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("no route", request=request)

    with pytest.raises(APIConnectionError):
        client_for(handler).ebay.sold("iphone")
    assert calls == 3


def test_an_unreadable_answer_says_so() -> None:
    handler, _ = answering(httpx.Response(200, json={"results": "nope"}))
    with pytest.raises(APIResponseValidationError, match="SoldResponse"):
        client_for(handler).ebay.sold("iphone")


def test_base_url_can_be_changed() -> None:
    handler, seen = answering(httpx.Response(200, json=samples.SOLD))
    client_for(handler, base_url="http://localhost:8787/").ebay.sold("iphone")
    assert str(seen[0].url).startswith("http://localhost:8787/ebay/v1/sold?")


def test_async_client() -> None:
    handler, seen = answering(httpx.Response(200, json=samples.SOLD))

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with AsyncTrawl("sk_test", http_client=http) as client:
            sold = await client.ebay.sold("iphone 13 pro", condition="used")
            return sold

    sold = asyncio.run(run())
    assert sold.results[0].item_id == "256637082114"
    assert seen[0].url.params.multi_items() == [("query", "iphone 13 pro"), ("condition", "used")]
