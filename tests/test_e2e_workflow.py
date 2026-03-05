"""
End-to-end test: full Hx policy workflow.

Creates a policy, uploads data, configures triangles (if model supports them),
and exports results. All steps run sequentially in a single test because each
depends on the previous.
"""

import logging
import os
from datetime import datetime

import pytest

from config.settings import BASE_URL, REFERENCE_DIR, OUTPUT_DIR
from pages.policy_list_page import PolicyListPage
from pages.policy_detail_page import PolicyDetailPage

logger = logging.getLogger("hx_test")

POLICY_NAME = "AXIS_UY2026_Upload_Template_v8"
UPLOAD_FILENAME = "2025-v6/AXIS UY2026 - Upload Template v8.0.xlsx"
MODEL_VERSION = "2025-v6"


@pytest.mark.e2e
def test_full_hx_workflow(browser_context):
    """Complete policy workflow: create → upload → triangles → export."""

    page = browser_context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")

    now = datetime.now()
    runtime_date = now.strftime("%d/%m/%Y")
    runtime_time = now.strftime("%H:%M:%S")

    upload_path = os.path.join(REFERENCE_DIR, UPLOAD_FILENAME)
    assert os.path.isfile(upload_path), f"Reference file not found: {upload_path}"

    policy_list = PolicyListPage(page)
    option_page = None  # will be set in step 7

    try:
        # ── Steps 1-7: create policy and open option ──

        # Step 1: click "test policies" in sidebar
        policy_list.navigate_to_test_policies()

        # Step 2: click "+ Create Test Policy"
        policy_list.click_create_test_policy()

        # Step 3: enter policy name
        policy_list.enter_policy_name(POLICY_NAME)

        # Step 4: enter policy description
        policy_list.enter_policy_description(POLICY_NAME)

        # Step 5: set inception and expiry dates
        policy_list.set_dates("01/01/2026", "31/12/2026")

        # Step 5a: set model version
        policy_list.set_model_version(MODEL_VERSION)

        # Step 6: click Create
        policy_list.click_create()

        # Step 7: open the policy option (opens in new tab)
        option_page = policy_list.click_open_policy_option(browser_context)
        policy_detail = PolicyDetailPage(option_page, OUTPUT_DIR)

        # ── Steps 8-11: notes, parameters, upload ──

        # Step 8: fill cedant notes with runtime values
        notes = (
            f"Automated E2E test\n"
            f"Date: {runtime_date}\n"
            f"Time: {runtime_time}\n"
            f"File: {UPLOAD_FILENAME}"
        )
        policy_detail.fill_cedant_notes(notes)

        # Step 9: navigate to Parameters
        policy_detail.navigate_to_parameters()

        # Step 10: upload file (timed)
        upload_elapsed = policy_detail.upload_file(upload_path)
        logger.info("Upload completed in %.2fs", upload_elapsed)

        # Step 11: load triangles from template excel (timed)
        triangles_elapsed = policy_detail.load_triangles_from_template()
        logger.info("Load triangles completed in %.2fs", triangles_elapsed)

        # ── Steps 12-14b: triangle selection (only if model has triangle pages) ──

        has_triangles = option_page.get_by_text("Premium Triangle", exact=True).is_visible(timeout=3000)

        if has_triangles:
            logger.info("Triangle pages detected — selecting development patterns")

            # Step 12: Premium Triangle → select first available pattern
            policy_detail.select_premium_triangle()

            # Step 13: Incurred Triangle → select first available pattern
            policy_detail.select_incurred_triangle()

            # Step 14: Paid Triangle → select first available pattern
            policy_detail.select_paid_triangle()

            # Step 14b: Projections → select first available class
            policy_detail.select_projections_class()
        else:
            logger.info("No triangle pages for model %s — skipping steps 12-14b", MODEL_VERSION)

        # ── Steps 15-16: export ──

        has_summary = option_page.get_by_text("Summary", exact=True).is_visible(timeout=2000)

        if has_summary:
            # Step 15: Summary → Export Policy
            export_path = policy_detail.export_policy()
            assert os.path.isfile(export_path), f"Export file not found: {export_path}"
            logger.info("Policy exported to: %s", export_path)
        else:
            logger.info("No Summary page for model %s — skipping step 15", MODEL_VERSION)

        # Step 16: JSON View → Download JSON
        json_path = policy_detail.download_json()
        assert os.path.isfile(json_path), f"JSON file not found: {json_path}"
        logger.info("JSON downloaded to: %s", json_path)

        logger.info("All steps completed successfully")

    except Exception:
        # Capture screenshot on failure before re-raising
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        active_page = option_page or page
        screenshot_path = os.path.join(OUTPUT_DIR, "failure_test_full_hx_workflow.png")
        try:
            active_page.screenshot(path=screenshot_path, full_page=True)
            logger.error("Screenshot saved: %s", screenshot_path)
        except Exception as sc_exc:
            logger.warning("Could not capture screenshot: %s", sc_exc)
        raise

    finally:
        if option_page:
            option_page.close()
        page.close()
