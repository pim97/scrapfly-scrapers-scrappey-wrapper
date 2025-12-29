"""
ScrapeConfig class that mimics ScrapFly's configuration interface.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ScrapeConfig:
    """
    Configuration for a scrape request, matching ScrapFly's ScrapeConfig interface.
    """
    url: str
    asp: bool = True
    country: str = "US"
    render_js: bool = False
    headers: Dict[str, str] = field(default_factory=dict)
    method: str = "GET"
    body: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy_pool: Optional[str] = None
    wait_for_selector: Optional[str] = None
    js: Optional[str] = None
    js_scenario: Optional[List[Dict[str, Any]]] = None
    auto_scroll: bool = False
    lang: Optional[List[str]] = None
    session: Optional[str] = None
    cache: bool = False
    cache_ttl: Optional[int] = None
    timeout: Optional[int] = None
    retry: bool = True
    rendering_wait: Optional[int] = None
    screenshots: Optional[Dict[str, Any]] = None
    debug: bool = False
    auto_solve_captcha: bool = True  # Automatically solve captchas (reCAPTCHA, hCaptcha, Turnstile, etc.)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_scrappey_payload(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Convert this config to a Scrappey API payload."""
        method_lower = self.method.lower()
        cmd = f"request.{method_lower}"
        
        payload: Dict[str, Any] = {
            "cmd": cmd,
            "url": self.url,
            # Always use premium proxy for faster, more reliable scraping
            "premiumProxy": True,
        }
        
        if session_id:
            payload["session"] = session_id
        elif self.session:
            payload["session"] = self.session
        
        if self.country:
            payload["proxyCountry"] = self._map_country_code(self.country)
        
        if self.headers:
            payload["customHeaders"] = self.headers
        
        if self.cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            if "customHeaders" not in payload:
                payload["customHeaders"] = {}
            payload["customHeaders"]["Cookie"] = cookie_str
        
        if self.body:
            payload["postData"] = self.body
        
        if self.data:
            payload["postData"] = self.data
        
        browser_actions = []
        
        if self.wait_for_selector:
            wait_action = {
                "type": "wait_for_selector",
                "cssSelector": self.wait_for_selector,
                "timeout": 30000
            }
            # Allow ignoring errors for wait_for_selector (won't crash if element not found)
            if self.extra.get("waitForSelectorIgnoreErrors"):
                wait_action["ignoreErrors"] = True
            browser_actions.append(wait_action)
        
        if self.js_scenario:
            for action in self.js_scenario:
                browser_actions.append(self._convert_js_scenario_action(action))
        
        if self.js:
            browser_actions.append({
                "type": "execute_js",
                "code": self.js
            })
        
        if self.auto_scroll:
            browser_actions.append({
                "type": "scroll"
            })
        
        if self.rendering_wait:
            # Convert milliseconds to seconds (Scrappey uses seconds)
            wait_seconds = self.rendering_wait / 1000 if self.rendering_wait > 100 else self.rendering_wait
            browser_actions.append({
                "type": "wait",
                "wait": wait_seconds
            })
        
        if browser_actions:
            payload["browserActions"] = browser_actions
        
        # Enable automatic captcha solving
        if self.auto_solve_captcha:
            payload["automaticallySolveCaptchas"] = True
        
        # Include any extra parameters
        if self.extra:
            payload.update(self.extra)
        
        return payload
    
    def _map_country_code(self, code: str) -> str:
        """Map 2-letter country codes to Scrappey's full country names."""
        country_map = {
            "US": "UnitedStates", "CA": "Canada", "GB": "UnitedKingdom",
            "UK": "UnitedKingdom", "DE": "Germany", "FR": "France",
            "ES": "Spain", "IT": "Italy", "NL": "Netherlands",
            "AU": "Australia", "JP": "Japan", "BR": "Brazil",
            "MX": "Mexico", "IN": "India", "CN": "China",
            "RU": "Russia", "KR": "SouthKorea", "SG": "Singapore",
            "HK": "HongKong", "TW": "Taiwan", "PL": "Poland",
            "SE": "Sweden", "NO": "Norway", "DK": "Denmark",
            "FI": "Finland", "CH": "Switzerland", "AT": "Austria",
            "BE": "Belgium", "IE": "Ireland", "PT": "Portugal",
            "GR": "Greece", "CZ": "CzechRepublic", "RO": "Romania",
            "HU": "Hungary", "TR": "Turkey", "IL": "Israel",
            "AE": "UnitedArabEmirates", "SA": "SaudiArabia",
            "ZA": "SouthAfrica", "AR": "Argentina", "CL": "Chile",
            "CO": "Colombia", "NZ": "NewZealand", "TH": "Thailand",
            "PH": "Philippines", "MY": "Malaysia", "ID": "Indonesia",
            "VN": "Vietnam",
        }
        return country_map.get(code.upper(), code)
    
    def _convert_js_scenario_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ScrapFly js_scenario action to Scrappey browserAction format."""
        if "wait_for_selector" in action:
            return {
                "type": "wait_for_selector",
                "cssSelector": action["wait_for_selector"].get("selector"),
                "timeout": action["wait_for_selector"].get("timeout", 30000)
            }
        elif "click" in action:
            click_data = action["click"]
            result = {"type": "click", "cssSelector": click_data.get("selector")}
            if click_data.get("ignore_if_not_visible"):
                result["ignoreErrors"] = True
            return result
        elif "wait" in action:
            return {"type": "wait", "wait": action["wait"]}
        elif "scroll" in action:
            scroll_data = action.get("scroll", {})
            result = {"type": "scroll"}
            if isinstance(scroll_data, dict) and scroll_data.get("selector"):
                result["cssSelector"] = scroll_data.get("selector")
            return result
        elif "execute_js" in action or "js" in action:
            code = action.get("execute_js", action.get("js", ""))
            return {"type": "execute_js", "code": code}
        elif "type" in action and "selector" in action:
            # Handle typing action
            return {
                "type": "type",
                "cssSelector": action.get("selector"),
                "text": action.get("text", "")
            }
        return action

