import logging
import os

import pytest
from playwright.sync_api import Playwright, sync_playwright

from config.settings import BASE_URL, HEADLESS, SLOW_MO, BROWSER_PROFILE_DIR, OUTPUT_DIR

logger = logging.getLogger("hx_test")


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Ensure the hx_test logger is configured for the session."""
    hx_logger = logging.getLogger("hx_test")
    if not hx_logger.handlers:
        hx_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        hx_logger.addHandler(handler)


@pytest.fixture(scope="session")
def browser_context(playwright: Playwright):
    """Launch a persistent browser context that preserves login state across runs.

    On first run (or expired session), the browser opens visibly so you can
    complete the Azure AD login + MFA manually. Once authenticated, the session
    is stored in .browser_profile/ and reused for subsequent headless runs.
    """
    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=BROWSER_PROFILE_DIR,
        headless=HEADLESS,
        slow_mo=SLOW_MO,
        accept_downloads=True,
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")

    # If we landed on a login/auth page, need manual login
    if "login" in page.url or "authorize" in page.url or "accounts." in page.url:
        print("\n" + "=" * 60)
        print("MANUAL LOGIN REQUIRED")
        print("Complete the Azure AD login + MFA in the browser window.")
        print("The test will continue once you reach the app.")
        print("=" * 60 + "\n")

        # Re-launch as visible if currently headless
        if HEADLESS:
            page.close()
            context.close()
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=BROWSER_PROFILE_DIR,
                headless=False,
                slow_mo=SLOW_MO,
                accept_downloads=True,
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(BASE_URL, wait_until="domcontentloaded")

        # Wait up to 2 minutes for the user to complete login
        page.wait_for_url(
            lambda url: "www.longtailre.hxrenew.com" in url
                        and "authorize" not in url
                        and "login" not in url
                        and "accounts." not in url,
            timeout=120_000,
        )
        print("Login successful — session saved.\n")

    # Keep the initial page open — closing the last tab kills the persistent context
    yield context
    context.close()


@pytest.fixture()
def page(browser_context):
    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")
    yield page
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture a screenshot on test failure."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Try to grab the page from the test's fixtures.
        # The test manages its own screenshot in its except block,
        # so this hook captures ALL open pages for extra context.
        browser_context = item.funcargs.get("browser_context")
        if browser_context:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            for i, pg in enumerate(browser_context.pages):
                screenshot_path = os.path.join(
                    OUTPUT_DIR, f"failure_{item.name}_tab{i}.png"
                )
                try:
                    pg.screenshot(path=screenshot_path, full_page=True)
                    logger.info("Screenshot saved: %s", screenshot_path)
                except Exception as exc:
                    logger.warning("Could not capture screenshot for tab %d: %s", i, exc)
