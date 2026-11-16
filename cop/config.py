"""All task settings: change values here, not in the code."""

from pathlib import Path
import string

# Saving
SAVE_DIR = Path(__file__).resolve().parents[1] / "data"
PATIENT_ID_CHARACTERS = string.ascii_letters + string.digits + "_-"  # also valid in folder names
PATIENT_ID_MAX_LENGTH = 20

# Cursor source: "mouse" or "force_plate"
CURSOR_SOURCE = "mouse"

# Screen
SCREEN_INDEX = 1  # 0 = main monitor, 1 = second monitor
DISPLAY_GAIN_PX_PER_CM = 100.0  # maximum screen pixels for 1 cm of CoP; reduced automatically if targets do not fit
SCREEN_MARGIN_PX = 20  # free space between the farthest target and the screen edge
REFRESH_TOLERANCE_FRACTION = 0.05  # overlay turns red if measured and monitor refresh rates differ more than this
BACKGROUND_COLOR = (0, 0, 0)
OUTLINE_WIDTH_PX = 3

# Center, targets and cursor (sizes in cm of CoP displacement)
TARGET_DIRECTIONS_DEG = (0, 45, 90, 135, 180)  # 0 = right, 90 = forward (up)
DEFAULT_TARGET_DISTANCE_CM = 6.0  # used until a calibration exists
CENTER_RADIUS_CM = 0.6
TARGET_RADIUS_CM = 0.8
CURSOR_RADIUS_CM = 0.25
CENTER_COLOR = (200, 200, 200)
TARGET_COLOR = (200, 200, 200)
CURSOR_COLOR = (255, 210, 0)

# Texts
FONT_FILE_NAME = "msyh.ttc"  # in the Windows fonts folder; must contain Chinese characters (e.g. Microsoft YaHei)
TEXT_FONT_SIZE_PX = 48
TEXT_COLOR = (230, 230, 230)

# Operator overlay (top left corner)
SHOW_OPERATOR_OVERLAY = True
OVERLAY_FONT_SIZE_PX = 20
OVERLAY_COLOR = (120, 120, 120)
OVERLAY_WARNING_COLOR = (220, 60, 60)