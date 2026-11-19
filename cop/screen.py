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
        "rest": "Rest",
        "finished": "Finished, thank you!",
        "get_ready": "Get ready",
        "stand_still": "Stand still",
        "lean": "Lean toward the arrow as far as you can (press Space when steady)",
        "hold": "Hold still",
        "back_to_center": "Come back to the center",
        "ok": "OK",
        "too_fast": "Too fast",
        "too_slow": "Too slow",
        "nogo_fail": "Red center: do not move",
        "early_start": "Too early: wait for the green center",
        "no_start": "Start sooner",
        "unstable_hold": "Stay still in the center",
        "fast": "Fast",
        "slow": "Slow",
    },
    "zh": {
        "language_name": "中文",
        "rest": "休息一下",
        "finished": "结束了，谢谢！",
        "get_ready": "准备",
        "stand_still": "站稳不动",
        "lean": "尽量向箭头方向倾斜（稳定后按空格键）",
        "hold": "保持不动",
        "back_to_center": "回到中心",
        "ok": "很好",
        "too_fast": "太快了",
        "too_slow": "太慢了",
        "nogo_fail": "中心变红：不要动",
        "early_start": "太早了：等中心变绿再动",
        "no_start": "请早点开始",
        "unstable_hold": "请在中心保持不动",
        "fast": "快",
        "slow": "慢",
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


def load_font(window: pygame.Surface, size_px: int) -> pygame.font.Font:
    font_path = Path(os.environ["WINDIR"]) / "Fonts" / config.FONT_FILE_NAME
    if not font_path.exists():
        raise FileNotFoundError(f"Font not found: {font_path}. Set FONT_FILE_NAME in cop/config.py.")
    return pygame.font.Font(font_path, geometry.scaled_px(size_px, window.get_size()))


def draw_circle(window: pygame.Surface, color: tuple, x_cm: float, y_cm: float, radius_cm: float, filled: bool,
                gain_px_per_cm: float):
    center_px = geometry.cm_to_pixels(x_cm, y_cm, window.get_size(), gain_px_per_cm)
    radius_px = geometry.cm_length_to_pixels(radius_cm, gain_px_per_cm)
    line_width_px = 0 if filled else geometry.scaled_px(config.OUTLINE_WIDTH_PX, window.get_size())
    pygame.draw.circle(window, color, center_px, radius_px, line_width_px)


def draw_cursor(window: pygame.Surface, x_cm: float, y_cm: float, gain_px_per_cm: float):
    screen_width, screen_height = window.get_size()
    x_px, y_px = geometry.cm_to_pixels(x_cm, y_cm, (screen_width, screen_height), gain_px_per_cm)
    radius_px = geometry.cm_length_to_pixels(config.CURSOR_RADIUS_CM, gain_px_per_cm)
    # Keep the drawn cursor on the screen; the position given in cm is not changed
    x_px = min(max(x_px, radius_px), screen_width - radius_px)
    y_px = min(max(y_px, radius_px), screen_height - radius_px)
    pygame.draw.circle(window, config.CURSOR_COLOR, (x_px, y_px), radius_px)
    # Dark edge: the cursor stays visible also on a target of similar color
    edge_px = geometry.scaled_px(config.OUTLINE_WIDTH_PX, (screen_width, screen_height))
    pygame.draw.circle(window, config.BACKGROUND_COLOR, (x_px, y_px), radius_px, edge_px)


def draw_ghost(window: pygame.Surface, x_cm: float, y_cm: float, gain_px_per_cm: float):
    # Semi-transparent cursor that shows the movement at the required speed
    x_px, y_px = geometry.cm_to_pixels(x_cm, y_cm, window.get_size(), gain_px_per_cm)
    radius_px = geometry.cm_length_to_pixels(config.CURSOR_RADIUS_CM, gain_px_per_cm)
    # Drawn on its own transparent image, then copied on the window: only this way the window shows through
    ghost_image = pygame.Surface((2 * radius_px, 2 * radius_px), pygame.SRCALPHA)
    pygame.draw.circle(ghost_image, (*config.CURSOR_COLOR, config.GHOST_ALPHA), (radius_px, radius_px), radius_px)
    window.blit(ghost_image, (x_px - radius_px, y_px - radius_px))


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
    line_width_px = geometry.scaled_px(config.ARROW_WIDTH_PX, window.get_size())
    pygame.draw.line(window, config.ARROW_COLOR, (center_x_px, center_y_px), edge_px, line_width_px)
    # Arrow tip halfway between the center and the edge
    tip_x_px = (center_x_px + edge_px[0]) / 2
    tip_y_px = (center_y_px + edge_px[1]) / 2
    head_px = geometry.scaled_px(config.ARROW_HEAD_PX, window.get_size())
    head_base_x = tip_x_px - step_x * head_px
    head_base_y = tip_y_px - step_y * head_px
    half_head_px = head_px / 2
    # Head: the tip plus two corners on the line perpendicular to the direction
    pygame.draw.polygon(window, config.ARROW_COLOR, [
        (tip_x_px, tip_y_px),
        (head_base_x - step_y * half_head_px, head_base_y + step_x * half_head_px),
        (head_base_x + step_y * half_head_px, head_base_y - step_x * half_head_px),
    ])


def draw_text(window: pygame.Surface, font: pygame.font.Font, text: str, color: tuple = config.TEXT_COLOR):
    # Patient texts always in the same place, below the CoP center, where there are no targets
    text_image = font.render(text, True, color)
    center_px = (window.get_width() // 2, round(config.TEXT_Y_FRACTION * window.get_height()))
    window.blit(text_image, text_image.get_rect(center=center_px))


def draw_time_bar(window: pygame.Surface, movement_time_s: float, correct_range_s: tuple[float, float],
                  zone_color: tuple):
    # Bar from 0 to MOVEMENT_TIMEOUT_S: correct range in the speed color, white mark at the movement time
    screen_width, screen_height = window.get_size()
    bar_width_px = config.TIME_BAR_WIDTH_FRACTION * screen_width
    bar_height_px = geometry.scaled_px(config.TIME_BAR_HEIGHT_PX, window.get_size())
    left_px = (screen_width - bar_width_px) / 2
    top_px = config.TIME_BAR_Y_FRACTION * screen_height - bar_height_px / 2
    px_per_s = bar_width_px / config.MOVEMENT_TIMEOUT_S
    shortest_s, longest_s = correct_range_s
    pygame.draw.rect(window, config.TIME_BAR_COLOR, (left_px, top_px, bar_width_px, bar_height_px))
    pygame.draw.rect(window, zone_color,
                     (left_px + shortest_s * px_per_s, top_px, (longest_s - shortest_s) * px_per_s, bar_height_px))
    # The mark sticks out above and below the bar, so it is visible on any color
    mark_x_px = left_px + min(movement_time_s, config.MOVEMENT_TIMEOUT_S) * px_per_s
    pygame.draw.line(window, config.TEXT_COLOR, (mark_x_px, top_px - bar_height_px / 2),
                     (mark_x_px, top_px + 1.5 * bar_height_px), max(2, bar_height_px // 3))


def target_area_px(window: pygame.Surface, text_font: pygame.font.Font,
                   hint_font: pygame.font.Font) -> tuple[float, float]:
    # Top and bottom of the screen part left to the center and the targets: below the operator keys (always
    # shown), above the patient texts. The operator information may cover a target: Tab hides it
    top_px = 0
    if config.SHOW_OPERATOR_OVERLAY:
        top_px = geometry.scaled_px(config.OVERLAY_EDGE_PX, window.get_size()) + hint_font.get_linesize()
    bottom_px = config.TEXT_Y_FRACTION * window.get_height() - text_font.get_height() / 2
    return top_px, bottom_px


def draw_overlay(window: pygame.Surface, hint_font: pygame.font.Font, overlay_font: pygame.font.Font, lines: list[str],
                 warning_lines: list[str], operator_hint: str, show_info: bool):
    # Keys for the operator centered at the top, always; below, only if show_info (key Tab), information in gray
    # and problems in red
    edge_px = geometry.scaled_px(config.OVERLAY_EDGE_PX, window.get_size())
    hint_image = hint_font.render(operator_hint, True, config.OVERLAY_HINT_COLOR)
    window.blit(hint_image, hint_image.get_rect(midtop=(window.get_width() // 2, edge_px)))
    if not show_info:
        return
    colored_lines = [(line, config.OVERLAY_COLOR) for line in lines]
    colored_lines += [(line, config.OVERLAY_WARNING_COLOR) for line in warning_lines]
    # One empty row below the keys, so the two never overlap
    top_px = edge_px + hint_font.get_linesize() + overlay_font.get_linesize()
    for line_index, (line, color) in enumerate(colored_lines):
        line_image = overlay_font.render(line, True, color)
        window.blit(line_image, (edge_px, top_px + line_index * overlay_font.get_linesize()))


def flip() -> float:
    # With vsync, flip waits for the screen refresh: the time right after it is when the frame is sent to the screen
    pygame.display.flip()
    return local_clock()