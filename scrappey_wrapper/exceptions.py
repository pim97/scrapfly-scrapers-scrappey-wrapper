"""
Custom exceptions for the Scrappey wrapper.
"""

class ScrappeyError(Exception):
    """Base exception for Scrappey wrapper errors."""
    
    def __init__(self, message: str, code: str = None, api_response: dict = None):
        self.message = message
        self.code = code
        self.api_response = api_response
        super().__init__(self.message)


class ScrappeyAuthError(ScrappeyError):
    """Raised when authentication fails (invalid API key)."""
    pass


class ScrappeyRequestError(ScrappeyError):
    """Raised when a scrape request fails."""
    pass


class ScrappeyTimeoutError(ScrappeyError):
    """Raised when a request times out."""
    pass


class ScrapflyScrapeError(ScrappeyError):
    """
    Compatibility exception matching ScrapFly's error class.
    Used in scrapers that catch this specific exception type.
    """
    
    def __init__(self, message: str, code: str = None, api_response: dict = None):
        super().__init__(message, code, api_response)

