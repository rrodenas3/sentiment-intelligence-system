"""Run YouTube comment ingestion -> sentiment pipeline (Slice A). Usage: PYTHONPATH=src python scripts/run_youtube_pipeline.py <video_id>"""
import os
import sys

# Allow running from repo root with PYTHONPATH=src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mswia.api.main import run_pipeline_youtube

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=src python scripts/run_youtube_pipeline.py <video_id>")
        print("Example: PYTHONPATH=src python scripts/run_youtube_pipeline.py dQw4w9WgXcQ")
        print("Set YOUTUBE_API_KEY in env.")
        sys.exit(1)
    video_id = sys.argv[1].strip()
    run_pipeline_youtube(video_id)
    print("Done. Check data/processed/ and GET /sentiment/summary or GET /stream/sentiment.")
