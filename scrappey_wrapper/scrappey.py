"""
ScrappeyClient - Main client class for interacting with Scrappey API.
"""
import asyncio
import os
import random
from typing import Dict, Any, Optional, List, AsyncIterator, Union

import httpx

from .config import ScrapeConfig
from .response import ScrapeApiResponse
from .exceptions import (
    ScrappeyError,
    ScrappeyAuthError,
    ScrappeyRequestError,
    ScrappeyTimeoutError,
    ScrapflyScrapeError,
)

# Errors that should trigger a retry
RETRYABLE_ERRORS = [
    "browser closed",
    "browser disconnected",
    "target closed",
    "page closed",
    "navigation failed",
    "net::err",
    "timeout",
    "econnreset",
    "econnrefused",
    "socket hang up",
    "network error",
    "protocol error",
    "session not found",
    "context destroyed",
]


class ScrappeyClient:
    """
    Client for interacting with the Scrappey API.
    Provides a ScrapFly-compatible interface for easy migration.
    
    Args:
        key: Scrappey API key. If not provided, uses SCRAPPEY_KEY env variable.
        max_concurrency: Maximum concurrent requests (1-100, default: 100).
        timeout: Request timeout in seconds (default: 120).
        max_retries: Number of retries for transient errors (default: 3).
        retry_delay: Initial retry delay in seconds (default: 1.0).
        retry_max_delay: Maximum retry delay in seconds (default: 30.0).
    
    Example:
        >>> client = ScrappeyClient(key="your-api-key", max_concurrency=50)
        >>> # Or use environment variable
        >>> client = ScrappeyClient()  # Uses SCRAPPEY_KEY env var, 100 concurrent
    """
    
    BASE_URL = "https://publisher.scrappey.com/api/v1"
    MAX_ALLOWED_CONCURRENCY = 100  # Scrappey supports up to 100 concurrent requests
    
    def __init__(
        self,
        key: Optional[str] = None,
        max_concurrency: int = 100,  # Scrappey supports high concurrency by default
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_max_delay: float = 30.0,
    ):
        self.api_key = key or os.environ.get("SCRAPPEY_KEY")
        if not self.api_key:
            raise ScrappeyAuthError(
                "API key is required. Set SCRAPPEY_KEY environment variable or pass key parameter."
            )
        
        # Validate and set concurrency (1-100)
        if max_concurrency < 1:
            max_concurrency = 1
        elif max_concurrency > self.MAX_ALLOWED_CONCURRENCY:
            print(f"[Scrappey] Warning: max_concurrency {max_concurrency} exceeds limit, using {self.MAX_ALLOWED_CONCURRENCY}")
            max_concurrency = self.MAX_ALLOWED_CONCURRENCY
        
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_max_delay = retry_max_delay
        self._session_cache: Dict[str, str] = {}
    
    def _is_retryable_error(self, error_message: str) -> bool:
        """Check if an error message indicates a retryable error."""
        error_lower = error_message.lower()
        return any(err in error_lower for err in RETRYABLE_ERRORS)
    
    def _get_retry_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.retry_delay * (2 ** attempt)
        delay = min(delay, self.retry_max_delay)
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return delay + jitter
    
    @property
    def _api_url(self) -> str:
        return f"{self.BASE_URL}?key={self.api_key}"
    
    async def _make_request(
        self,
        payload: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        request_timeout = timeout or self.timeout
        
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            try:
                response = await client.post(
                    self._api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                data = response.json()
                
                if "error" in data:
                    error_code = data.get("code", "UNKNOWN")
                    error_message = data.get("error", "Unknown error")
                    
                    if error_code == "CODE-0001":
                        raise ScrappeyAuthError(error_message, error_code, data)
                    elif "timeout" in error_message.lower():
                        raise ScrappeyTimeoutError(error_message, error_code, data)
                    else:
                        raise ScrappeyRequestError(error_message, error_code, data)
                
                return data
                
            except httpx.TimeoutException as e:
                raise ScrappeyTimeoutError(f"Request timed out: {e}")
            except httpx.HTTPError as e:
                raise ScrappeyRequestError(f"HTTP error: {e}")
    
    async def create_session(self, **kwargs) -> str:
        payload = {"cmd": "sessions.create", **kwargs}
        response = await self._make_request(payload)
        session_id = response.get("session")
        if not session_id:
            raise ScrappeyError("Failed to create session - no session ID returned")
        return session_id
    
    async def destroy_session(self, session_id: str) -> bool:
        payload = {"cmd": "sessions.destroy", "session": session_id}
        await self._make_request(payload)
        return True
    
    async def async_scrape(
        self,
        config: ScrapeConfig,
        session_id: Optional[str] = None
    ) -> ScrapeApiResponse:
        payload = config.to_scrappey_payload(session_id)
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._make_request(payload)
                return ScrapeApiResponse(response, config.url)
            except (ScrappeyRequestError, ScrappeyTimeoutError) as e:
                last_error = e
                error_message = str(e)
                
                # Don't retry auth errors
                if isinstance(e, ScrappeyAuthError):
                    raise
                
                # Check if error is retryable
                if not self._is_retryable_error(error_message):
                    raise
                
                # Don't retry if we've exhausted attempts
                if attempt >= self.max_retries:
                    break
                
                # Calculate delay and wait
                delay = self._get_retry_delay(attempt)
                print(f"[Scrappey] Retryable error: {error_message[:100]}... Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
            except httpx.HTTPError as e:
                last_error = e
                error_message = str(e)
                
                if not self._is_retryable_error(error_message):
                    raise ScrappeyRequestError(f"HTTP error: {e}")
                
                if attempt >= self.max_retries:
                    break
                
                delay = self._get_retry_delay(attempt)
                print(f"[Scrappey] HTTP error: {error_message[:100]}... Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise ScrappeyRequestError(
            f"Failed after {self.max_retries + 1} attempts. Last error: {last_error}",
            code="MAX_RETRIES_EXCEEDED",
            api_response={"url": config.url}
        )
    
    async def concurrent_scrape(
        self,
        configs: List[ScrapeConfig],
        session_id: Optional[str] = None
    ) -> AsyncIterator[Union[ScrapeApiResponse, ScrapflyScrapeError]]:
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def scrape_with_semaphore(config: ScrapeConfig) -> Union[ScrapeApiResponse, ScrapflyScrapeError]:
            async with semaphore:
                try:
                    return await self.async_scrape(config, session_id)
                except ScrappeyError as e:
                    error = ScrapflyScrapeError(
                        message=str(e),
                        code=getattr(e, 'code', None),
                        api_response=getattr(e, 'api_response', None)
                    )
                    error.api_response = {"config": {"url": config.url}}
                    return error
        
        tasks = [scrape_with_semaphore(config) for config in configs]
        
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result
    
    def scrape(self, config: ScrapeConfig) -> ScrapeApiResponse:
        """Synchronous scrape method for compatibility."""
        return asyncio.get_event_loop().run_until_complete(self.async_scrape(config))


# Alias for ScrapFly compatibility
ScrapflyClient = ScrappeyClient

