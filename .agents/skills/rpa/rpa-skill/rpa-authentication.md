# RPA Authentication Module

Login automation patterns including username/password, OAuth, SSO, MFA handling, and session management.

## Basic Login Patterns

### Username/Password Login

```python
#!/usr/bin/env python3
"""Basic login automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Optional
from dataclasses import dataclass
import json


@dataclass
class LoginCredentials:
    """Login credentials."""
    username: str
    password: str
    totp_secret: Optional[str] = None


class LoginAutomator:
    """Handle login automation."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def basic_login(
        self,
        url: str,
        username_selector: str,
        password_selector: str,
        submit_selector: str,
        credentials: LoginCredentials,
        success_indicator: str = None
    ) -> bool:
        """Perform basic username/password login."""
        self.page.goto(url)
        
        # Fill credentials
        self.page.fill(username_selector, credentials.username)
        self.page.fill(password_selector, credentials.password)
        
        # Submit
        self.page.click(submit_selector)
        
        # Verify success
        if success_indicator:
            try:
                self.page.wait_for_selector(success_indicator, timeout=10000)
                return True
            except:
                return False
        else:
            self.page.wait_for_load_state("networkidle")
            return True
    
    def login_with_remember_me(
        self,
        url: str,
        credentials: LoginCredentials,
        remember_selector: str = "#remember-me"
    ) -> bool:
        """Login with remember me option."""
        self.page.goto(url)
        self.page.fill("#username", credentials.username)
        self.page.fill("#password", credentials.password)
        self.page.check(remember_selector)
        self.page.click("button[type=submit]")
        self.page.wait_for_load_state("networkidle")
        return True
    
    def handle_login_error(self) -> Optional[str]:
        """Check for and return login error message."""
        error_selectors = [
            ".error-message",
            ".alert-danger",
            "#login-error",
            "[role=alert]",
        ]
        
        for selector in error_selectors:
            error = self.page.locator(selector)
            if error.is_visible():
                return error.text_content().strip()
        
        return None
    
    def wait_for_redirect(self, expected_url_pattern: str, timeout: int = 30000) -> bool:
        """Wait for post-login redirect."""
        try:
            self.page.wait_for_url(expected_url_pattern, timeout=timeout)
            return True
        except:
            return False


def example_basic_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        automator = LoginAutomator(page)
        credentials = LoginCredentials(username="demo", password="demo123")
        
        success = automator.basic_login(
            url="https://the-internet.herokuapp.com/login",
            username_selector="#username",
            password_selector="#password",
            submit_selector="button[type=submit]",
            credentials=credentials,
            success_indicator=".flash.success"
        )
        
        print(f"Login successful: {success}")
        browser.close()


if __name__ == "__main__":
    example_basic_login()
```

---

## Multi-Factor Authentication

### TOTP (Google Authenticator)

```python
#!/usr/bin/env python3
"""MFA/TOTP handling - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
import pyotp
from typing import Optional


class MFAHandler:
    """Handle multi-factor authentication."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def generate_totp(self, secret: str) -> str:
        """Generate TOTP code from secret."""
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def enter_totp(self, selector: str, secret: str) -> bool:
        """Enter TOTP code."""
        code = self.generate_totp(secret)
        self.page.fill(selector, code)
        return True
    
    def enter_totp_digits(self, selector_pattern: str, secret: str):
        """Enter TOTP into separate digit inputs."""
        code = self.generate_totp(secret)
        
        for i, digit in enumerate(code):
            selector = selector_pattern.format(i=i)
            self.page.fill(selector, digit)
    
    def wait_for_new_totp(self, secret: str, current_code: str = None) -> str:
        """Wait for TOTP to refresh (if current is about to expire)."""
        totp = pyotp.TOTP(secret)
        
        if current_code is None:
            return totp.now()
        
        # Wait for new code
        import time
        while totp.now() == current_code:
            time.sleep(1)
        
        return totp.now()
    
    def handle_sms_mfa(self, code_input_selector: str, get_code_func) -> bool:
        """Handle SMS-based MFA."""
        # Wait for SMS code (implementation depends on how you receive it)
        code = get_code_func()
        self.page.fill(code_input_selector, code)
        return True
    
    def handle_backup_code(self, selector: str, backup_code: str) -> bool:
        """Enter backup/recovery code."""
        self.page.fill(selector, backup_code)
        return True
    
    def click_mfa_method(self, method: str):
        """Select MFA method when multiple available."""
        method_map = {
            "authenticator": "Use authenticator app",
            "sms": "Send SMS",
            "email": "Send email",
            "backup": "Use backup code",
        }
        
        if method in method_map:
            self.page.click(f"text={method_map[method]}")


def login_with_mfa(url: str, username: str, password: str, totp_secret: str):
    """Complete login flow with TOTP MFA."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Step 1: Login
        page.goto(url)
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("button[type=submit]")
        
        # Step 2: Handle MFA
        page.wait_for_selector("#totp-input")
        
        mfa = MFAHandler(page)
        mfa.enter_totp("#totp-input", totp_secret)
        page.click("#verify-button")
        
        # Step 3: Verify success
        page.wait_for_url("**/dashboard**")
        print("Login with MFA successful!")
        
        browser.close()


if __name__ == "__main__":
    # Example - replace with real values
    login_with_mfa(
        url="https://example.com/login",
        username="user@example.com",
        password="password123",
        totp_secret="JBSWY3DPEHPK3PXP"  # Base32 secret
    )
```

---

## OAuth/SSO Login

### OAuth 2.0 Flow

```python
#!/usr/bin/env python3
"""OAuth login handling - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Optional
from urllib.parse import urlparse, parse_qs


class OAuthHandler:
    """Handle OAuth/SSO login flows."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def google_login(self, email: str, password: str, totp_secret: str = None) -> bool:
        """Handle Google OAuth login."""
        # Wait for Google login page
        self.page.wait_for_url("**/accounts.google.com/**")
        
        # Enter email
        self.page.fill('input[type="email"]', email)
        self.page.click("#identifierNext")
        
        # Wait for password screen
        self.page.wait_for_selector('input[type="password"]', state="visible")
        self.page.fill('input[type="password"]', password)
        self.page.click("#passwordNext")
        
        # Handle 2FA if present
        if totp_secret:
            try:
                self.page.wait_for_selector('input[name="totpPin"]', timeout=5000)
                import pyotp
                code = pyotp.TOTP(totp_secret).now()
                self.page.fill('input[name="totpPin"]', code)
                self.page.click("#totpNext")
            except:
                pass  # No 2FA required
        
        # Wait for redirect back
        self.page.wait_for_url(lambda url: "google.com" not in url)
        return True
    
    def microsoft_login(self, email: str, password: str) -> bool:
        """Handle Microsoft OAuth login."""
        self.page.wait_for_url("**/login.microsoftonline.com/**")
        
        # Enter email
        self.page.fill('input[type="email"]', email)
        self.page.click('input[type="submit"]')
        
        # Wait for password
        self.page.wait_for_selector('input[type="password"]', state="visible")
        self.page.fill('input[type="password"]', password)
        self.page.click('input[type="submit"]')
        
        # Handle "Stay signed in?" prompt
        try:
            self.page.wait_for_selector('text="Stay signed in?"', timeout=5000)
            self.page.click('input[value="No"]')
        except:
            pass
        
        self.page.wait_for_url(lambda url: "microsoftonline.com" not in url)
        return True
    
    def github_login(self, username: str, password: str, totp_secret: str = None) -> bool:
        """Handle GitHub OAuth login."""
        self.page.wait_for_url("**/github.com/login**")
        
        self.page.fill("#login_field", username)
        self.page.fill("#password", password)
        self.page.click('input[type="submit"]')
        
        # Handle 2FA
        if totp_secret:
            try:
                self.page.wait_for_selector("#totp", timeout=5000)
                import pyotp
                code = pyotp.TOTP(totp_secret).now()
                self.page.fill("#totp", code)
            except:
                pass
        
        # Handle authorization if needed
        try:
            self.page.wait_for_selector('button[name="authorize"]', timeout=5000)
            self.page.click('button[name="authorize"]')
        except:
            pass
        
        return True
    
    def generic_sso(
        self,
        sso_button_selector: str,
        email_selector: str,
        password_selector: str,
        email: str,
        password: str
    ) -> bool:
        """Handle generic SSO/SAML login."""
        # Click SSO button on main app
        self.page.click(sso_button_selector)
        
        # Wait for SSO provider page
        self.page.wait_for_load_state("networkidle")
        
        # Enter credentials
        self.page.fill(email_selector, email)
        self.page.fill(password_selector, password)
        self.page.click('button[type="submit"]')
        
        # Wait for redirect back to app
        self.page.wait_for_load_state("networkidle")
        return True
    
    def extract_oauth_code(self) -> Optional[str]:
        """Extract OAuth authorization code from URL."""
        current_url = self.page.url
        parsed = urlparse(current_url)
        params = parse_qs(parsed.query)
        return params.get("code", [None])[0]


def oauth_login_example():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to app
        page.goto("https://example.com")
        
        # Click "Login with Google"
        page.click('button:has-text("Login with Google")')
        
        oauth = OAuthHandler(page)
        success = oauth.google_login(
            email="user@gmail.com",
            password="password123"
        )
        
        print(f"OAuth login successful: {success}")
        browser.close()


if __name__ == "__main__":
    oauth_login_example()
```

---

## Session Management

### Session Persistence

```python
#!/usr/bin/env python3
"""Session management - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, BrowserContext
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import json


class SessionManager:
    """Manage browser sessions with persistence."""
    
    def __init__(self, storage_dir: str = "./sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def _session_path(self, name: str) -> Path:
        return self.storage_dir / f"{name}.json"
    
    def _meta_path(self, name: str) -> Path:
        return self.storage_dir / f"{name}_meta.json"
    
    def save_session(self, context: BrowserContext, name: str, ttl_hours: int = 24):
        """Save browser session to file."""
        # Save storage state
        context.storage_state(path=str(self._session_path(name)))
        
        # Save metadata
        meta = {
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
            "ttl_hours": ttl_hours
        }
        
        with open(self._meta_path(name), "w") as f:
            json.dump(meta, f)
        
        print(f"Session '{name}' saved (expires in {ttl_hours} hours)")
    
    def load_session(self, browser, name: str) -> Optional[BrowserContext]:
        """Load saved session if valid."""
        session_path = self._session_path(name)
        meta_path = self._meta_path(name)
        
        if not session_path.exists():
            return None
        
        # Check expiration
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            
            expires_at = datetime.fromisoformat(meta["expires_at"])
            if datetime.now() > expires_at:
                print(f"Session '{name}' expired")
                self.delete_session(name)
                return None
        
        # Create context with saved state
        context = browser.new_context(storage_state=str(session_path))
        print(f"Session '{name}' loaded")
        return context
    
    def delete_session(self, name: str):
        """Delete saved session."""
        for path in [self._session_path(name), self._meta_path(name)]:
            if path.exists():
                path.unlink()
    
    def list_sessions(self) -> list[dict]:
        """List all saved sessions."""
        sessions = []
        
        for meta_path in self.storage_dir.glob("*_meta.json"):
            name = meta_path.stem.replace("_meta", "")
            
            with open(meta_path) as f:
                meta = json.load(f)
            
            expires_at = datetime.fromisoformat(meta["expires_at"])
            
            sessions.append({
                "name": name,
                "created_at": meta["created_at"],
                "expires_at": meta["expires_at"],
                "expired": datetime.now() > expires_at
            })
        
        return sessions
    
    def is_session_valid(self, name: str) -> bool:
        """Check if session exists and is not expired."""
        meta_path = self._meta_path(name)
        
        if not meta_path.exists():
            return False
        
        with open(meta_path) as f:
            meta = json.load(f)
        
        expires_at = datetime.fromisoformat(meta["expires_at"])
        return datetime.now() < expires_at


def session_workflow():
    """Login once, reuse session for subsequent runs."""
    session_mgr = SessionManager()
    session_name = "my_app_session"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Try to load existing session
        context = session_mgr.load_session(browser, session_name)
        
        if context:
            # Use existing session
            page = context.new_page()
            page.goto("https://example.com/dashboard")
            
            # Check if still logged in
            if page.locator("#logout-button").is_visible():
                print("Using cached session - already logged in!")
            else:
                print("Session expired, need to re-login")
                context.close()
                context = None
        
        if not context:
            # Fresh login required
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://example.com/login")
            page.fill("#username", "demo")
            page.fill("#password", "demo123")
            page.click("button[type=submit]")
            page.wait_for_url("**/dashboard**")
            
            # Save session for next time
            session_mgr.save_session(context, session_name, ttl_hours=8)
        
        # Continue with automation...
        page = context.pages[0] if context.pages else context.new_page()
        print(f"Current page: {page.url}")
        
        browser.close()


if __name__ == "__main__":
    session_workflow()
```

---

## Complete Login Framework

```python
#!/usr/bin/env python3
"""Complete login framework - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page, BrowserContext
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Any
from pathlib import Path
import json
import pyotp


class AuthMethod(Enum):
    BASIC = "basic"
    OAUTH_GOOGLE = "oauth_google"
    OAUTH_MICROSOFT = "oauth_microsoft"
    OAUTH_GITHUB = "oauth_github"
    SSO_SAML = "sso_saml"
    SSO_CUSTOM = "sso_custom"


@dataclass
class AuthConfig:
    """Authentication configuration."""
    method: AuthMethod
    login_url: str
    username: str
    password: str
    username_selector: str = "#username"
    password_selector: str = "#password"
    submit_selector: str = "button[type=submit]"
    success_url_pattern: str = "**/dashboard**"
    totp_secret: Optional[str] = None
    totp_selector: Optional[str] = None
    sso_button_selector: Optional[str] = None
    remember_me_selector: Optional[str] = None
    custom_steps: list[Callable] = field(default_factory=list)


class AuthenticationFramework:
    """Unified authentication framework."""
    
    def __init__(self, page: Page, session_dir: str = "./sessions"):
        self.page = page
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
    
    def authenticate(self, config: AuthConfig, use_cached: bool = True) -> bool:
        """Authenticate using config."""
        session_name = f"{config.method.value}_{config.username}"
        
        # Try cached session
        if use_cached and self._load_session(session_name):
            if self._verify_session(config.success_url_pattern):
                return True
        
        # Perform fresh login
        success = self._perform_login(config)
        
        if success:
            self._save_session(session_name)
        
        return success
    
    def _perform_login(self, config: AuthConfig) -> bool:
        """Perform login based on auth method."""
        self.page.goto(config.login_url)
        
        match config.method:
            case AuthMethod.BASIC:
                return self._basic_login(config)
            
            case AuthMethod.OAUTH_GOOGLE:
                return self._google_login(config)
            
            case AuthMethod.OAUTH_MICROSOFT:
                return self._microsoft_login(config)
            
            case AuthMethod.OAUTH_GITHUB:
                return self._github_login(config)
            
            case AuthMethod.SSO_SAML | AuthMethod.SSO_CUSTOM:
                return self._sso_login(config)
        
        return False
    
    def _basic_login(self, config: AuthConfig) -> bool:
        """Basic username/password login."""
        self.page.fill(config.username_selector, config.username)
        self.page.fill(config.password_selector, config.password)
        
        if config.remember_me_selector:
            self.page.check(config.remember_me_selector)
        
        self.page.click(config.submit_selector)
        
        # Handle MFA if configured
        if config.totp_secret and config.totp_selector:
            try:
                self.page.wait_for_selector(config.totp_selector, timeout=5000)
                code = pyotp.TOTP(config.totp_secret).now()
                self.page.fill(config.totp_selector, code)
                self.page.click(config.submit_selector)
            except:
                pass
        
        # Execute custom steps
        for step in config.custom_steps:
            step(self.page)
        
        # Verify success
        try:
            self.page.wait_for_url(config.success_url_pattern, timeout=30000)
            return True
        except:
            return False
    
    def _google_login(self, config: AuthConfig) -> bool:
        """Google OAuth login."""
        if config.sso_button_selector:
            self.page.click(config.sso_button_selector)
        
        self.page.wait_for_url("**/accounts.google.com/**")
        self.page.fill('input[type="email"]', config.username)
        self.page.click("#identifierNext")
        
        self.page.wait_for_selector('input[type="password"]', state="visible")
        self.page.fill('input[type="password"]', config.password)
        self.page.click("#passwordNext")
        
        if config.totp_secret:
            try:
                self.page.wait_for_selector('input[name="totpPin"]', timeout=5000)
                code = pyotp.TOTP(config.totp_secret).now()
                self.page.fill('input[name="totpPin"]', code)
                self.page.click("#totpNext")
            except:
                pass
        
        self.page.wait_for_url(config.success_url_pattern, timeout=30000)
        return True
    
    def _microsoft_login(self, config: AuthConfig) -> bool:
        """Microsoft OAuth login."""
        if config.sso_button_selector:
            self.page.click(config.sso_button_selector)
        
        self.page.wait_for_url("**/login.microsoftonline.com/**")
        self.page.fill('input[type="email"]', config.username)
        self.page.click('input[type="submit"]')
        
        self.page.wait_for_selector('input[type="password"]', state="visible")
        self.page.fill('input[type="password"]', config.password)
        self.page.click('input[type="submit"]')
        
        try:
            self.page.wait_for_selector('text="Stay signed in?"', timeout=3000)
            self.page.click('input[value="No"]')
        except:
            pass
        
        self.page.wait_for_url(config.success_url_pattern, timeout=30000)
        return True
    
    def _github_login(self, config: AuthConfig) -> bool:
        """GitHub OAuth login."""
        if config.sso_button_selector:
            self.page.click(config.sso_button_selector)
        
        self.page.wait_for_url("**/github.com/login**")
        self.page.fill("#login_field", config.username)
        self.page.fill("#password", config.password)
        self.page.click('input[type="submit"]')
        
        if config.totp_secret:
            try:
                self.page.wait_for_selector("#totp", timeout=5000)
                code = pyotp.TOTP(config.totp_secret).now()
                self.page.fill("#totp", code)
                self.page.click('button[type="submit"]')
            except:
                pass
        
        try:
            self.page.wait_for_selector('button[name="authorize"]', timeout=3000)
            self.page.click('button[name="authorize"]')
        except:
            pass
        
        self.page.wait_for_url(config.success_url_pattern, timeout=30000)
        return True
    
    def _sso_login(self, config: AuthConfig) -> bool:
        """Generic SSO login."""
        if config.sso_button_selector:
            self.page.click(config.sso_button_selector)
        
        self.page.wait_for_load_state("networkidle")
        self.page.fill(config.username_selector, config.username)
        self.page.fill(config.password_selector, config.password)
        self.page.click(config.submit_selector)
        
        self.page.wait_for_url(config.success_url_pattern, timeout=30000)
        return True
    
    def _save_session(self, name: str):
        """Save current session."""
        path = self.session_dir / f"{name}.json"
        self.page.context.storage_state(path=str(path))
    
    def _load_session(self, name: str) -> bool:
        """Load saved session."""
        path = self.session_dir / f"{name}.json"
        if not path.exists():
            return False
        
        # Need to recreate context - return False to signal fresh login needed
        # In practice, you'd create a new context with storage_state
        return False
    
    def _verify_session(self, expected_url_pattern: str) -> bool:
        """Verify session is still valid."""
        try:
            self.page.goto(expected_url_pattern.replace("**", ""))
            return True
        except:
            return False


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        auth = AuthenticationFramework(page)
        
        config = AuthConfig(
            method=AuthMethod.BASIC,
            login_url="https://the-internet.herokuapp.com/login",
            username="tomsmith",
            password="SuperSecretPassword!",
            success_url_pattern="**/secure**"
        )
        
        success = auth.authenticate(config)
        print(f"Authentication successful: {success}")
        
        browser.close()
```

---

## Best Practices

1. **Never hardcode credentials** - Use environment variables or secret managers
2. **Cache sessions** - Avoid repeated logins when possible
3. **Handle MFA gracefully** - Support TOTP, SMS, email verification
4. **Implement retry logic** - Handle temporary failures
5. **Monitor session expiration** - Refresh before timeout
6. **Use secure storage** - Encrypt saved sessions

---

**Next Module:** See **rpa-file-handling.md** for upload/download automation.
