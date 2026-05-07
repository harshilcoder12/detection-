# DronoWar – Autonomous Drone Mission (Round 2)
## Raspberry Pi 5 + Camera + MAVLink Flight Controller

---

## File Structure
```
drone_mission/
├── main.py            ← Run this to start the mission
├── config.py          ← All tunable parameters
├── flight_control.py  ← Takeoff, goto, land, RTL, failsafe
├── detection.py       ← Bullseye detection (YOLO or OpenCV)
├── grid_search.py     ← Lawnmower waypoint generator
├── geotagger.py       ← GPS tagging & JSON logging
└── requirements.txt
```

---

## Setup on RPi 5

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Enable UART on RPi5 (if using UART to FC)
#    Add to /boot/firmware/config.txt:
#    enable_uart=1
#    dtoverlay=disable-bt

# 3. (Optional) Place YOLOv8 weights
#    Copy your trained bullseye.pt to drone_mission/
#    If absent, OpenCV HoughCircles fallback is used automatically

# 4. Edit config.py
#    - Set CONNECTION_STRING (/dev/ttyAMA0 for UART, /dev/ttyUSB0 for USB)
#    - Set BAUD_RATE to match your FC (typically 57600 or 115200)
#    - Adjust GRID_SPACING_M based on your camera's field of view
```

---

## Run the Mission

```bash
cd drone_mission
python main.py
```

---

## Pipeline Summary

```
CONNECT & ARM
     ↓
TAKEOFF (4.5m)
     ↓
GRID SEARCH (lawnmower, 15×10m arena)
   [Camera thread running in background]
     ↓  detect bullseye → GEOTAG GPS
   [Repeat until 3 targets found or grid complete]
     ↓
FLY TO TARGET 1 → LAND → HOLD 3s → GEOTAG → TAKEOFF
     ↓
FLY TO TARGET 2 → LAND → HOLD 3s → GEOTAG → TAKEOFF
     ↓
FLY TO TARGET 3 → LAND → HOLD 3s → GEOTAG
     ↓
RTL (Return to Launch)
```

---

## Key Config Parameters (config.py)

| Parameter | Default | Notes |
|---|---|---|
| CONNECTION_STRING | /dev/ttyAMA0 | Change to /dev/ttyUSB0 for USB |
| CRUISE_ALT_M | 4.5 | Must stay ≤ 6m per rules |
| GRID_SPACING_M | 2.5 | Smaller = more thorough, slower |
| LAND_HOLD_SEC | 3 | Rules require minimum 3s |
| NUM_TARGETS | 3 | Fixed per rulebook |
| CONFIDENCE_THRESH | 0.55 | YOLO confidence cutoff |

---

## Failsafe Behaviour
- Battery < 15% → automatic RTL
- Unexpected disarm → abort & RTL
- KeyboardInterrupt (Ctrl+C) → RTL
- Any unhandled exception → RTL
