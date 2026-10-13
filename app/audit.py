import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

# ----------------------------
# Log File Path
# ----------------------------
LOG_FILE_PATH = Path("logs/audit_log.json")
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Configure Loguru to write to the JSON audit file
logger.add(
    str(LOG_FILE_PATH),
    format="{time} | {level} | {message}",
    level="INFO",
    rotation="1 MB",  # Rotate logs after size limit
    retention="10 days",  # Keep old logs for 10 days
    enqueue=True
)

# ----------------------------
# Log Change Utility
# ----------------------------
def log_action(user: str, action: str, details: str):
    """Log a specific user action to both Loguru + structured JSON"""
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "user": user,
        "action": action,
        "details": details
    }

    logger.info(json.dumps(entry))  # Log structured JSON for parsing
    return entry


# ----------------------------
# Read Logs
# ----------------------------
def read_audit_logs(limit: Optional[int] = None):
    """Read and return the audit logs"""
    logs = []

    if not LOG_FILE_PATH.exists():
        return []

    with open(LOG_FILE_PATH, "r") as f:
        for line in f:
            try:
                parts = line.strip().split("|", 2)
                if len(parts) == 3:
                    time_str, level, json_data = map(str.strip, parts)
                    entry = json.loads(json_data)
                    logs.append(entry)
            except Exception:
                continue  # Skip malformed lines

    logs.reverse()  # Show latest first
    return logs[:limit] if limit else logs
