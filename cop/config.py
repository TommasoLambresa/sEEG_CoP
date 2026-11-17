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
SCREEN_INDEX = 1  # 0 = main monitor, 1 = second monitor
DISPLAY_GAIN_PX_PER_CM = 100.0  # maximum screen pixels for 1 cm of CoP; reduced automatically if targets do not fit
SCREEN_MARGIN_PX = 20  # free space between the farthest target and the screen edge
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
CENTER_COLOR = (200, 200, 200)
TARGET_COLOR = (200, 200, 200)
CURSOR_COLOR = (255, 210, 0)

# Calibration (key C)
CALIBRATION_VIEW_CM = 15.0  # largest lean shown on screen during calibration (also the mouse range)
CALIBRATION_READY_S = 2.0  # "get ready" screen before the center measurement
CENTER_CALIBRATION_S = 5.0  # standing still: mean and SD give the center
LIMIT_REPETITIONS = 2  # per direction; the larger one is kept
LIMIT_HOLD_S = 2.0  # measured after the operator presses space
RETURN_HOLD_S = 0.5  # time inside the center circle that counts as "back to center"
TARGET_FRACTION = 0.6  # target distance = fraction of the limit
TARGET_GAP_CM = 0.3  # smallest free space between circles: the minimum target distance follows from it
ARROW_HEAD_PX = 60
ARROW_WIDTH_PX = 12
ARROW_COLOR = (80, 160, 255)

# Texts
FONT_FILE_NAME = "msyh.ttc"  # in the Windows fonts folder; must contain Chinese characters (e.g. Microsoft YaHei)
TEXT_FONT_SIZE_PX = 48
TEXT_COLOR = (230, 230, 230)

# Operator overlay (top left corner)
SHOW_OPERATOR_OVERLAY = True
OVERLAY_FONT_SIZE_PX = 20
OVERLAY_COLOR = (120, 120, 120)
OVERLAY_WARNING_COLOR = (220, 60, 60)