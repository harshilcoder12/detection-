# ─────────────────────────────────────────────
#  detection.py  –  Bullseye Target Detection
#  Primary  : YOLOv8-nano  (if model exists)
#  Fallback : OpenCV HSV + HoughCircles
# ─────────────────────────────────────────────
import cv2
import numpy as np
import os
from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT,
    CONFIDENCE_THRESH, MIN_CIRCLE_RADIUS,
    YELLOW_HSV_LOW, YELLOW_HSV_HIGH
)

# ── Try to load YOLO model ──────────────────────────────────────────────────
_yolo = None
MODEL_PATH = "bullseye.pt"   # place your trained YOLOv8 weights here

def _load_yolo():
    global _yolo
    if os.path.exists(MODEL_PATH):
        try:
            from ultralytics import YOLO
            _yolo = YOLO(MODEL_PATH)
            print("[DETECTION] YOLOv8 model loaded ✓")
        except ImportError:
            print("[DETECTION] ultralytics not installed – using OpenCV fallback")
    else:
        print(f"[DETECTION] {MODEL_PATH} not found – using OpenCV fallback")

_load_yolo()

# ── Camera ──────────────────────────────────────────────────────────────────
def open_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")
    print("[DETECTION] Camera opened ✓")
    return cap


def read_frame(cap):
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Camera read failed")
    return frame


# ── YOLO detection ──────────────────────────────────────────────────────────
def _detect_yolo(frame) -> bool:
    results = _yolo(frame, verbose=False)[0]
    for box in results.boxes:
        if float(box.conf[0]) >= CONFIDENCE_THRESH:
            return True
    return False


# ── OpenCV HSV + Hough fallback ─────────────────────────────────────────────
def _detect_opencv(frame) -> bool:
    """
    Detects concentric circle pattern of a bullseye target.
    Works even when target colour varies – shape is the primary cue.
    """
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=30,
        param1=80,
        param2=35,
        minRadius=MIN_CIRCLE_RADIUS,
        maxRadius=300
    )

    if circles is None:
        return False

    # Require at least 2 concentric-ish circles (bullseye has multiple rings)
    circles = np.uint16(np.around(circles[0]))
    if len(circles) >= 2:
        # Check that at least two circles share a similar centre
        cx0, cy0 = circles[0][0], circles[0][1]
        for c in circles[1:]:
            dx = abs(int(c[0]) - int(cx0))
            dy = abs(int(c[1]) - int(cy0))
            if dx < 40 and dy < 40:   # centres within 40 px → concentric
                return True

    return False


# ── Public API ───────────────────────────────────────────────────────────────
def is_target_visible(frame) -> bool:
    """
    Returns True if a bullseye target is detected in the frame.
    Uses YOLO when available, OpenCV otherwise.
    """
    #return True
    
    if _yolo is not None:
        return _detect_yolo(frame)
    return _detect_opencv(frame)


def annotate(frame) -> "np.ndarray":
    """Draw detection overlay on frame (for debug streaming)."""
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1.2, 30,
                               param1=80, param2=35,
                               minRadius=MIN_CIRCLE_RADIUS, maxRadius=300)
    if circles is not None:
        for c in np.uint16(np.around(circles[0])):
            cv2.circle(frame, (c[0], c[1]), c[2], (0, 255, 0), 2)
            cv2.circle(frame, (c[0], c[1]), 2,    (0, 0, 255), 3)
    return frame
