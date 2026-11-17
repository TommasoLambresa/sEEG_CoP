"""Conversions and positions: the task works in cm, the screen in pixels."""

import math

from cop import config


def center_px(screen_size: tuple[int, int]) -> tuple[float, float]:
    # Screen point where CoP (0, 0) is drawn: lower than the middle, because all targets are above it
    return screen_size[0] / 2, screen_size[1] * config.CENTER_SCREEN_Y_FRACTION


def fit_display_gain(points_cm: list, screen_size: tuple[int, int]) -> float:
    # Largest gain (up to the maximum) that keeps every point, plus a target radius, inside the screen
    center_x_px, center_y_px = center_px(screen_size)
    gain = config.DISPLAY_GAIN_PX_PER_CM
    for x_cm, y_cm in points_cm:
        # Points are on the sides or above the center: check the space left or right, and the space above
        gain = min(gain, (center_x_px - config.SCREEN_MARGIN_PX) / (abs(x_cm) + config.TARGET_RADIUS_CM))
        gain = min(gain, (center_y_px - config.SCREEN_MARGIN_PX) / (y_cm + config.TARGET_RADIUS_CM))
    return gain


def min_target_distance_cm() -> float:
    # Smallest distance that keeps targets off the center circle and neighbouring targets apart
    directions_deg = sorted(config.TARGET_DIRECTIONS_DEG)
    smallest_angle_rad = math.radians(min(next_deg - deg for deg, next_deg in zip(directions_deg, directions_deg[1:])))
    off_center_cm = config.CENTER_RADIUS_CM + config.TARGET_RADIUS_CM + config.TARGET_GAP_CM
    # Two targets at distance d and angle a apart are 2 d sin(a / 2) from each other
    apart_cm = (2 * config.TARGET_RADIUS_CM + config.TARGET_GAP_CM) / (2 * math.sin(smallest_angle_rad / 2))
    return max(off_center_cm, apart_cm)


def cm_to_pixels(x_cm: float, y_cm: float, screen_size: tuple[int, int], gain_px_per_cm: float) -> tuple[int, int]:
    center_x_px, center_y_px = center_px(screen_size)
    x_px = center_x_px + x_cm * gain_px_per_cm
    # Screen y grows downward, CoP y grows forward
    y_px = center_y_px - y_cm * gain_px_per_cm
    return round(x_px), round(y_px)


def cm_length_to_pixels(length_cm: float, gain_px_per_cm: float) -> int:
    return round(length_cm * gain_px_per_cm)


def target_position(direction_deg: float, distance_cm: float) -> tuple[float, float]:
    angle_rad = math.radians(direction_deg)
    return distance_cm * math.cos(angle_rad), distance_cm * math.sin(angle_rad)


def inside_circle(x_cm: float, y_cm: float, circle_x_cm: float, circle_y_cm: float, radius_cm: float) -> bool:
    # boolean, whether the point (x_cm, y_cm) is inside the circle with center (circle_x_cm, circle_y_cm) and radius radius_cm
    return math.hypot(x_cm - circle_x_cm, y_cm - circle_y_cm) <= radius_cm