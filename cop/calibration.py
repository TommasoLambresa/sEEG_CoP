"""Calibration: center and limits from cursor samples, target distances, calibration.json."""

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np

from cop import config, geometry


def center_from_samples(samples: list) -> dict:
    # samples: (x_cm, y_cm) while standing still
    samples_xy = np.array(samples)
    mean_x_cm, mean_y_cm = samples_xy.mean(axis=0)
    sd_x_cm, sd_y_cm = samples_xy.std(axis=0)
    return {"x_cm": float(mean_x_cm), "y_cm": float(mean_y_cm), "sd_x_cm": float(sd_x_cm), "sd_y_cm": float(sd_y_cm)}


def make_calibration(center: dict, hold_samples_by_direction: dict) -> dict:
    # hold_samples_by_direction: {direction_deg: [samples of each repetition]}
    reached_cm = {}
    for direction_deg, repetitions in hold_samples_by_direction.items():
        unit_vector = np.array([math.cos(math.radians(direction_deg)), math.sin(math.radians(direction_deg))])
        # Distance reached along the direction: mean hold position, from the center, projected on the direction
        reached_cm[direction_deg] = [
            float((np.mean(samples, axis=0) - [center["x_cm"], center["y_cm"]]) @ unit_vector)
            for samples in repetitions
        ]
    limits_cm = {direction_deg: max(values_cm) for direction_deg, values_cm in reached_cm.items()}
    minimum_cm = geometry.min_target_distance_cm()
    directions = {}
    for direction_deg, limit_cm in limits_cm.items():
        # Symmetric pairs (0 and 180, 45 and 135): same distance on both sides, from the smaller limit of the pair
        pair_limit_cm = min(limit_cm, limits_cm.get(180 - direction_deg, limit_cm))
        distance_cm = config.TARGET_FRACTION * pair_limit_cm
        directions[direction_deg] = {
            "reached_cm": reached_cm[direction_deg],
            "limit_cm": limit_cm,
            "target_distance_cm": max(distance_cm, minimum_cm),
            "raised_to_minimum": distance_cm < minimum_cm,
        }
    return {
        "time": datetime.now().isoformat(timespec="seconds"),
        "center": center,
        "minimum_target_distance_cm": minimum_cm,
        "directions": directions,
    }


def save_calibrations(session_folder: Path, session: dict, calibrations: list):
    # Rewritten after every calibration: all calibrations of the session plus a copy of every config constant
    settings = {name: value for name, value in vars(config).items() if name.isupper()}
    content = {"session": session, "calibrations": calibrations, "config": settings}
    text = json.dumps(content, indent=2, ensure_ascii=False, default=str)  # default=str turns paths into text
    (session_folder / "calibration.json").write_text(text, encoding="utf-8")