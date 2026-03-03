import logging
import os

logger = logging.getLogger("hx_test")


def save_download(download, output_dir: str) -> str:
    """Save a Playwright Download object to output_dir and return the path."""
    os.makedirs(output_dir, exist_ok=True)
    filename = download.suggested_filename
    dest = os.path.join(output_dir, filename)
    download.save_as(dest)
    logger.info("Saved download: %s", dest)
    return dest
