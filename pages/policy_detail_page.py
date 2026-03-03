"""Page object for the policy option detail view (steps 8-16).

This page opens in a new tab from the policy overview.
Left nav: Cedant Data Request, Parameters, Premium Triangle, Incurred Triangle,
          Paid Triangle, Ultimate Triangle, Incurred Dev Graph, Paid Dev Graph,
          Projections, All Classes Dev Patterns, Summary, JSON View
"""

import logging
import os
from pathlib import Path

from playwright.sync_api import Page

from utils.downloads import save_download
from utils.timing import Timer

logger = logging.getLogger("hx_test")


class PolicyDetailPage:
    def __init__(self, page: Page, output_dir: str):
        self.page = page
        self.output_dir = output_dir

    def _click_nav(self, name: str):
        """Click a numbered item in the left sidebar nav."""
        self.page.get_by_text(name, exact=True).click()
        self.page.wait_for_load_state("networkidle")

    # Step 8 — fill cedant notes (rich text editor under "Cedant specific queries & to do's")
    def fill_cedant_notes(self, notes_text: str):
        logger.info("Step 8: filling cedant notes")
        editor = self.page.locator(".ProseMirror, .tiptap, [contenteditable], [role='textbox']").first
        editor.wait_for(state="visible", timeout=15000)
        editor.click()
        editor.type(notes_text)

    # Step 9 — click "Parameters" in left nav
    def navigate_to_parameters(self):
        logger.info("Step 9: clicking 'Parameters' in left nav")
        self._click_nav("Parameters")

    # Step 10 — upload file (TIMED)
    def upload_file(self, file_path: str) -> float:
        logger.info("Step 10: uploading file '%s'", file_path)
        abs_path = str(Path(file_path).resolve())

        with Timer("File Upload") as t:
            # Try hidden file input first, then file chooser
            file_input = self.page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.first.set_input_files(abs_path)
            else:
                with self.page.expect_file_chooser() as fc_info:
                    self.page.get_by_text("Choose File").click()
                file_chooser = fc_info.value
                file_chooser.set_files(abs_path)

            # Wait for upload completion
            self.page.wait_for_load_state("networkidle")

        return t.elapsed

    # Step 11 — load triangles from template excel (TIMED)
    def load_triangles_from_template(self) -> float:
        logger.info("Step 11: clicking 'Load Triangles from Template Excel'")

        with Timer("Load Triangles from Template Excel") as t:
            self.page.get_by_role("button", name="Load Triangles from Template Excel").click()

            # This triggers an async server task. Wait for it to complete.
            # The page shows "Locked by an async task" while processing.
            locked_text = self.page.get_by_text("Locked by an async task")
            locked_text.wait_for(state="visible", timeout=15000)
            logger.info("Async task started — waiting for completion...")
            locked_text.wait_for(state="hidden", timeout=120000)
            logger.info("Async task completed")

        return t.elapsed

    # Steps 12-14b — select triangle curve via left nav + searchable dropdown
    def select_triangle(self, nav_name: str):
        logger.info("Selecting first development pattern for '%s'", nav_name)
        self._click_nav(nav_name)
        # Open the "Selected Development Pattern" searchable dropdown
        dropdown = self.page.get_by_role("button", name="Selected Development Pattern")
        dropdown.click()

        # Select the first available option from the list
        option = self.page.get_by_role("option").first.or_(
            self.page.get_by_role("menuitem").first
        ).or_(
            self.page.locator("[class*='dropdown'] li, [class*='menu'] li").first
        )
        option.first.click()
        logger.info("Selected first option for '%s'", nav_name)

    def select_premium_triangle(self):
        logger.info("Step 12: Premium Triangle")
        self.select_triangle("Premium Triangle")

    def select_incurred_triangle(self):
        logger.info("Step 13: Incurred Triangle")
        self.select_triangle("Incurred Triangle")

    def select_paid_triangle(self):
        logger.info("Step 14: Paid Triangle")
        self.select_triangle("Paid Triangle")

    def select_projections_class(self):
        logger.info("Step 14b: Projections — selecting first class")
        self._click_nav("Projections")
        # Projections uses "Selected Class" dropdown, not "Selected Development Pattern"
        dropdown = self.page.get_by_role("button", name="Selected Class").or_(
            self.page.locator("select").first
        )
        dropdown.first.click()
        # Select first available option
        option = self.page.get_by_role("option").first
        option.click()
        logger.info("Selected first class for Projections")

    # Step 15 — Summary → Export Policy (async task, then download the result)
    def export_policy(self) -> str:
        logger.info("Step 15: Summary → Export Policy")
        self._click_nav("Summary")

        # Click "Export Policy" — triggers async task
        self.page.get_by_role("button", name="Export Policy").click()

        # Wait for the task to complete
        self.page.get_by_text("Task completed successfully").wait_for(
            state="visible", timeout=60000
        )
        logger.info("Export task completed")

        # Download the generated file by clicking its download icon
        with self.page.expect_download() as download_info:
            self.page.locator("a[download], [aria-label*='download'], [aria-label*='Download']").first.click()
        download = download_info.value
        return save_download(download, self.output_dir)

    # Step 16 — JSON View → Download JSON
    def download_json(self) -> str:
        logger.info("Step 16: JSON View → Download JSON")
        self._click_nav("JSON View")

        # Look for a download button/link on the JSON View page
        with self.page.expect_download() as download_info:
            self.page.get_by_role("button", name="Download JSON").or_(
                self.page.get_by_role("button", name="Download")
            ).or_(
                self.page.get_by_role("link", name="Download")
            ).first.click()
        download = download_info.value
        return save_download(download, self.output_dir)
