"""Center-out task driven by the center of pressure; it will publish the task markers (for now: center, targets and cursor)."""

import argparse

import pygame

from cop import config, cursor, geometry, saving, screen

def main():
    parser = argparse.ArgumentParser(description="Center-out task driven by the center of pressure.")
    parser.add_argument("--source", default=config.CURSOR_SOURCE, choices=["mouse", "force_plate"])
    arguments = parser.parse_args()

    window = screen.open_window()
    screen_width, screen_height = window.get_size()
    monitor_hz = screen.monitor_refresh_hz()
    text_font = screen.load_font(config.TEXT_FONT_SIZE_PX)
    overlay_font = screen.load_font(config.OVERLAY_FONT_SIZE_PX)
    session_info = screen.ask_session_info(window, text_font)
    if session_info is None:
        pygame.quit()
        return
    patient_id, language = session_info
    session_folder = saving.make_session_folder(patient_id)
    target_positions = [
        geometry.target_position(direction_deg, config.DEFAULT_TARGET_DISTANCE_CM)
        for direction_deg in config.TARGET_DIRECTIONS_DEG
    ]
    # Computed once: the scale does not change during the trials
    display_gain = geometry.fit_display_gain(
        config.DEFAULT_TARGET_DISTANCE_CM + config.TARGET_RADIUS_CM, (screen_width, screen_height)
    )
    cursor_source = cursor.make_cursor(arguments.source, (screen_width, screen_height), display_gain)

    recent_flip_times = []
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        cursor_x_cm, cursor_y_cm, sample_time = cursor_source.read()

        window.fill(config.BACKGROUND_COLOR)
        in_center = geometry.inside_circle(cursor_x_cm, cursor_y_cm, 0.0, 0.0, config.CENTER_RADIUS_CM)
        screen.draw_circle(window, config.CENTER_COLOR, 0.0, 0.0, config.CENTER_RADIUS_CM, in_center, display_gain)
        for target_x_cm, target_y_cm in target_positions:
            in_target = geometry.inside_circle(cursor_x_cm, cursor_y_cm, target_x_cm, target_y_cm, config.TARGET_RADIUS_CM)
            screen.draw_circle(
                window, config.TARGET_COLOR, target_x_cm, target_y_cm, config.TARGET_RADIUS_CM, in_target, display_gain
            )
        screen.draw_cursor(window, cursor_x_cm, cursor_y_cm, display_gain)
        screen.draw_text(window, text_font, screen.TEXTS[language]["quit_hint"], (screen_width // 2, screen_height - 80))

        if config.SHOW_OPERATOR_OVERLAY and len(recent_flip_times) > 1:
            refresh_hz = (len(recent_flip_times) - 1) / (recent_flip_times[-1] - recent_flip_times[0])
            refresh_ok = abs(refresh_hz - monitor_hz) <= config.REFRESH_TOLERANCE_FRACTION * monitor_hz
            screen.draw_overlay(window, overlay_font, [
                f"session {session_folder.name}, language {language}",
                f"screen {screen_width} x {screen_height} px",
                f"refresh {refresh_hz:.1f} Hz (monitor {monitor_hz} Hz)",
                f"display gain {display_gain:.1f} px/cm (max {config.DISPLAY_GAIN_PX_PER_CM:.0f})",
                f"cursor x {cursor_x_cm:+.2f} cm, y {cursor_y_cm:+.2f} cm",
            ], config.OVERLAY_COLOR if refresh_ok else config.OVERLAY_WARNING_COLOR)

        recent_flip_times.append(screen.flip())
        recent_flip_times = recent_flip_times[-61:]

    pygame.quit()


if __name__ == "__main__":
    main()