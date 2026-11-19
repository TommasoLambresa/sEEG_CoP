"""All task settings: change values here, not in the code."""

from pathlib import Path
import string

# Saving
SAVE_DIR = Path(__file__).resolve().parents[1] / "data"  # folder proposed in the start window
NAME_CHARACTERS = string.ascii_letters + string.digits + "_-"  # allowed in patient ID and session: valid in folder names
NAME_MAX_LENGTH = 20
START_WINDOW_FONT_SIZE = 12  # points

# Cursor source: "mouse" or "force_plate"
CURSOR_SOURCE = "mouse"

# Screen
SCREEN_INDEX = 0  # 0 = main monitor, 1 = second monitor
REFERENCE_SCREEN_HEIGHT_PX = 1080  # sizes in px in this file are for a screen this high; scaled to the real one
SCREEN_MARGIN_PX = 20  # free space between the farthest target and the screen edge or the operator keys
CENTER_SCREEN_Y_FRACTION = 0.8  # CoP (0, 0) drawn at this fraction of the screen height from the top (0.5 = middle)
REFRESH_TOLERANCE_FRACTION = 0.05  # red warning if measured and monitor refresh rates differ more than this
BACKGROUND_COLOR = (0, 0, 0)
OUTLINE_WIDTH_PX = 3

# Center, targets and cursor (sizes in cm of CoP displacement)
TARGET_DIRECTIONS_DEG = (0, 45, 90, 135, 180)  # 0 = right, 90 = forward (up)
DEFAULT_TARGET_DISTANCE_CM = 6.0  # used until the first calibration (key C)
CENTER_RADIUS_CM = 0.4
TARGET_RADIUS_CM = 0.4
CURSOR_RADIUS_CM = 0.25
CENTER_COLOR = (200, 200, 200)  # also the "wait" color of the center during a trial
TARGET_COLOR = (200, 200, 200)
CURSOR_COLOR = (240, 240, 240)  # off-white, with a dark edge

# Calibration (key C)
CALIBRATION_VIEW_CM = 15.0  # largest lean shown on screen during calibration and before the first one (also the mouse range)
CALIBRATION_READY_S = 2.0  # "get ready" screen before the center measurement
CENTER_CALIBRATION_S = 5.0  # standing still: mean and SD give the center
LIMIT_REPETITIONS = 2  # per direction; the larger one is kept
LIMIT_HOLD_S = 2.0  # measured after the operator presses space
RETURN_HOLD_S = 0.5  # time inside the center circle that counts as "back to center"
TARGET_FRACTION = 0.6  # target distance = fraction of the limit
TARGET_GAP_CM = 0.3  # smallest free space between circles: the minimum target distance follows from it
ARROW_HEAD_PX = 60
ARROW_WIDTH_PX = 8
ARROW_COLOR = (80, 160, 255)

# Trial list: shuffled with a seed saved with the session; Space starts each block
TRIAL_LIST_SEED = 42  # None: a new seed every session; a number: the same list every session
TRIALS_PER_CONDITION = 1  # per direction and speed
NOGO_TRIALS = 3  # directions in turn; the first half fast (rounded up), then slow
BLOCK_COUNT = 2

# Trial (times in s; movement time = leaving the center -> entering the target)
CENTER_HOLD_S = 1.0  # inside the center before the target appears; leaving restarts the count
CENTER_HOLD_TIMEOUT_S = 10.0  # hold not reached in this time: trial aborted ("unstable_hold")
TARGET_WAIT_RANGE_S = (1, 2)  # target on -> go, random in this range; leaving the center: aborted ("early_start")
START_TIMEOUT_S = 3.0  # go -> leaving the center; longer: aborted ("no_start"). Long: slow starts are smooth
MOVEMENT_TIME_RANGES_S = {"fast": (0.0, 1.2), "slow": (2.0, 3.0)}  # correct movement time (shortest, longest)
MOVEMENT_TIMEOUT_S = 6.0  # target not reached in this time: "too_slow"
TARGET_HOLD_S = 1.0  # inside the target after the arrival; leaving restarts the count
TARGET_HOLD_TIMEOUT_S = 5.0  # hold not reached in this time: feedback anyway, the trial stays valid
NOGO_HOLD_S = 1.5  # no-go: stay in the center this long after the no-go signal
FEEDBACK_S = 1.0
INTER_TRIAL_S = 1.0  # counted only while the cursor is back inside the center
MAX_REPEATS_PER_TRIAL = 3  # aborted or wrong-duration trials are run again later, at most this many times
# Colors from the Okabe-Ito palette: still told apart with red-green color blindness
SPEED_TARGET_COLORS = {"fast": (230, 159, 0), "slow": (86, 180, 233)}  # orange = fast, sky blue = slow
GO_COLOR = (0, 158, 115)  # center at the go (bluish green): move
NOGO_COLOR = (213, 94, 0)  # center at the no-go signal (vermilion): do not move
TIME_BAR_WIDTH_FRACTION = 0.5  # feedback bar from 0 to MOVEMENT_TIMEOUT_S, fraction of the screen width
TIME_BAR_HEIGHT_PX = 16
TIME_BAR_Y_FRACTION = 0.965  # fraction of the screen height from the top, below the patient texts
TIME_BAR_COLOR = (70, 70, 70)

# Training (key T): the patient watches the ghost (semi-transparent cursor), then practices with and without it
GHOST_DURATIONS_S = {"fast": 1.5, "slow": 5.0}
GHOST_ALPHA = 110  # 0 = invisible, 255 = as opaque as the cursor
DEMONSTRATION_DIRECTIONS_DEG = (90, 45, 135)  # one ghost movement per direction, for each speed
DEMONSTRATION_WAIT_S = 1.5  # target on -> go in the demonstration
REFRESHER_DIRECTIONS_DEG = (90,)  # reminder before each block: one ghost movement per direction, for each speed
PRACTICE_WINDOW = 5  # a practice stage ends when PRACTICE_CORRECT_NEEDED of the last PRACTICE_WINDOW movements
PRACTICE_CORRECT_NEEDED = 4  # have the right duration, or when the operator presses Space

# Texts
FONT_FILE_NAME = "msyh.ttc"  # in the Windows fonts folder; must contain Chinese characters (e.g. Microsoft YaHei)
TEXT_FONT_SIZE_PX = 48
TEXT_COLOR = (230, 230, 230)
TEXT_Y_FRACTION = 0.91  # patient texts: fraction of the screen height from the top, below the CoP center

# Operator overlay: keys centered at the top (always shown), information in the top left corner (Tab hides it)
SHOW_OPERATOR_OVERLAY = True  # False: no keys and no information
OVERLAY_EDGE_PX = 10  # distance of the overlay from the screen edges
HINT_FONT_SIZE_PX = 30
OVERLAY_FONT_SIZE_PX = 18
OVERLAY_COLOR = (120, 120, 120)
OVERLAY_HINT_COLOR = (200, 200, 200)  # keys for the operator, centered at the top
OVERLAY_WARNING_COLOR = (220, 60, 60)