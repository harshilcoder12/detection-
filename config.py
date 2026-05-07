# ─────────────────────────────────────────────
#  config.py  –  Mission Configuration
# ─────────────────────────────────────────────

# --- Connection ---
CONNECTION_STRING = "/dev/ttyAMA0"   # RPi5 UART to FC  (change if USB: /dev/ttyUSB0)
#CONNECTION_STRING = "127.0.0.1:14551"
BAUD_RATE         = 57600

# --- Arena ---
ARENA_WIDTH_M   = 15.0   # metres (X axis)
ARENA_HEIGHT_M  = 10.0   # metres (Y axis)

# --- Flight ---
CRUISE_ALT_M      = 4.5   # metres AGL during search
LAND_HOLD_SEC     = 3     # seconds to stay landed per target
TAKEOFF_WAIT_SEC  = 10    # seconds to wait after issuing LAND before hold timer
GRID_SPACING_M    = 2.5   # lawnmower row spacing (tune for camera FOV)
AIRSPEED_MS       = 2.0   # m/s during waypoint nav

# --- Camera ---
CAMERA_INDEX      = 0          # /dev/video0
FRAME_WIDTH       = 1280
FRAME_HEIGHT      = 720
DETECTION_FPS     = 5          # how many frames/sec to run detection

# --- Detection ---
NUM_TARGETS       = 3
CONFIDENCE_THRESH = 0.55       # YOLO confidence threshold
# HSV fallback range for bullseye yellow centre
YELLOW_HSV_LOW  = (20,  100, 100)
YELLOW_HSV_HIGH = (35,  255, 255)
MIN_CIRCLE_RADIUS = 20         # pixels – ignore tiny blobs

# --- Logging ---
LOG_FILE = "mission_log.json"
