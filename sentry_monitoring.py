# sentry_monitoring.py

import os
from dotenv import load_dotenv
import sentry_sdk

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()
SENTRY_DSN = os.getenv("SENTRY_DSN")

def init_sentry(environment: str = "production"):
    """
    Initializes Sentry for cloud-based error logging.
    
    Parameters:
    - environment: str — "production" or "development"
    """
    if SENTRY_DSN and SENTRY_DSN.strip().lower() != "your_sentry_dsn":
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            environment=environment,
            send_default_pii=True
        )
        print("✅ Sentry initialized in", environment, "mode.")
    else:
        print("⚠️ Sentry DSN not found or invalid in .env. Skipping cloud error logging.")
