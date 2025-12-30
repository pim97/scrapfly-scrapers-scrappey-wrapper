"""
ScrappeyClient - Main client class for interacting with Scrappey API.
"""
import asyncio
import json
import os
import random
import re
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
        debug: Enable debug logging (default: False, or set SCRAPPEY_DEBUG=1).
    
    Example:
        >>> client = ScrappeyClient(key="your-api-key", max_concurrency=50)
        >>> # Or use environment variable
        >>> client = ScrappeyClient()  # Uses SCRAPPEY_KEY env var, 100 concurrent
        >>> # Enable debug logging
        >>> client = ScrappeyClient(debug=True)
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
        debug: Optional[bool] = None,
    ):
        self.api_key = key or os.environ.get("SCRAPPEY_KEY")
        if not self.api_key:
            raise ScrappeyAuthError(
                "API key is required. Set SCRAPPEY_KEY environment variable or pass key parameter."
            )
        
        # Debug mode from param or env var
        if debug is None:
            debug = os.environ.get("SCRAPPEY_DEBUG", "").lower() in ("1", "true", "yes")
        self.debug = debug
        
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
    
    def _log_debug(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            print(f"[Scrappey DEBUG] {message}")
    
    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML."""
        if not html:
            return "(empty response)"
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:80]
        return "(no title)"
    
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
        
        # Log request payload in debug mode
        if self.debug:
            url = payload.get("url", "unknown")
            # Create a sanitized payload for logging (hide sensitive data)
            log_payload = {k: v for k, v in payload.items() if k != "key"}
            self._log_debug(f"→ Request to: {url}")
            self._log_debug(f"  Payload: {json.dumps(log_payload, indent=2)}")
        
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            try:
                response = await client.post(
                    self._api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                data = response.json()
                
                # Log response in debug mode
                if self.debug:
                    solution = data.get("solution", {})
                    html = solution.get("response", solution.get("html", ""))
                    title = self._extract_title(html)
                    status = solution.get("statusCode", "?")
                    current_url = solution.get("currentUrl", payload.get("url", "?"))
                    elapsed = data.get("timeElapsed", "?")
                    self._log_debug(f"← Response: {status} | Title: {title}")
                    self._log_debug(f"  URL: {current_url} | Time: {elapsed}ms")
                
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
            except ScrappeyAuthError:
                # Auth errors cannot be retried - re-raise immediately
                raise
            except (ScrappeyError, ScrappeyRequestError, ScrappeyTimeoutError, httpx.HTTPError, Exception) as e:
                last_error = e
                error_message = str(e)
                error_short = error_message[:150].replace('\n', ' ')
                
                # Don't retry if we've exhausted attempts
                if attempt >= self.max_retries:
                    print(f"[Scrappey] ❌ Failed after {self.max_retries + 1} attempts for {config.url}")
                    print(f"[Scrappey]    Last error: {error_short}")
                    break
                
                # Calculate delay and wait
                delay = self._get_retry_delay(attempt)
                print(f"[Scrappey] ⚠️  Error on {config.url}: {error_short}")
                print(f"[Scrappey]    Retrying in {delay:.1f}s (attempt {attempt + 2}/{self.max_retries + 1})")
                await asyncio.sleep(delay)
        
        # All retries exhausted - return an empty response instead of crashing
        print(f"[Scrappey] ⚠️  Returning empty response for {config.url} after all retries failed")
        return ScrapeApiResponse(
            {"solution": {"html": "", "status": 0}, "error": str(last_error)},
            config.url
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

