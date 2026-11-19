"""Center-out task driven by the center of pressure; it will publish the task markers."""

import argparse
import random
import sys

import pygame

from cop import calibration, config, cursor, geometry, saving, screen, start_window, trial


def run_calibration(window: pygame.Surface, text_font: pygame.font.Font, hint_font: pygame.font.Font,
                    overlay_font: pygame.font.Font, cursor_source: cursor.MouseCursor, gain: float,
                    language: str, show_info: bool, center_only: bool = False) -> tuple[dict, bool]:
    # Returns the new calibration (only {"center": ...} if center_only, after a pause) and whether the operator
    # information is shown (Tab), to keep it in the task

    def run_phase(text_key: str, origin_cm: tuple[float, float], duration_s: float = 0.0, direction_deg=None,
                  wait_for_space: bool = False, wait_for_center: bool = False, operator_line: str = "") -> list:
        # One calibration screen; returns the cursor samples (x_cm, y_cm) read while it was shown
        nonlocal show_info
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
                if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    show_info = not show_info
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and isinstance(cursor_source, cursor.MouseCursor):
                    cursor_source.recenter(*origin_cm)
            x_cm, y_cm, sample_time = cursor_source.read()
            in_center = geometry.inside_circle(x_cm - origin_cm[0], y_cm - origin_cm[1], 0.0, 0.0, config.CENTER_RADIUS_CM)

            window.fill(config.BACKGROUND_COLOR)
            if direction_deg is not None:
                screen.draw_arrow(window, direction_deg)
            screen.draw_circle(window, config.CENTER_COLOR, 0.0, 0.0, config.CENTER_RADIUS_CM, in_center, gain)
            screen.draw_cursor(window, x_cm - origin_cm[0], y_cm - origin_cm[1], gain)
            screen.draw_text(window, text_font, screen.TEXTS[language][text_key])
            if config.SHOW_OPERATOR_OVERLAY:
                if wait_for_space:
                    operator_hint = "Space: the patient is steady at the limit"
                elif wait_for_center:
                    operator_hint = "Wait: the patient comes back to the center"
                else:
                    operator_hint = f"Wait {duration_s:.0f} s"
                screen.draw_overlay(window, hint_font, overlay_font, [f"calibration: {text_key}", operator_line], [],
                                    f"{operator_hint}  |  R: mouse to the center  |  Tab: info  |  Esc: quit",
                                    show_info)
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
    if center_only:
        return {"center": center}, show_info
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
    return calibration.make_calibration(center, hold_samples_by_direction), show_info


def run_demonstration(window: pygame.Surface, text_font: pygame.font.Font, hint_font: pygame.font.Font,
                      overlay_font: pygame.font.Font, cursor_source: cursor.MouseCursor, origin_cm: tuple[float, float],
                      target_positions: list, gain: float, language: str, directions_deg: tuple,
                      show_info: bool) -> bool:
    # The patient watches the ghost: for each speed, one movement per direction in directions_deg, shown like a
    # trial (target and speed word, green center at the go, ghost to the target, still there for TARGET_HOLD_S).
    # Space skips the rest. Returns whether the operator information is shown (Tab), to keep it in the task
    demonstrations = [
        (speed, direction_deg) for speed in ("fast", "slow") for direction_deg in directions_deg
    ]
    for speed, direction_deg in demonstrations:
        target_cm = target_positions[config.TARGET_DIRECTIONS_DEG.index(direction_deg)]
        ghost_s = config.GHOST_DURATIONS_S[speed]
        # A trial used only to draw the screen: its phase follows the clock, the patient's cursor does not count
        shown_trial = trial.Trial(direction_deg, target_cm, speed, False, config.DEMONSTRATION_WAIT_S)
        start_time = None
        elapsed_s = 0.0
        while elapsed_s < config.DEMONSTRATION_WAIT_S + ghost_s + config.TARGET_HOLD_S + config.INTER_TRIAL_S:
            for event in pygame.event.get():
                key = event.key if event.type == pygame.KEYDOWN else None
                if event.type == pygame.QUIT or key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if key == pygame.K_SPACE:
                    return show_info
                if key == pygame.K_r and isinstance(cursor_source, cursor.MouseCursor):
                    cursor_source.recenter(*origin_cm)
                if key == pygame.K_TAB:
                    show_info = not show_info
            raw_x_cm, raw_y_cm, sample_time = cursor_source.read()
            if start_time is None:
                start_time = sample_time
            elapsed_s = sample_time - start_time
            since_go_s = elapsed_s - config.DEMONSTRATION_WAIT_S
            ghost_cm = None
            if since_go_s < 0:
                shown_trial.phase = "target_wait"
            elif since_go_s < ghost_s + config.TARGET_HOLD_S:
                shown_trial.phase = "movement"
                ghost_cm = geometry.minimum_jerk_position(target_cm, since_go_s, ghost_s)
            else:
                shown_trial.phase = "inter_trial"

            window.fill(config.BACKGROUND_COLOR)
            draw_trial(window, text_font, shown_trial, raw_x_cm - origin_cm[0], raw_y_cm - origin_cm[1], gain,
                       language, ghost_cm)
            if config.SHOW_OPERATOR_OVERLAY:
                screen.draw_overlay(window, hint_font, overlay_font,
                                    [f"demonstration: {speed}, {direction_deg} deg, ghost {ghost_s:.1f} s"], [],
                                    "Demonstration: the patient watches  |  Space: skip  |  R: mouse to the center  |  "
                                    "Tab: info  |  Esc: quit", show_info)
            screen.flip()
    return show_info


def target_positions_cm(target_distances_cm: list) -> list:
    # (x, y) of each target in cm from the center, in the order of TARGET_DIRECTIONS_DEG
    return [
        geometry.target_position(direction_deg, distance_cm)
        for direction_deg, distance_cm in zip(config.TARGET_DIRECTIONS_DEG, target_distances_cm)
    ]


def draw_trial(window: pygame.Surface, text_font: pygame.font.Font, current_trial: trial.Trial, cursor_x_cm: float,
               cursor_y_cm: float, gain: float, language: str, ghost_cm: tuple[float, float] | None = None):
    phase = current_trial.phase
    # Center as a traffic light: gray while waiting, green at the go, vermilion at the no-go signal
    if phase in ("movement", "target_hold"):
        center_color = config.GO_COLOR
    elif phase == "nogo_hold":
        center_color = config.NOGO_COLOR
    else:
        center_color = config.CENTER_COLOR
    in_center = geometry.inside_circle(cursor_x_cm, cursor_y_cm, 0.0, 0.0, config.CENTER_RADIUS_CM)
    screen.draw_circle(window, center_color, 0.0, 0.0, config.CENTER_RADIUS_CM, in_center, gain)
    # Target filled with its speed color from its appearance, speed word in the same color below the center:
    # neither changes at the go
    if phase in ("target_wait", "movement", "nogo_hold", "target_hold"):
        speed_color = config.SPEED_TARGET_COLORS[current_trial.speed]
        target_x_cm, target_y_cm = current_trial.target_cm
        screen.draw_circle(window, speed_color, target_x_cm, target_y_cm, config.TARGET_RADIUS_CM, True, gain)
        screen.draw_text(window, text_font, screen.TEXTS[language][current_trial.speed], speed_color)
    # Ghost below the patient's cursor: the cursor stays visible when the two overlap
    if ghost_cm is not None:
        screen.draw_ghost(window, *ghost_cm, gain)
    screen.draw_cursor(window, cursor_x_cm, cursor_y_cm, gain)
    if phase == "feedback":
        # Aborted trials show the reason, the others the outcome
        text_key = current_trial.reason if current_trial.outcome == "aborted" else current_trial.outcome
        screen.draw_text(window, text_font, screen.TEXTS[language][text_key])
        # After a movement: where its duration fell compared with the correct range
        if not current_trial.nogo and current_trial.outcome in ("ok", "too_fast", "too_slow"):
            if current_trial.movement_time_s is None:
                movement_time_s = config.MOVEMENT_TIMEOUT_S  # target never reached: mark at the end of the bar
            else:
                movement_time_s = current_trial.movement_time_s
            screen.draw_time_bar(window, movement_time_s, config.MOVEMENT_TIME_RANGES_S[current_trial.speed],
                                 config.SPEED_TARGET_COLORS[current_trial.speed])


def main():
    parser = argparse.ArgumentParser(description="Center-out task driven by the center of pressure.")
    parser.add_argument("--source", default=config.CURSOR_SOURCE, choices=["mouse", "force_plate"])
    arguments = parser.parse_args()

    settings = start_window.ask_start_settings()
    if settings is None:
        return
    language = settings["language"]
    # The seed fixes order and waits of the trials: the same seed gives the same list
    seed = config.TRIAL_LIST_SEED if config.TRIAL_LIST_SEED is not None else random.randrange(2 ** 31)
    blocks = trial.make_trial_list(seed)
    window = screen.open_window()
    screen_width, screen_height = window.get_size()
    monitor_hz = screen.monitor_refresh_hz()
    text_font = screen.load_font(window, config.TEXT_FONT_SIZE_PX)
    hint_font = screen.load_font(window, config.HINT_FONT_SIZE_PX)
    overlay_font = screen.load_font(window, config.OVERLAY_FONT_SIZE_PX)
    # Center and targets are fitted between the operator keys and the patient texts
    area_top_px, area_bottom_px = screen.target_area_px(window, text_font, hint_font)
    session = {
        "patient_id": settings["patient_id"],
        "session": settings["session"],
        "language": language,
        "cursor_source": arguments.source,
        "screen_size_px": [screen_width, screen_height],
        "monitor_refresh_hz": monitor_hz,
        "seed": seed,
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
    calibration_gain = geometry.fit_display_gain(calibration_view_cm, (screen_width, screen_height), area_top_px,
                                                 area_bottom_px)
    cursor_source = cursor.make_cursor(arguments.source, (screen_width, screen_height), calibration_gain)

    # Until the first calibration: center at (0, 0), the same default distance in every direction, calibration scale
    origin_cm = (0.0, 0.0)
    target_distances_cm = [config.DEFAULT_TARGET_DISTANCE_CM] * len(config.TARGET_DIRECTIONS_DEG)
    target_positions = target_positions_cm(target_distances_cm)
    display_gain = calibration_gain
    block_number = 0  # blocks started so far
    pending_trials = []  # (planned trial, attempt) still to run in the current block
    current_trial = None
    current_planned = None  # planned trial of current_trial: number, block, direction, speed, no-go, wait
    last_trial = None
    pause_requested = False  # key P: pause after the current trial
    paused = False
    recent_flip_times = []
    show_info = True  # operator information below the keys; Tab hides and shows it
    practice_stage = None  # during the practice (key T): "with_ghost", then "without_ghost"
    practice_correct = []  # one per movement in the current practice stage: True if its duration was right
    practice_count = 0  # practice trials started: they follow a fixed order
    running = True
    while running:
        # A trial that ended in the previous frame goes back in the block if needed, then the next one starts
        if current_trial is not None and current_trial.phase == "done":
            if practice_stage is not None:
                # Practice: nothing is repeated, aborted trials do not count
                if current_trial.outcome != "aborted":
                    practice_correct.append(current_trial.outcome == "ok")
                if sum(practice_correct[-config.PRACTICE_WINDOW:]) >= config.PRACTICE_CORRECT_NEEDED:
                    practice_stage = "without_ghost" if practice_stage == "with_ghost" else None
                    practice_correct = []
            else:
                if current_trial.needs_repeat and current_trial.attempt <= config.MAX_REPEATS_PER_TRIAL:
                    # Run again at the end of the same block, with the same number and wait
                    pending_trials.append((current_planned, current_trial.attempt + 1))
                if pause_requested:
                    paused = True
                    pause_requested = False
            last_trial = current_trial
            current_trial = None
        next_trial = None
        if current_trial is None and practice_stage is not None:
            # Fixed order: speeds alternate, directions go in turn (with 5 directions, all 10 pairs every 10 trials)
            next_trial = ({
                "trial": practice_count + 1,
                "block": 0,  # 0 = practice
                "direction_deg": config.TARGET_DIRECTIONS_DEG[practice_count % len(config.TARGET_DIRECTIONS_DEG)],
                "speed": ("fast", "slow")[practice_count % 2],
                "nogo": False,
                "wait_s": random.uniform(*config.TARGET_WAIT_RANGE_S),
            }, 1)
            practice_count += 1
        elif current_trial is None and pending_trials and not paused:
            next_trial = pending_trials.pop(0)
        if next_trial is not None:
            current_planned, attempt = next_trial
            target_cm = target_positions[config.TARGET_DIRECTIONS_DEG.index(current_planned["direction_deg"])]
            current_trial = trial.Trial(current_planned["direction_deg"], target_cm, current_planned["speed"],
                                        current_planned["nogo"], current_planned["wait_s"], attempt)

        # Calibration, training and blocks start only while no trial runs: targets and scale never change in a trial
        no_trial = current_trial is None and practice_stage is None
        between_blocks = no_trial and not pending_trials
        calibrate = False
        train = False
        start_block = False
        resume = False
        for event in pygame.event.get():
            key = event.key if event.type == pygame.KEYDOWN else None
            if event.type == pygame.QUIT or key == pygame.K_ESCAPE:
                running = False
            if key == pygame.K_c and no_trial:
                calibrate = True
            if key == pygame.K_t and between_blocks:
                train = True
            if key == pygame.K_SPACE and practice_stage is not None:
                # The operator ends this practice stage
                practice_stage = "without_ghost" if practice_stage == "with_ghost" else None
                practice_correct = []
                current_trial = None
            elif key == pygame.K_SPACE and paused:
                resume = True
            elif key == pygame.K_SPACE and between_blocks and block_number < len(blocks):
                start_block = True
            if key == pygame.K_p and practice_stage is None and (current_trial is not None or pending_trials):
                pause_requested = True
            if key == pygame.K_r and isinstance(cursor_source, cursor.MouseCursor):
                cursor_source.recenter(*origin_cm)
            if key == pygame.K_TAB:
                show_info = not show_info

        if train:
            show_info = run_demonstration(window, text_font, hint_font, overlay_font, cursor_source, origin_cm,
                                          target_positions, display_gain, language, config.DEMONSTRATION_DIRECTIONS_DEG,
                                          show_info)
            practice_stage = "with_ghost"
            practice_correct = []
            practice_count = 0
            recent_flip_times = []

        if start_block or resume:
            # After every pause the patient may stand differently: the center is measured again, limits are kept.
            # Task scale: the patient only stands still, no lean to show
            recalibration, show_info = run_calibration(window, text_font, hint_font, overlay_font, cursor_source,
                                                       display_gain, language, show_info, center_only=True)
            origin_cm = (recalibration["center"]["x_cm"], recalibration["center"]["y_cm"])
            if start_block:
                # Reminder of the two speeds, one ghost each, then the trials of the block
                show_info = run_demonstration(window, text_font, hint_font, overlay_font, cursor_source, origin_cm,
                                              target_positions, display_gain, language,
                                              config.REFRESHER_DIRECTIONS_DEG, show_info)
                pending_trials = [(planned, 1) for planned in blocks[block_number]]
                block_number += 1
            paused = False
            recent_flip_times = []

        if calibrate:
            new_calibration, show_info = run_calibration(window, text_font, hint_font, overlay_font, cursor_source,
                                                         calibration_gain, language, show_info)
            origin_cm = (new_calibration["center"]["x_cm"], new_calibration["center"]["y_cm"])
            target_distances_cm = [
                new_calibration["directions"][direction_deg]["target_distance_cm"]
                for direction_deg in config.TARGET_DIRECTIONS_DEG
            ]
            target_positions = target_positions_cm(target_distances_cm)
            # Scale that fits the new targets to the screen: changes only here, never during the trials
            display_gain = geometry.fit_display_gain(target_positions, (screen_width, screen_height), area_top_px,
                                                     area_bottom_px)
            new_calibration["display_gain_px_per_cm"] = display_gain
            calibrations.append(new_calibration)
            if session_folder is not None:
                calibration.save_calibrations(session_folder, session, calibrations)
            recent_flip_times = []

        raw_x_cm, raw_y_cm, sample_time = cursor_source.read()
        # The calibrated center is the origin of the task
        cursor_x_cm, cursor_y_cm = raw_x_cm - origin_cm[0], raw_y_cm - origin_cm[1]
        if current_trial is not None:
            for event_name in current_trial.update(cursor_x_cm, cursor_y_cm, sample_time):
                # Printed in the terminal until the LSL markers exist
                print(f"{sample_time:10.3f}  {event_name}")

        window.fill(config.BACKGROUND_COLOR)
        if current_trial is None:
            # Before, between or after the blocks, or paused: all targets, to check the layout
            in_center = geometry.inside_circle(cursor_x_cm, cursor_y_cm, 0.0, 0.0, config.CENTER_RADIUS_CM)
            screen.draw_circle(window, config.CENTER_COLOR, 0.0, 0.0, config.CENTER_RADIUS_CM, in_center, display_gain)
            for target_x_cm, target_y_cm in target_positions:
                in_target = geometry.inside_circle(cursor_x_cm, cursor_y_cm, target_x_cm, target_y_cm,
                                                   config.TARGET_RADIUS_CM)
                screen.draw_circle(window, config.TARGET_COLOR, target_x_cm, target_y_cm, config.TARGET_RADIUS_CM,
                                   in_target, display_gain)
            screen.draw_cursor(window, cursor_x_cm, cursor_y_cm, display_gain)
            session_finished = block_number == len(blocks) and not pending_trials
            screen.draw_text(window, text_font, screen.TEXTS[language]["finished" if session_finished else "rest"])
        else:
            # First practice stage: the ghost starts at the go and moves at the required speed
            ghost_cm = None
            if practice_stage == "with_ghost" and current_trial.phase in ("movement", "target_hold"):
                ghost_cm = geometry.minimum_jerk_position(current_trial.target_cm, sample_time - current_trial.go_s,
                                                          config.GHOST_DURATIONS_S[current_trial.speed])
            draw_trial(window, text_font, current_trial, cursor_x_cm, cursor_y_cm, display_gain, language, ghost_cm)

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
            # Keys for the operator: what can be done now
            keys_text = "R: mouse to the center  |  Tab: info  |  Esc: quit"
            if practice_stage is not None:
                correct_count = sum(practice_correct[-config.PRACTICE_WINDOW:])
                operator_hint = (f"Practice {practice_stage.replace('_', ' ')}: {correct_count} of the last "
                                 f"{config.PRACTICE_WINDOW} correct  |  Space: next stage  |  {keys_text}")
            elif current_trial is not None:
                pause_text = "pausing after this trial" if pause_requested else "P: pause after this trial"
                operator_hint = f"Block {block_number} of {len(blocks)}  |  {pause_text}  |  {keys_text}"
            elif paused:
                operator_hint = f"Paused  |  Space: resume block {block_number}  |  C: calibrate  |  {keys_text}"
            elif block_number < len(blocks):
                operator_hint = (f"Space: start block {block_number + 1} of {len(blocks)}  |  T: training  |  "
                                 f"C: calibrate  |  {keys_text}")
            else:
                operator_hint = f"Session finished  |  T: training  |  C: calibrate  |  {keys_text}"
            if current_trial is None:
                trial_line = "no trial running"
            else:
                nogo_text = " no-go" if current_trial.nogo else ""
                place_text = "practice" if practice_stage is not None else f"block {current_planned['block']}"
                trial_line = (f"trial {current_planned['trial']} ({place_text}): {current_trial.direction_deg} deg "
                              f"{current_trial.speed}{nogo_text}, attempt {current_trial.attempt}, "
                              f"phase {current_trial.phase}")
            block_sizes_text = "+".join(str(len(block)) for block in blocks)
            block_line = (f"trial list seed {seed}: blocks of {block_sizes_text} trials, {block_number} started, "
                          f"{len(pending_trials)} trials left in the current one")
            if last_trial is None:
                last_trial_line = "last trial: none"
            else:
                reaction_text = "-" if last_trial.reaction_time_s is None else f"{last_trial.reaction_time_s:.2f} s"
                movement_text = "-" if last_trial.movement_time_s is None else f"{last_trial.movement_time_s:.2f} s"
                last_trial_line = (f"last trial: {last_trial.outcome} {last_trial.reason or ''}, "
                                   f"RT {reaction_text}, MT {movement_text}")
            screen.draw_overlay(window, hint_font, overlay_font, [
                f"saving to {session_folder}" if session_folder is not None else "data not saved",
                f"language {language}, screen {screen_width} x {screen_height} px",
                f"refresh {refresh_hz:.1f} Hz (monitor {monitor_hz} Hz)",
                f"display gain {display_gain:.1f} px/cm",
                calibration_line,
                f"target distances {distances_text} cm",
                block_line,
                trial_line,
                last_trial_line,
                f"cursor x {cursor_x_cm:+.2f} cm, y {cursor_y_cm:+.2f} cm",
            ], warning_lines, operator_hint, show_info)

        recent_flip_times.append(screen.flip())
        recent_flip_times = recent_flip_times[-61:]

    pygame.quit()


if __name__ == "__main__":
    main()