"""Trials of the center-out task: one trial (phases, timers, outcome) and the trial list of the session.
No drawing and no clock: position and time come in."""

import numpy as np

from cop import config, geometry


class Trial:
    def __init__(self, direction_deg: float, target_cm: tuple[float, float], speed: str, nogo: bool, wait_s: float,
                 attempt: int = 1):
        self.direction_deg = direction_deg
        self.target_cm = target_cm
        self.speed = speed  # "fast" or "slow": target color and correct movement time
        self.nogo = nogo
        self.wait_s = wait_s  # target on -> go
        self.attempt = attempt  # 1 the first time, then 2, 3... when the trial is run again
        self.phase = "center_hold"
        self.phase_start_s = None
        self.inside_since_s = None
        self.go_s = None
        self.movement_start_s = None
        self.reaction_time_s = None  # go -> leaving the center
        self.movement_time_s = None  # leaving the center -> entering the target
        self.outcome = None  # "ok", "too_fast", "too_slow", "nogo_fail" or "aborted"
        self.reason = None  # why aborted ("unstable_hold", "early_start", "no_start"), or "no_arrival"

    @property
    def needs_repeat(self) -> bool:
        # Aborted trials and wrong durations are run again later; a failed no-go is not
        return self.outcome in ("aborted", "too_fast", "too_slow")

    def update(self, x_cm: float, y_cm: float, time_s: float) -> list[str]:
        # Once per frame: cursor in task coordinates and the time of its sample; returns the events of this frame
        events = []
        if self.phase_start_s is None:
            self.phase_start_s = time_s
            events.append("trial_start")
        phase_s = time_s - self.phase_start_s
        in_center = geometry.inside_circle(x_cm, y_cm, 0.0, 0.0, config.CENTER_RADIUS_CM)
        in_target = geometry.inside_circle(x_cm, y_cm, *self.target_cm, config.TARGET_RADIUS_CM)

        if self.phase == "center_hold":
            if self.held(in_center, time_s, config.CENTER_HOLD_S):
                events += ["center_hold_ok", "target_on"]
                self.set_phase("target_wait", time_s)
            elif phase_s > config.CENTER_HOLD_TIMEOUT_S:
                events += self.finish("aborted", "unstable_hold", time_s)
        elif self.phase == "target_wait":
            if not in_center:
                events += self.finish("aborted", "early_start", time_s)
            elif phase_s >= self.wait_s:
                self.go_s = time_s
                events.append("nogo_signal" if self.nogo else "go")
                self.set_phase("nogo_hold" if self.nogo else "movement", time_s)
        elif self.phase == "nogo_hold":
            if not in_center:
                events += self.finish("nogo_fail", None, time_s)
            elif phase_s >= config.NOGO_HOLD_S:
                events += self.finish("ok", None, time_s)
        elif self.phase == "movement":
            if self.movement_start_s is None:
                if not in_center:
                    self.movement_start_s = time_s
                    self.reaction_time_s = time_s - self.go_s
                    events.append("movement_start")
                elif phase_s > config.START_TIMEOUT_S:
                    events += self.finish("aborted", "no_start", time_s)
            elif in_target:
                self.movement_time_s = time_s - self.movement_start_s
                shortest_s, longest_s = config.MOVEMENT_TIME_RANGES_S[self.speed]
                if self.movement_time_s < shortest_s:
                    self.outcome = "too_fast"
                elif self.movement_time_s > longest_s:
                    self.outcome = "too_slow"
                else:
                    self.outcome = "ok"
                events.append("target_arrival")
                self.set_phase("target_hold", time_s)
            elif time_s - self.movement_start_s > config.MOVEMENT_TIMEOUT_S:
                events += self.finish("too_slow", "no_arrival", time_s)
        elif self.phase == "target_hold":
            if self.held(in_target, time_s, config.TARGET_HOLD_S):
                events += ["target_hold_ok"] + self.finish(self.outcome, None, time_s)
            elif phase_s > config.TARGET_HOLD_TIMEOUT_S:
                events += ["target_hold_timeout"] + self.finish(self.outcome, None, time_s)
        elif self.phase == "feedback":
            if phase_s >= config.FEEDBACK_S:
                self.set_phase("inter_trial", time_s)
        elif self.phase == "inter_trial":
            # Counted only while the cursor is back inside the center
            if self.held(in_center, time_s, config.INTER_TRIAL_S):
                events.append("trial_end")
                self.phase = "done"
        return events

    def held(self, inside: bool, time_s: float, hold_s: float) -> bool:
        # True once the cursor has stayed inside for hold_s; leaving restarts the count
        if not inside:
            self.inside_since_s = None
        elif self.inside_since_s is None:
            self.inside_since_s = time_s
        return self.inside_since_s is not None and time_s - self.inside_since_s >= hold_s

    def set_phase(self, phase: str, time_s: float):
        self.phase = phase
        self.phase_start_s = time_s
        self.inside_since_s = None

    def finish(self, outcome: str, reason: str | None, time_s: float) -> list[str]:
        # Outcome known: feedback next
        self.outcome = outcome
        self.reason = reason
        self.set_phase("feedback", time_s)
        return ["abort", "feedback"] if outcome == "aborted" else ["feedback"]


def make_trial_list(seed: int) -> list[list[dict]]:
    # Each direction at each speed TRIALS_PER_CONDITION times, plus NOGO_TRIALS no-go trials with the directions in
    # turn (the first half fast, rounded up, then slow). The seed fixes order and waits: same seed, same list
    rng = np.random.default_rng(seed)
    directions_deg = config.TARGET_DIRECTIONS_DEG
    trials = [
        {"direction_deg": direction_deg, "speed": speed, "nogo": False}
        for direction_deg in directions_deg for speed in ("fast", "slow") for _ in range(config.TRIALS_PER_CONDITION)
    ]
    fast_nogo_count = (config.NOGO_TRIALS + 1) // 2
    trials += [
        {"direction_deg": directions_deg[index % len(directions_deg)],
         "speed": "fast" if index < fast_nogo_count else "slow", "nogo": True}
        for index in range(config.NOGO_TRIALS)
    ]
    # Dealt to the blocks in turn, like cards: every condition, no-go included, is spread evenly over the blocks
    # (165 trials in 6 blocks: 28, 28, 28, 27, 27, 27); then each block is shuffled
    blocks = [trials[first::config.BLOCK_COUNT] for first in range(config.BLOCK_COUNT)]
    blocks = [[block[index] for index in rng.permutation(len(block))] for block in blocks]
    number = 0
    for block_number, block in enumerate(blocks, start=1):
        for planned in block:
            number += 1
            planned.update(trial=number, block=block_number, wait_s=float(rng.uniform(*config.TARGET_WAIT_RANGE_S)))
    return blocks