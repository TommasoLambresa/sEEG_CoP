"""Saving: one folder per session."""

from datetime import datetime
from pathlib import Path

from cop import config


def make_session_folder(patient_id: str) -> Path:
    # Date and time in the name: folders sort by time and never overwrite each other
    session_folder = config.SAVE_DIR / f"{patient_id}_{datetime.now():%Y%m%d_%H%M%S}"
    session_folder.mkdir(parents=True)
    return session_folder