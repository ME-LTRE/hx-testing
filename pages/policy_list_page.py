"""Page object for the policy list view (steps 1-7)."""

import logging

from playwright.sync_api import Page

logger = logging.getLogger("hx_test")


class PolicyListPage:
    def __init__(self, page: Page):
        self.page = page

    # Step 1 — click "Test Policies" in the sidebar
    def navigate_to_test_policies(self):
        logger.info("Step 1: clicking 'Test Policies' in sidebar")
        self.page.get_by_role("link", name="Test Policies").click()
        self.page.wait_for_load_state("networkidle")

    # Step 2 — click "+ Create Test Policy"
    def click_create_test_policy(self):
        logger.info("Step 2: clicking '+ Create Test Policy'")
        self.page.get_by_role("button", name="Create Test Policy").click()
        # Wait for the dialog/modal to appear
        self.page.get_by_role("dialog").wait_for(state="visible")

    # Steps 3-6 operate inside the create-policy dialog
    @property
    def _dialog(self):
        return self.page.get_by_role("dialog")

    # Step 3 — enter policy name (label is "Name *" with required asterisk)
    def enter_policy_name(self, name: str):
        logger.info("Step 3: entering policy name '%s'", name)
        self._dialog.get_by_label("Name").first.fill(name)

    # Step 4 — enter policy description
    def enter_policy_description(self, description: str):
        logger.info("Step 4: entering policy description '%s'", description)
        self._dialog.get_by_label("Description").fill(description)

    # Step 5 — set inception and expiry dates
    # The date fields are <input type="text"> with aria-labels.
    # React controlled component needs character-by-character typing to trigger
    # proper state updates (fill() only sets DOM value).
    def set_dates(self, inception: str, expiry: str):
        logger.info("Step 5: setting inception=%s, expiry=%s", inception, expiry)

        self._set_date_input("Inception date picker", inception)
        self._set_date_input("Expiry date picker", expiry)

    def _set_date_input(self, aria_label: str, date_value: str):
        """Select all, type a date character-by-character, then commit with Tab."""
        date_input = self.page.get_by_label(aria_label)
        date_input.click()
        # Select all existing text, then type replacement (fires React events)
        date_input.press("Control+a")
        date_input.press_sequentially(date_value, delay=50)
        # Tab commits the value and moves focus (Enter would submit the form)
        date_input.press("Tab")

    # Step 5a — set model version
    def set_model_version(self, version: str):
        logger.info("Step 5a: setting model version '%s'", version)
        self._dialog.get_by_label("Model Version").click()
        self.page.get_by_role("option", name=version).click()

    # Step 6 — click Create
    def click_create(self):
        logger.info("Step 6: clicking 'Create'")
        self._dialog.get_by_role("button", name="Create").click()
        self.page.wait_for_load_state("networkidle")

    # Step 7 — click the "Open Policy Option" icon (↗) in the options table row.
    # This opens in a NEW TAB. Returns the new Page object.
    def click_open_policy_option(self, context) -> "Page":
        logger.info("Step 7: clicking 'Open Policy Option'")
        with context.expect_page() as new_page_info:
            self.page.get_by_role("link", name="Open Policy Option").click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("networkidle")
        # Wait for the app to fully connect and render content
        # (the page shows "Connecting to server..." before content loads)
        new_page.get_by_text("Cedant Data Request").wait_for(
            state="visible", timeout=60000
        )
        logger.info("Step 7: switched to new tab — %s", new_page.url)
        return new_page
