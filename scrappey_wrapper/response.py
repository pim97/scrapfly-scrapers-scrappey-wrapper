"""
ScrapeApiResponse class that mimics ScrapFly's response interface.
"""
from typing import Dict, Any, Optional
from parsel import Selector


class ScrapeApiResponse:
    """
    Response wrapper that provides a ScrapFly-compatible interface for Scrappey responses.
    """
    
    def __init__(self, scrappey_response: Dict[str, Any], original_url: str):
        self._raw_response = scrappey_response
        self._original_url = original_url
        
        solution = scrappey_response.get("solution", {})
        self._html = solution.get("html", solution.get("response", ""))
        self._selector: Optional[Selector] = None
        
        self._context = {
            "url": solution.get("url", original_url),
            "status_code": scrappey_response.get("status", solution.get("status", 200)),
            "cookies": solution.get("cookies", []),
            "headers": solution.get("headers", {}),
        }
        
        self._scrape_result = {
            "browser_data": {
                "xhr_call": solution.get("xhrCalls", []),
                "javascript_evaluation_result": solution.get("jsResult"),
                "screenshot": scrappey_response.get("screenshotUrl"),
            },
            "content": self._html,
            "status_code": self._context["status_code"],
            "url": self._context["url"],
        }
    
    @property
    def selector(self) -> Selector:
        if self._selector is None:
            self._selector = Selector(text=self._html)
        return self._selector
    
    @property
    def content(self) -> str:
        return self._html
    
    @property
    def context(self) -> Dict[str, Any]:
        return self._context
    
    @property
    def scrape_result(self) -> Dict[str, Any]:
        return self._scrape_result
    
    @property
    def status_code(self) -> int:
        return self._context.get("status_code", 200)
    
    @property
    def url(self) -> str:
        return self._context.get("url", self._original_url)
    
    @property
    def cookies(self) -> list:
        return self._context.get("cookies", [])
    
    @property
    def headers(self) -> Dict[str, str]:
        return self._context.get("headers", {})
    
    @property
    def raw_response(self) -> Dict[str, Any]:
        return self._raw_response
    
    @property
    def captcha_tokens(self) -> list:
        """
        Returns solved captcha tokens if automaticallySolveCaptchas was enabled.
        Each token includes captchaType, token, and timestamp.
        """
        solution = self._raw_response.get("solution", {})
        return solution.get("javascriptReturn", [])
    
    @property
    def additional_cost(self) -> float:
        """Returns additional costs (e.g., from captcha solving)."""
        return self._raw_response.get("additionalCost", 0.0)

