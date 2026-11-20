"""Saving: one folder per session, the events and cursor files, and the task markers on LSL."""

import csv
import json
from datetime import datetime
from pathlib import Path

from pylsl import IRREGULAR_RATE, StreamInfo, StreamOutlet

from cop import config

# events.csv: planned trials and markers, one row each; empty cells where a value does not apply
EVENT_COLUMNS = ["lsl_time", "event", "phase", "block", "trial", "attempt", "direction_deg", "speed", "nogo",
                 "wait_s", "reaction_time_s", "movement_time_s", "outcome", "reason"]
# cursor.csv: one row per frame; the trial fields stay empty at rest
CURSOR_COLUMNS = ["lsl_time", "phase", "block", "trial", "attempt", "x_cm", "y_cm"]
# Values also sent in the LSL marker, next to the event name
MARKER_KEYS = ["block", "trial", "attempt", "direction_deg", "speed", "nogo", "outcome", "reason"]


def make_session_folder(save_folder: Path, patient_id: str, session: str) -> Path:
    # Date and time in the name: folders sort by time and never overwrite each other
    session_folder = save_folder / f"{patient_id}_{session}_{datetime.now():%Y%m%d_%H%M%S}"
    session_folder.mkdir(parents=True)
    return session_folder


class Saver:
    def __init__(self, session_folder: Path | None):
        # Markers always go on LSL; the CSV files are written only when saving (session_folder not None)
        info = StreamInfo(config.MARKER_STREAM_NAME, "Markers", 1, IRREGULAR_RATE, "string",
                          config.MARKER_STREAM_NAME)
        self.outlet = StreamOutlet(info)
        self.files = {}
        self.writers = {}
        if session_folder is not None:
            for name, columns in [("events", EVENT_COLUMNS), ("cursor", CURSOR_COLUMNS)]:
                self.files[name] = (session_folder / f"{name}.csv").open("w", newline="", encoding="utf-8")
                # Each file keeps only its own columns: the other values are left out
                self.writers[name] = csv.DictWriter(self.files[name], columns, extrasaction="ignore")
                self.writers[name].writeheader()

    def marker(self, time_s: float, event: str, **values):
        # LSL marker with the given time (compact JSON), and the same event as a row of events.csv
        message = {"event": event} | {key: values[key] for key in MARKER_KEYS if values.get(key) is not None}
        self.outlet.push_sample([json.dumps(message, separators=(",", ":"))], time_s)
        self.row(time_s, event, **values)

    def row(self, time_s: float, event: str, **values):
        # Only in events.csv, not on LSL: the planned trials
        self.write("events", {"lsl_time": time_s, "event": event} | values)

    def cursor(self, time_s: float, **values):
        # One row per frame in cursor.csv
        self.write("cursor", {"lsl_time": time_s} | values)

    def write(self, name: str, row: dict):
        # Flushed at once: a crash loses nothing
        if name not in self.writers:
            return
        rounded = {key: round(value, 6) if isinstance(value, float) else value for key, value in row.items()}
        self.writers[name].writerow(rounded)
        self.files[name].flush()

    def close(self):
        for csv_file in self.files.values():
            csv_file.close()