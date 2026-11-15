"""Conversions and positions: the task works in cm, the screen in pixels."""

import math

from cop import config


def fit_display_gain(farthest_cm: float, screen_size: tuple[int, int]) -> float:
    # Largest gain that keeps a point farthest_cm away from the center inside the screen
    available_px = min(screen_size) / 2 - config.SCREEN_MARGIN_PX
    return min(config.DISPLAY_GAIN_PX_PER_CM, available_px / farthest_cm)


def cm_to_pixels(x_cm: float, y_cm: float, screen_size: tuple[int, int], gain_px_per_cm: float) -> tuple[int, int]:
    screen_width, screen_height = screen_size
    x_px = screen_width / 2 + x_cm * gain_px_per_cm
    # Screen y grows downward, CoP y grows forward
    y_px = screen_height / 2 - y_cm * gain_px_per_cm
    return round(x_px), round(y_px)


def cm_length_to_pixels(length_cm: float, gain_px_per_cm: float) -> int:
    return round(length_cm * gain_px_per_cm)


def target_position(direction_deg: float, distance_cm: float) -> tuple[float, float]:
    angle_rad = math.radians(direction_deg)
    return distance_cm * math.cos(angle_rad), distance_cm * math.sin(angle_rad)


def inside_circle(x_cm: float, y_cm: float, circle_x_cm: float, circle_y_cm: float, radius_cm: float) -> bool:
    # boolean, whether the point (x_cm, y_cm) is inside the circle with center (circle_x_cm, circle_y_cm) and radius radius_cm
    return math.hypot(x_cm - circle_x_cm, y_cm - circle_y_cm) <= radius_cm