# Browser Actions Documentation

## Overview

Browser actions allow you to automate interactions with web pages. They are specified in the `browserActions` array in your request payload.

## Common Properties (All Actions)

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `type` | string | required | The action type (see list below) |
| `when` | string | `"afterload"` | When to execute: `"beforeload"` or `"afterload"` |
| `ignoreErrors` | boolean | `false` | If `true`, errors won't stop execution |
| `timeout` | number | `60000` | Timeout in milliseconds |

---

## Action Types

### 1. `click` - Click an Element

Clicks on an element using CSS selector.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | Yes | CSS selector of element to click |
| `wait` | number | No | Wait time (ms) after clicking |
| `waitForSelector` | string | No | Wait for this selector after click |
| `direct` | boolean | No | Use direct click instead of cursor simulation |

**Example:**
```json
{
  "type": "click",
  "cssSelector": "#submit-button",
  "wait": 1000,
  "waitForSelector": ".success-message"
}
```

---

### 2. `type` - Type Text into Input

Types text into an input field with human-like delays.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | Yes | CSS selector of input element |
| `text` | string | Yes | Text to type |
| `wait` | number | No | Wait time (ms) after typing |
| `direct` | boolean | No | Use direct typing instead of cursor |

**Example:**
```json
{
  "type": "type",
  "cssSelector": "#username",
  "text": "myusername"
}
```

---

### 3. `goto` - Navigate to URL

Navigates the browser to a new URL.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | Yes | URL to navigate to |
| `wait` | number | No | Wait time (ms) after navigation |

**Example:**
```json
{
  "type": "goto",
  "url": "https://example.com/page2"
}
```

---

### 4. `wait` - Wait for Duration

Pauses execution for a specified time.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `wait` | number | Yes | Wait time in milliseconds |

**Example:**
```json
{
  "type": "wait",
  "wait": 2000
}
```

---

### 5. `wait_for_selector` - Wait for Element

Waits for an element to appear in the DOM.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | Yes | CSS selector to wait for |
| `timeout` | number | No | Timeout in ms (default: 60000) |

**Example:**
```json
{
  "type": "wait_for_selector",
  "cssSelector": ".loaded-content",
  "timeout": 30000
}
```

---

### 6. `wait_for_function` - Wait for JavaScript Condition

Waits until a JavaScript expression returns truthy.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `code` | string | Yes | JavaScript code that returns truthy when done |
| `timeout` | number | No | Timeout in ms (default: 60000) |

**Example:**
```json
{
  "type": "wait_for_function",
  "code": "window.dataLoaded === true",
  "timeout": 30000
}
```

---

### 7. `wait_for_load_state` - Wait for Page State

Waits for a specific page load state.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `waitForLoadState` | string | Yes | `"domcontentloaded"`, `"networkidle"`, or `"load"` |

**Example:**
```json
{
  "type": "wait_for_load_state",
  "waitForLoadState": "networkidle"
}
```

---

### 8. `wait_for_cookie` - Wait for Cookie

Waits for a specific cookie to be set.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cookieName` | string | Yes | Name of the cookie to wait for |
| `cookieValue` | string | No | Expected value of the cookie |
| `cookieDomain` | string | No | Domain the cookie should be set on |
| `pollIntervalMs` | number | No | Poll interval (default: 200ms) |
| `timeout` | number | No | Timeout in ms (default: 60000) |

**Example:**
```json
{
  "type": "wait_for_cookie",
  "cookieName": "session_id",
  "timeout": 30000
}
```

---

### 9. `execute_js` - Execute JavaScript

Executes JavaScript code on the page. Results are stored in `javascriptReturn` array.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `code` | string | Yes | JavaScript code to execute |
| `dontReturnValue` | boolean | No | If `true`, don't capture return value |

**Example:**
```json
{
  "type": "execute_js",
  "code": "document.querySelector('.price').innerText"
}
```

Access results in subsequent actions: `{javascriptReturn[0]}`

---

### 10. `scroll` - Scroll Page/Element

Scrolls to an element or the bottom of the page.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | No | Element to scroll to (if omitted, scrolls to bottom) |
| `repeat` | number | No | Number of times to repeat scroll |
| `delayMs` | number | No | Delay between scrolls (default: 100ms) |

**Example:**
```json
{
  "type": "scroll",
  "cssSelector": "#footer",
  "repeat": 3,
  "delayMs": 500
}
```

---

### 11. `hover` - Hover Over Element

Hovers the mouse over an element.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | Yes | CSS selector of element to hover |
| `timeout` | number | No | Timeout in ms |

**Example:**
```json
{
  "type": "hover",
  "cssSelector": ".dropdown-trigger"
}
```

---

### 12. `keyboard` - Press Keyboard Key

Simulates keyboard key presses.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `value` | string | Yes | Key to press (see values below) |
| `cssSelector` | string | No | Element to focus first (for `clear`) |
| `wait` | number | No | Wait time after pressing |
| `waitForSelector` | string | No | Wait for selector after pressing |

**Supported values:** `tab`, `enter`, `space`, `arrowdown`, `arrowup`, `arrowleft`, `arrowright`, `backspace`, `clear`

**Example:**
```json
{
  "type": "keyboard",
  "value": "enter"
}
```

---

### 13. `dropdown` - Select Dropdown Option

Selects an option from a dropdown/select element.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | Yes | CSS selector of select element |
| `index` | number | No* | Option index to select |
| `value` | string | No* | Option value to select |
| `wait` | number | No | Wait time after selection |
| `waitForSelector` | string | No | Wait for selector after selection |

*Either `index` or `value` is required.

**Example:**
```json
{
  "type": "dropdown",
  "cssSelector": "#country-select",
  "value": "US"
}
```

---

### 14. `switch_iframe` - Switch to iFrame

Switches context to an iframe for subsequent actions.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `cssSelector` | string | Yes | CSS selector of the iframe |

**Example:**
```json
{
  "type": "switch_iframe",
  "cssSelector": "#payment-iframe"
}
```

---

### 15. `set_viewport` - Set Browser Viewport

Changes the browser viewport size.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `width` | number | No | Viewport width (default: 1280) |
| `height` | number | No | Viewport height (default: 1024) |
| `wait` | number | No | Wait time after setting |

**Example:**
```json
{
  "type": "set_viewport",
  "width": 1920,
  "height": 1080
}
```

---

### 16. `if` - Conditional Execution

Executes actions conditionally based on JavaScript condition.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `condition` | string | Yes | JavaScript condition to evaluate |
| `then` | array | No | Actions to run if condition is true |
| `or` | array | No | Actions to run if condition is false |

**Example:**
```json
{
  "type": "if",
  "condition": "document.querySelector('.captcha') !== null",
  "then": [
    { "type": "solve_captcha", "captcha": "turnstile" }
  ],
  "or": [
    { "type": "click", "cssSelector": "#continue" }
  ]
}
```

---

### 17. `while` - Loop Execution

Loops actions while a condition is true.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `condition` | string | Yes | JavaScript condition to evaluate |
| `then` | array | Yes | Actions to run each iteration |
| `maxAttempts` | number | No | Maximum iterations (prevents infinite loops) |

**Example:**
```json
{
  "type": "while",
  "condition": "document.querySelector('.load-more') !== null",
  "then": [
    { "type": "click", "cssSelector": ".load-more" },
    { "type": "wait", "wait": 1000 }
  ],
  "maxAttempts": 10
}
```

---

### 18. `solve_captcha` - Solve Captcha

Solves various captcha types.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `captcha` | string | Yes | Captcha type (see list below) |
| `captchaData` | object | No | Additional captcha configuration |
| `websiteUrl` | string | No | Website URL (for some captcha types) |
| `websiteKey` | string | No | Site key (for some captcha types) |
| `cssSelector` | string | No | Captcha element selector |
| `inputSelector` | string | No | Input field for captcha answer |
| `clickSelector` | string | No | Submit button after solving |
| `iframeSelector` | string | No | iFrame containing captcha |
| `coreName` | string | No | Core name for custom captcha |

**Captcha Types:**
- `turnstile` - Cloudflare Turnstile
- `recaptcha` - Google reCAPTCHA v2
- `recaptchav2` - reCAPTCHA v2 with sitekey
- `recaptchav3` - reCAPTCHA v3
- `hcaptcha` - hCaptcha
- `hcaptcha_inside` - hCaptcha with sitekey
- `hcaptcha_enterprise_inside` - hCaptcha Enterprise
- `funcaptcha` - FunCaptcha/Arkose Labs
- `perimeterx` - PerimeterX
- `mtcaptcha` - MTCaptcha
- `mtcaptchaisolated` - MTCaptcha isolated
- `v4guard` - v4Guard captcha
- `custom` - Custom image captcha
- `fingerprintjscom` - FingerprintJS
- `fingerprintjs_curseforge` - FingerprintJS CurseForge

**captchaData options:**

| Property | Type | Description |
|----------|------|-------------|
| `sitekey` | string | Captcha site key |
| `action` | string | reCAPTCHA action |
| `pageAction` | string | reCAPTCHA v3 page action |
| `invisible` | boolean | Invisible captcha |
| `base64Image` | string | Base64 image for custom captcha |
| `cssSelector` | string | Turnstile container selector |
| `reset` | boolean | Reset captcha state before solving |
| `fast` | boolean | Use fast solving mode |

**Example:**
```json
{
  "type": "solve_captcha",
  "captcha": "turnstile",
  "captchaData": {
    "sitekey": "0x4AAAAAAA...",
    "cssSelector": ".cf-turnstile"
  }
}
```

---

### 19. `discord_login` - Discord Token Login

Logs into Discord using a token.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | string | Yes | Discord auth token |
| `direct` | boolean | No | Skip navigation to login page |
| `wait` | number | No | Wait time after login |
| `timeout` | number | No | Timeout for login (default: 60000) |

**Example:**
```json
{
  "type": "discord_login",
  "token": "your_discord_token"
}
```

---

### 20. `remove_iframes` - Remove All iFrames

Removes all iframes from the page (experimental).

**Example:**
```json
{
  "type": "remove_iframes"
}
```

---

## Using JavaScript Return Values

Results from `execute_js` are stored in the `javascriptReturn` array and can be referenced in subsequent actions:

```json
{
  "browserActions": [
    {
      "type": "execute_js",
      "code": "document.querySelector('.token').dataset.value"
    },
    {
      "type": "type",
      "cssSelector": "#input",
      "text": "{javascriptReturn[0]}"
    }
  ]
}
```

---

## Full Example

```json
{
  "cmd": "request.get",
  "url": "https://example.com",
  "browserActions": [
    {
      "type": "wait_for_selector",
      "cssSelector": "#login-form",
      "when": "afterload"
    },
    {
      "type": "type",
      "cssSelector": "#username",
      "text": "myuser"
    },
    {
      "type": "type",
      "cssSelector": "#password",
      "text": "mypassword"
    },
    {
      "type": "solve_captcha",
      "captcha": "turnstile"
    },
    {
      "type": "click",
      "cssSelector": "#submit",
      "waitForSelector": ".dashboard"
    },
    {
      "type": "execute_js",
      "code": "document.querySelector('.user-data').innerText"
    }
  ]
}
```

---

## Python Wrapper Usage

When using the `scrappey_wrapper`, you can use browser actions via `js_scenario`:

```python
from scrappey_wrapper import ScrapeConfig, ScrapflyClient

client = ScrapflyClient(key="your-api-key")

config = ScrapeConfig(
    url="https://example.com",
    js_scenario=[
        {"wait_for_selector": {"selector": "#content"}},
        {"click": {"selector": "#load-more"}},
        {"wait": 2000},
    ]
)

response = await client.async_scrape(config)
```

Or use the `wait_for_selector` parameter directly:

```python
config = ScrapeConfig(
    url="https://example.com",
    wait_for_selector="#main-content"
)
```

