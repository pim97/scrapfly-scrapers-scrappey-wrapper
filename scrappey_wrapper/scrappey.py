"""
ScrappeyClient - Main client class for interacting with Scrappey API.
"""
import asyncio
import os
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


class ScrappeyClient:
    """
    Client for interacting with the Scrappey API.
    Provides a ScrapFly-compatible interface for easy migration.
    """
    
    BASE_URL = "https://publisher.scrappey.com/api/v1"
    
    def __init__(
        self,
        key: Optional[str] = None,
        max_concurrency: int = 50,
        timeout: int = 120,
    ):
        self.api_key = key or os.environ.get("SCRAPPEY_KEY")
        if not self.api_key:
            raise ScrappeyAuthError(
                "API key is required. Set SCRAPPEY_KEY environment variable or pass key parameter."
            )
        
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self._session_cache: Dict[str, str] = {}
    
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
        response = await self._make_request(payload)
        return ScrapeApiResponse(response, config.url)
    
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

