"""Cursor sources: read() returns x and y in cm and the time of the sample."""

import pygame
from pylsl import local_clock

from cop import geometry


class MouseCursor:
    def __init__(self, screen_size: tuple[int, int], px_per_cm: float):
        # The pointer on the screen point where CoP (0, 0) is drawn reads (0, 0) cm
        self.center_x_px, self.center_y_px = geometry.center_px(screen_size)
        self.px_per_cm = px_per_cm
        pygame.mouse.set_visible(False)
        # Keep the pointer inside the window, otherwise set_pos is ignored when it starts on another monitor
        pygame.event.set_grab(True)
        self.recenter(0.0, 0.0)

    def read(self) -> tuple[float, float, float]:
        x_px, y_px = pygame.mouse.get_pos()
        x_cm = (x_px - self.center_x_px) / self.px_per_cm
        y_cm = (self.center_y_px - y_px) / self.px_per_cm
        return x_cm, y_cm, local_clock()

    def recenter(self, x_cm: float, y_cm: float):
        # Moves the pointer where read() gives (x_cm, y_cm): key R during tests
        pygame.mouse.set_pos(round(self.center_x_px + x_cm * self.px_per_cm),
                             round(self.center_y_px - y_cm * self.px_per_cm))


def make_cursor(source_name: str, screen_size: tuple[int, int], display_gain_px_per_cm: float) -> MouseCursor:
    if source_name == "mouse":
        return MouseCursor(screen_size, display_gain_px_per_cm)
    if source_name == "force_plate":
        raise NotImplementedError("The force plate cursor is not available yet.")
    raise ValueError(f"Unknown cursor source: {source_name}")