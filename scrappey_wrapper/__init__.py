"""
Scrappey Wrapper - A ScrapFly-compatible interface for the Scrappey API.

Usage:
    from scrappey_wrapper import ScrapeConfig, ScrapflyClient, ScrapeApiResponse
"""

from .config import ScrapeConfig
from .response import ScrapeApiResponse
from .scrappey import ScrappeyClient, ScrapflyClient
from .exceptions import (
    ScrappeyError,
    ScrappeyAuthError,
    ScrappeyRequestError,
    ScrappeyTimeoutError,
    ScrapflyScrapeError,
)

__all__ = [
    "ScrappeyClient",
    "ScrapflyClient",
    "ScrapeConfig",
    "ScrapeApiResponse",
    "ScrappeyError",
    "ScrappeyAuthError",
    "ScrappeyRequestError",
    "ScrappeyTimeoutError",
    "ScrapflyScrapeError",
]

__version__ = "1.0.0"

