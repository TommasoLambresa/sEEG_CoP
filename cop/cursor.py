"""Cursor sources: read() returns x and y in cm and the time of the sample."""

import pygame
from pylsl import local_clock


class MouseCursor:
    def __init__(self, screen_size: tuple[int, int], px_per_cm: float):
        self.screen_center_x_px = screen_size[0] / 2
        self.screen_center_y_px = screen_size[1] / 2
        # Same scale as the display: the task cursor stays under the hidden pointer
        self.px_per_cm = px_per_cm
        pygame.mouse.set_visible(False)
        # Keep the pointer inside the window, otherwise set_pos is ignored when it starts on another monitor
        pygame.event.set_grab(True)
        pygame.mouse.set_pos(round(self.screen_center_x_px), round(self.screen_center_y_px))

    def read(self) -> tuple[float, float, float]:
        x_px, y_px = pygame.mouse.get_pos()
        x_cm = (x_px - self.screen_center_x_px) / self.px_per_cm
        y_cm = (self.screen_center_y_px - y_px) / self.px_per_cm
        return x_cm, y_cm, local_clock()


def make_cursor(source_name: str, screen_size: tuple[int, int], display_gain_px_per_cm: float) -> MouseCursor:
    if source_name == "mouse":
        return MouseCursor(screen_size, display_gain_px_per_cm)
    if source_name == "force_plate":
        raise NotImplementedError("The force plate cursor is not available yet.")
    raise ValueError(f"Unknown cursor source: {source_name}")