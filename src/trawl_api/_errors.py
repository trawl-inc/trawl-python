from __future__ import annotations

import httpx


class TrawlError(Exception):
    """Base class for every error this package raises."""


class APIConnectionError(TrawlError):
    """The request never got an answer (DNS, connection reset, TLS)."""


class APITimeoutError(APIConnectionError):
    """The request ran past the client's timeout."""


class APIResponseValidationError(TrawlError):
    """The API answered 2xx with a body this version of the package cannot read."""


class APIStatusError(TrawlError):
    """The API answered with an error status. `message` is the API's own explanation."""

    def __init__(self, message: str, response: httpx.Response) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code


class BadRequestError(APIStatusError):
    """400: a parameter failed validation; the message names the field and the rule."""


class AuthenticationError(APIStatusError):
    """403: the API key is missing, invalid or deleted."""


class NotFoundError(APIStatusError):
    """404: nothing found, e.g. an item whose details are not available yet. Not billed."""


class RateLimitError(APIStatusError):
    """429 with Retry-After: the plan's per-second rate was exceeded. Wait and retry."""

    def __init__(self, message: str, response: httpx.Response, *, retry_after: float) -> None:
        super().__init__(message, response)
        self.retry_after = retry_after


# Deliberately not a RateLimitError: code that catches a rate limit to sleep and
# retry would loop forever on spent credits, which only a new window or a plan fixes.
class InsufficientCreditsError(APIStatusError):
    """429 without Retry-After: the month's credits are spent, or too few remain to
    cover the request's max_pages. Lower max_pages, upgrade, or wait for the reset."""


class ServerError(APIStatusError):
    """5xx: a failure on trawl's side. Safe to retry."""
