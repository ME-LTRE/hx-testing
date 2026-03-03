"""One-time login helper.

Run this to open a browser, log in with Azure AD + MFA, and save the session.
Subsequent test runs will reuse the saved session automatically.

Usage:
    python login.py
"""

import os
from playwright.sync_api import sync_playwright
from config.settings import BASE_URL, BROWSER_PROFILE_DIR


def main():
    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_PROFILE_DIR,
            headless=False,
            accept_downloads=True,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded")

        if "login" in page.url or "authorize" in page.url or "accounts." in page.url:
            print("Complete the login in the browser window...")
            page.wait_for_url(
                lambda url: "www.longtailre.hxrenew.com" in url
                            and "authorize" not in url
                            and "login" not in url
                            and "accounts." not in url,
                timeout=120_000,
            )
            print("Login successful — session saved to .browser_profile/")
        else:
            print("Already authenticated — session is valid.")

        page.close()
        context.close()


if __name__ == "__main__":
    main()
