import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("HX_BASE_URL", "https://longtailre.hxrenew.com")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))

REFERENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reference")
BROWSER_PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".browser_profile")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
