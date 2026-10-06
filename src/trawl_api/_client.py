from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Any, TypeVar

import httpx
from pydantic import ValidationError

from ._errors import (
    APIConnectionError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TrawlError,
)
from ._models import APIResponse, rate_limit_from_headers
from ._version import __version__
from .ebay import AsyncEbay, Ebay

DEFAULT_BASE_URL = "https://api.trawl.dev"
# A 20-page search with details is one response of up to 2,000 listings.
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2

_RETRY_STATUSES = frozenset({500, 502, 503, 504})
_MAX_RETRY_AFTER = 30.0
_STATUS_ERRORS: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: NotFoundError,
}

Params = list[tuple[str, str]]
ResponseT = TypeVar("ResponseT", bound=APIResponse)


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return 1.0


def _error_message(response: httpx.Response) -> str:
    try:
        body: Any = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and isinstance(body.get("error"), str):
        return body["error"]
    return response.text.strip() or f"HTTP {response.status_code}"


def _status_error(response: httpx.Response) -> APIStatusError:
    message = _error_message(response)
    status = response.status_code
    if status == 429:
        retry_after = _retry_after(response)
        if retry_after is None:
            return InsufficientCreditsError(message, response)
        return RateLimitError(message, response, retry_after=retry_after)
    if status >= 500:
        return ServerError(message, response)
    return _STATUS_ERRORS.get(status, APIStatusError)(message, response)


def _parse(response: httpx.Response, model: type[ResponseT]) -> ResponseT:
    try:
        parsed = model.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise APIResponseValidationError(
            f"The API's answer could not be read as {model.__name__}. "
            "Upgrading trawl-api may fix this: pip install -U trawl-api"
        ) from exc
    parsed._rate_limit = rate_limit_from_headers(response.headers)
    return parsed


class _BaseClient:
    def __init__(
        self,
        api_key: str | None,
        base_url: str | None,
        timeout: float,
        max_retries: int,
    ) -> None:
        api_key = api_key or os.environ.get("TRAWL_API_KEY")
        if not api_key:
            raise TrawlError(
                "No API key. Pass api_key=... or set the TRAWL_API_KEY environment variable. "
                "Create a key at https://trawl.dev/console/keys"
            )
        self.api_key = api_key
        self.base_url = (base_url or os.environ.get("TRAWL_BASE_URL") or DEFAULT_BASE_URL).rstrip(
            "/"
        )
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "accept": "application/json",
            "user-agent": f"trawl-python/{__version__}",
        }

    def _retry_delay(self, attempt: int, response: httpx.Response | None) -> float | None:
        """Seconds to wait before another attempt, or None when the failure is final."""
        if attempt >= self.max_retries:
            return None
        if response is not None:
            retry_after = _retry_after(response)
            if response.status_code == 429:
                # Without Retry-After the credits are spent, and waiting does not help.
                if retry_after is None:
                    return None
                # Jittered: the API answers every limited caller with the same wait, and
                # concurrent callers that all come back at that instant collide again.
                return min(retry_after, _MAX_RETRY_AFTER) + random.uniform(0, 0.25)
            if response.status_code not in _RETRY_STATUSES:
                return None
            if retry_after is not None:
                return min(retry_after, _MAX_RETRY_AFTER)
        return min(0.5 * 2**attempt, 8.0) * random.uniform(0.75, 1.25)


class Trawl(_BaseClient):
    """The trawl API client.

        client = Trawl()  # reads TRAWL_API_KEY
        sold = client.ebay.sold("iphone 15 pro 256gb", condition="used")

    Failed requests are retried `max_retries` times on connection errors, 5xx
    answers and per-second rate limits; errors are never billed.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key, base_url, timeout, max_retries)
        self._http = http_client or httpx.Client()
        self._owns_http = http_client is None
        self.ebay = Ebay(self)

    def _get(self, path: str, params: Params, model: type[ResponseT]) -> ResponseT:
        attempt = 0
        while True:
            response: httpx.Response | None = None
            cause: Exception | None = None
            error: TrawlError
            try:
                response = self._http.get(
                    self.base_url + path,
                    params=tuple(params),
                    headers=self._headers,
                    timeout=self.timeout,
                )
            except httpx.TimeoutException as exc:
                error, cause = APITimeoutError("The request timed out."), exc
            except httpx.TransportError as exc:
                error, cause = APIConnectionError(f"Could not reach the API: {exc}"), exc
            else:
                if response.is_success:
                    return _parse(response, model)
                error = _status_error(response)
            delay = self._retry_delay(attempt, response)
            if delay is None:
                raise error from cause
            time.sleep(delay)
            attempt += 1

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Trawl:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class AsyncTrawl(_BaseClient):
    """The trawl API client for asyncio. Same surface as `Trawl`, awaited."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key, base_url, timeout, max_retries)
        self._http = http_client or httpx.AsyncClient()
        self._owns_http = http_client is None
        self.ebay = AsyncEbay(self)

    async def _get(self, path: str, params: Params, model: type[ResponseT]) -> ResponseT:
        attempt = 0
        while True:
            response: httpx.Response | None = None
            cause: Exception | None = None
            error: TrawlError
            try:
                response = await self._http.get(
                    self.base_url + path,
                    params=tuple(params),
                    headers=self._headers,
                    timeout=self.timeout,
                )
            except httpx.TimeoutException as exc:
                error, cause = APITimeoutError("The request timed out."), exc
            except httpx.TransportError as exc:
                error, cause = APIConnectionError(f"Could not reach the API: {exc}"), exc
            else:
                if response.is_success:
                    return _parse(response, model)
                error = _status_error(response)
            delay = self._retry_delay(attempt, response)
            if delay is None:
                raise error from cause
            await asyncio.sleep(delay)
            attempt += 1

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncTrawl:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()
