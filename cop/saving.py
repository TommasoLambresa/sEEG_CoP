"""Saving: one folder per session."""

from datetime import datetime
from pathlib import Path


def make_session_folder(save_folder: Path, patient_id: str, session: str) -> Path:
    # Date and time in the name: folders sort by time and never overwrite each other
    session_folder = save_folder / f"{patient_id}_{session}_{datetime.now():%Y%m%d_%H%M%S}"
    session_folder.mkdir(parents=True)
    return session_folder