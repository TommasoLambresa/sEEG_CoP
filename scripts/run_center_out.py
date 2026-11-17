"""Center-out task driven by the center of pressure; it will publish the task markers (for now: calibration, center, targets and cursor)."""

import argparse
import sys

import pygame

from cop import calibration, config, cursor, geometry, saving, screen, start_window


def run_calibration(window: pygame.Surface, text_font: pygame.font.Font, overlay_font: pygame.font.Font,
                    cursor_source: cursor.MouseCursor, calibration_gain: float, language: str) -> dict:
    screen_width, screen_height = window.get_size()

    def run_phase(text_key: str, origin_cm: tuple[float, float], duration_s: float = 0.0, direction_deg=None,
                  wait_for_space: bool = False, wait_for_center: bool = False, operator_line: str = "") -> list:
        # One calibration screen; returns the cursor samples (x_cm, y_cm) read while it was shown
        samples = []
        start_time = None
        inside_since = None
        while True:
            space_pressed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    space_pressed = True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and isinstance(cursor_source, cursor.MouseCursor):
                    cursor_source.recenter(*origin_cm)
            x_cm, y_cm, sample_time = cursor_source.read()
            in_center = geometry.inside_circle(x_cm - origin_cm[0], y_cm - origin_cm[1], 0.0, 0.0, config.CENTER_RADIUS_CM)

            window.fill(config.BACKGROUND_COLOR)
            if direction_deg is not None:
                screen.draw_arrow(window, direction_deg)
            screen.draw_circle(window, config.CENTER_COLOR, 0.0, 0.0, config.CENTER_RADIUS_CM, in_center, calibration_gain)
            screen.draw_cursor(window, x_cm - origin_cm[0], y_cm - origin_cm[1], calibration_gain)
            screen.draw_text(window, text_font, screen.TEXTS[language][text_key], (screen_width // 2, screen_height - 80))
            if config.SHOW_OPERATOR_OVERLAY:
                if wait_for_space:
                    hint = "Space: patient steady at the limit"
                elif wait_for_center:
                    hint = "waiting for the return to the center"
                else:
                    hint = f"{duration_s:.0f} s"
                screen.draw_overlay(window, overlay_font, [f"calibration: {text_key}, {hint}", operator_line], [])
            flip_time = screen.flip()

            if start_time is None:
                start_time = flip_time
            if not in_center:
                inside_since = None
            elif inside_since is None:
                inside_since = flip_time
            samples.append((x_cm, y_cm))
            space_done = wait_for_space and space_pressed
            # Back only after staying inside the center circle for RETURN_HOLD_S
            center_done = wait_for_center and inside_since is not None and flip_time - inside_since >= config.RETURN_HOLD_S
            time_done = not wait_for_space and not wait_for_center and flip_time - start_time >= duration_s
            if space_done or center_done or time_done:
                return samples

    run_phase("get_ready", (0.0, 0.0), config.CALIBRATION_READY_S)
    center = calibration.center_from_samples(run_phase("stand_still", (0.0, 0.0), config.CENTER_CALIBRATION_S))
    origin_cm = (center["x_cm"], center["y_cm"])
    hold_samples_by_direction = {}
    for direction_deg in config.TARGET_DIRECTIONS_DEG:
        hold_samples_by_direction[direction_deg] = []
        for repetition in range(1, config.LIMIT_REPETITIONS + 1):
            operator_line = f"direction {direction_deg} deg, repetition {repetition} of {config.LIMIT_REPETITIONS}"
            run_phase("lean", origin_cm, direction_deg=direction_deg, wait_for_space=True, operator_line=operator_line)
            hold_samples = run_phase("hold", origin_cm, config.LIMIT_HOLD_S, direction_deg, operator_line=operator_line)
            hold_samples_by_direction[direction_deg].append(hold_samples)
            run_phase("back_to_center", origin_cm, wait_for_center=True, operator_line=operator_line)
    return calibration.make_calibration(center, hold_samples_by_direction)


def target_positions_cm(target_distances_cm: list) -> list:
    # (x, y) of each target in cm from the center, in the order of TARGET_DIRECTIONS_DEG
    return [
        geometry.target_position(direction_deg, distance_cm)
        for direction_deg, distance_cm in zip(config.TARGET_DIRECTIONS_DEG, target_distances_cm)
    ]


def main():
    parser = argparse.ArgumentParser(description="Center-out task driven by the center of pressure.")
    parser.add_argument("--source", default=config.CURSOR_SOURCE, choices=["mouse", "force_plate"])
    arguments = parser.parse_args()

    settings = start_window.ask_start_settings()
    if settings is None:
        return
    language = settings["language"]
    window = screen.open_window()
    screen_width, screen_height = window.get_size()
    monitor_hz = screen.monitor_refresh_hz()
    text_font = screen.load_font(config.TEXT_FONT_SIZE_PX)
    overlay_font = screen.load_font(config.OVERLAY_FONT_SIZE_PX)
    session = {
        "patient_id": settings["patient_id"],
        "session": settings["session"],
        "language": language,
        "cursor_source": arguments.source,
        "screen_size_px": [screen_width, screen_height],
        "monitor_refresh_hz": monitor_hz,
    }
    calibrations = []
    session_folder = None
    if settings["save_data"]:
        session_folder = saving.make_session_folder(settings["save_folder"], settings["patient_id"], settings["session"])
        calibration.save_calibrations(session_folder, session, calibrations)
    # Calibration screens, and the task before the first calibration, use a fixed scale wide enough for the
    # largest lean; the mouse covers the same range
    calibration_view_cm = [(-config.CALIBRATION_VIEW_CM, 0.0), (config.CALIBRATION_VIEW_CM, 0.0),
                           (0.0, config.CALIBRATION_VIEW_CM)]
    calibration_gain = geometry.fit_display_gain(calibration_view_cm, (screen_width, screen_height))
    cursor_source = cursor.make_cursor(arguments.source, (screen_width, screen_height), calibration_gain)

    # Until the first calibration: center at (0, 0), the same default distance in every direction, calibration scale
    origin_cm = (0.0, 0.0)
    target_distances_cm = [config.DEFAULT_TARGET_DISTANCE_CM] * len(config.TARGET_DIRECTIONS_DEG)
    target_positions = target_positions_cm(target_distances_cm)
    display_gain = calibration_gain
    recent_flip_times = []
    running = True
    while running:
        calibrate = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                calibrate = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and isinstance(cursor_source, cursor.MouseCursor):
                cursor_source.recenter(*origin_cm)

        if calibrate:
            new_calibration = run_calibration(window, text_font, overlay_font, cursor_source, calibration_gain, language)
            origin_cm = (new_calibration["center"]["x_cm"], new_calibration["center"]["y_cm"])
            target_distances_cm = [
                new_calibration["directions"][direction_deg]["target_distance_cm"]
                for direction_deg in config.TARGET_DIRECTIONS_DEG
            ]
            target_positions = target_positions_cm(target_distances_cm)
            # Scale that fits the new targets to the screen: changes only here, never during the trials
            display_gain = geometry.fit_display_gain(target_positions, (screen_width, screen_height))
            new_calibration["display_gain_px_per_cm"] = display_gain
            calibrations.append(new_calibration)
            if session_folder is not None:
                calibration.save_calibrations(session_folder, session, calibrations)
            recent_flip_times = []

        raw_x_cm, raw_y_cm, sample_time = cursor_source.read()
        # The calibrated center is the origin of the task
        cursor_x_cm, cursor_y_cm = raw_x_cm - origin_cm[0], raw_y_cm - origin_cm[1]

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
            warning_lines = []
            if abs(refresh_hz - monitor_hz) > config.REFRESH_TOLERANCE_FRACTION * monitor_hz:
                warning_lines.append("measured refresh rate differs from the monitor: check SCREEN_INDEX and vsync")
            if calibrations:
                center = calibrations[-1]["center"]
                calibration_line = (f"calibration {len(calibrations)}: "
                                    f"center SD x {center['sd_x_cm']:.2f} cm, y {center['sd_y_cm']:.2f} cm")
                raised_deg = [
                    str(direction_deg) for direction_deg, values in calibrations[-1]["directions"].items()
                    if values["raised_to_minimum"]
                ]
                if raised_deg:
                    warning_lines.append(f"limits too small at {', '.join(raised_deg)} deg: target distance raised "
                                         f"to the minimum {calibrations[-1]['minimum_target_distance_cm']:.1f} cm")
            else:
                calibration_line = "no calibration: default distances"
            distances_text = ", ".join(
                f"{direction_deg}: {distance_cm:.1f}"
                for direction_deg, distance_cm in zip(config.TARGET_DIRECTIONS_DEG, target_distances_cm)
            )
            screen.draw_overlay(window, overlay_font, [
                f"saving to {session_folder}" if session_folder is not None else "data not saved",
                f"language {language}, screen {screen_width} x {screen_height} px",
                f"refresh {refresh_hz:.1f} Hz (monitor {monitor_hz} Hz)",
                f"display gain {display_gain:.1f} px/cm",
                calibration_line,
                f"target distances {distances_text} cm",
                f"cursor x {cursor_x_cm:+.2f} cm, y {cursor_y_cm:+.2f} cm",
                "C: calibrate, R: mouse back to the center",
            ], warning_lines)

        recent_flip_times.append(screen.flip())
        recent_flip_times = recent_flip_times[-61:]

    pygame.quit()


if __name__ == "__main__":
    main()