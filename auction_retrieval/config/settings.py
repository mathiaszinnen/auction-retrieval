from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Default data directory
DATA_DIR = Path(
    os.getenv("AUCTION_RETRIEVAL_DATA_DIR", Path.home() / "auction_retrieval_data")
)

# Ensure the folder exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
