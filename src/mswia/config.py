"""Config from env; paths for raw/processed data (Spec 001)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = Path(os.environ.get("DATA_RAW_DIR", str(BASE_DIR / "data" / "raw")))
DATA_PROCESSED_DIR = Path(os.environ.get("DATA_PROCESSED_DIR", str(BASE_DIR / "data" / "processed")))
MODELS_DIR = Path(os.environ.get("MODELS_DIR", str(BASE_DIR / "models")))

# Sentiment label thresholds (Spec 001)
SCORE_NEGATIVE_THRESHOLD = -0.05
SCORE_POSITIVE_THRESHOLD = 0.05

# Model version for output contract
SENTIMENT_MODEL_VERSION = os.environ.get("SENTIMENT_MODEL_VERSION", "vader-baseline-1.0")

# YouTube (optional)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# Reddit (optional)
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "mswia/1.0.0 (by /u/mswia)")
