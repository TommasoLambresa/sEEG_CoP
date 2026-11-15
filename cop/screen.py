"""Window, drawing and texts."""

import ctypes
import os
from pathlib import Path

import pygame
from pylsl import local_clock

from cop import config, geometry

TEXTS = {
    "en": {"quit_hint": "Press Esc to quit"},
    "zh": {"quit_hint": "按 Esc 键退出"},
}


def open_window() -> pygame.Surface:
    # Real pixel sizes on Windows even with display scaling (e.g. 125 %)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    # Direct3D 11 syncs to the monitor that shows the window; the default (Direct3D 9) syncs to the main monitor
    os.environ["SDL_RENDER_DRIVER"] = "direct3d11"
    pygame.init()
    desktop_sizes = pygame.display.get_desktop_sizes()
    if config.SCREEN_INDEX >= len(desktop_sizes):
        raise ValueError(
            f"SCREEN_INDEX = {config.SCREEN_INDEX}, but only {len(desktop_sizes)} monitor(s) found. Set it in cop/config.py."
        )
    screen_size = desktop_sizes[config.SCREEN_INDEX]    # In pygame 2 vsync works only together with the SCALED flag
    return pygame.display.set_mode(
        screen_size, pygame.FULLSCREEN | pygame.SCALED, vsync=1, display=config.SCREEN_INDEX
    )


def monitor_refresh_hz() -> int:
    # Needed to take the actual refresh rate of the monitor into account, 
    # which can be if multiple monitors are used. The refresh rate of the 
    # monitor that shows the window is used for vsync.
    sdl = ctypes.CDLL(str(Path(pygame.__file__).parent / "SDL2.dll"))
    # SDL_DisplayMode fits in 6 ints: format, width, height, refresh rate, then a pointer
    display_mode = (ctypes.c_int * 6)()
    sdl.SDL_GetDesktopDisplayMode(config.SCREEN_INDEX, ctypes.byref(display_mode))
    return display_mode[3]


def load_font(size_px: int) -> pygame.font.Font:
    font_path = Path(os.environ["WINDIR"]) / "Fonts" / config.FONT_FILE_NAME
    if not font_path.exists():
        raise FileNotFoundError(f"Font not found: {font_path}. Set FONT_FILE_NAME in cop/config.py.")
    return pygame.font.Font(font_path, size_px)


def draw_circle(window: pygame.Surface, color: tuple, x_cm: float, y_cm: float, radius_cm: float, filled: bool,
                gain_px_per_cm: float):
    center_px = geometry.cm_to_pixels(x_cm, y_cm, window.get_size(), gain_px_per_cm)
    radius_px = geometry.cm_length_to_pixels(radius_cm, gain_px_per_cm)
    line_width_px = 0 if filled else config.OUTLINE_WIDTH_PX
    pygame.draw.circle(window, color, center_px, radius_px, line_width_px)


def draw_cursor(window: pygame.Surface, x_cm: float, y_cm: float, gain_px_per_cm: float):
    screen_width, screen_height = window.get_size()
    x_px, y_px = geometry.cm_to_pixels(x_cm, y_cm, (screen_width, screen_height), gain_px_per_cm)
    radius_px = geometry.cm_length_to_pixels(config.CURSOR_RADIUS_CM, gain_px_per_cm)
    # Keep the drawn cursor on the screen; the position given in cm is not changed
    x_px = min(max(x_px, radius_px), screen_width - radius_px)
    y_px = min(max(y_px, radius_px), screen_height - radius_px)
    pygame.draw.circle(window, config.CURSOR_COLOR, (x_px, y_px), radius_px)


def draw_text(window: pygame.Surface, font: pygame.font.Font, text: str, center_px: tuple[int, int]):
    text_image = font.render(text, True, config.TEXT_COLOR)
    window.blit(text_image, text_image.get_rect(center=center_px))


def draw_overlay(window: pygame.Surface, font: pygame.font.Font, lines: list[str], color: tuple):
    for line_index, line in enumerate(lines):
        line_image = font.render(line, True, color)
        window.blit(line_image, (10, 10 + line_index * font.get_linesize()))


def flip() -> float:
    # With vsync, flip waits for the screen refresh: the time right after it is when the frame is sent to the screen
    pygame.display.flip()
    return local_clock()