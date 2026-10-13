# init_db_runner.py

import sys
from pathlib import Path
from app.db import engine
from app.models import Base


# Ensure app is importable even when running this file directly
sys.path.append(str(Path(__file__).parent))

from app.db import init_db

if __name__ == "__main__":
    print("🔧 Initializing the TuitorIN database...")
    init_db()
    print("✅ Database initialized successfully.")
