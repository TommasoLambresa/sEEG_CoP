"""Window, drawing and texts."""

import ctypes
import math
import os
from pathlib import Path

import pygame
from pylsl import local_clock

from cop import config, geometry

TEXTS = {
    "en": {
        "language_name": "English",
        "quit_hint": "Press Esc to quit",
        "get_ready": "Get ready",
        "stand_still": "Stand still",
        "lean": "Lean toward the arrow as far as you can (press Space when steady)",
        "hold": "Hold still",
        "back_to_center": "Come back to the center",
    },
    "zh": {
        "language_name": "中文",
        "quit_hint": "按 Esc 键退出",
        "get_ready": "准备",
        "stand_still": "站稳不动",
        "lean": "尽量向箭头方向倾斜（稳定后按空格键）",
        "hold": "保持不动",
        "back_to_center": "回到中心",
    },
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
    screen_size = desktop_sizes[config.SCREEN_INDEX]
    # In pygame 2 vsync works only together with the SCALED flag
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


def draw_arrow(window: pygame.Surface, direction_deg: float):
    center_x_px, center_y_px = geometry.center_px(window.get_size())
    # Unit vector of the direction on the screen (screen y grows downward)
    step_x = math.cos(math.radians(direction_deg))
    step_y = -math.sin(math.radians(direction_deg))
    # Line from the center to the window edge: a line longer than the window, cut by the window rectangle
    far_px = math.hypot(*window.get_size())
    _, edge_px = window.get_rect().clipline(
        (center_x_px, center_y_px), (center_x_px + step_x * far_px, center_y_px + step_y * far_px)
    )
    pygame.draw.line(window, config.ARROW_COLOR, (center_x_px, center_y_px), edge_px, config.ARROW_WIDTH_PX)
    # Arrow tip halfway between the center and the edge
    tip_x_px = (center_x_px + edge_px[0]) / 2
    tip_y_px = (center_y_px + edge_px[1]) / 2
    head_base_x = tip_x_px - step_x * config.ARROW_HEAD_PX
    head_base_y = tip_y_px - step_y * config.ARROW_HEAD_PX
    half_head_px = config.ARROW_HEAD_PX / 2
    # Head: the tip plus two corners on the line perpendicular to the direction
    pygame.draw.polygon(window, config.ARROW_COLOR, [
        (tip_x_px, tip_y_px),
        (head_base_x - step_y * half_head_px, head_base_y + step_x * half_head_px),
        (head_base_x + step_y * half_head_px, head_base_y - step_x * half_head_px),
    ])


def draw_text(window: pygame.Surface, font: pygame.font.Font, text: str, center_px: tuple[int, int]):
    text_image = font.render(text, True, config.TEXT_COLOR)
    window.blit(text_image, text_image.get_rect(center=center_px))


def draw_overlay(window: pygame.Surface, font: pygame.font.Font, lines: list[str], warning_lines: list[str]):
    # Information for the operator in gray, problems in red below it
    colored_lines = [(line, config.OVERLAY_COLOR) for line in lines]
    colored_lines += [(line, config.OVERLAY_WARNING_COLOR) for line in warning_lines]
    for line_index, (line, color) in enumerate(colored_lines):
        line_image = font.render(line, True, color)
        window.blit(line_image, (10, 10 + line_index * font.get_linesize()))


def flip() -> float:
    # With vsync, flip waits for the screen refresh: the time right after it is when the frame is sent to the screen
    pygame.display.flip()
    return local_clock()