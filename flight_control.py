# ─────────────────────────────────────────────
#  flight_control.py  –  Flight Primitives
# ─────────────────────────────────────────────
import time, math
from dronekit import connect, VehicleMode, LocationGlobalRelative
from config import (
    CONNECTION_STRING, BAUD_RATE,
    CRUISE_ALT_M, AIRSPEED_MS,
    LAND_HOLD_SEC, TAKEOFF_WAIT_SEC
)


# ── Connect ──────────────────────────────────────────────────────────────────
def connect_vehicle():
    print(f"[FC] Connecting → {CONNECTION_STRING} @ {BAUD_RATE}")
    vehicle = connect(CONNECTION_STRING, baud=BAUD_RATE, wait_ready=True)
    vehicle.airspeed = AIRSPEED_MS
    print(f"[FC] Connected  | Mode={vehicle.mode.name} | "
          f"Armed={vehicle.armed} | GPS={vehicle.gps_0.fix_type}")
    return vehicle


# ── Arm & Takeoff ─────────────────────────────────────────────────────────────
def arm_and_takeoff(vehicle, target_alt: float = CRUISE_ALT_M):
    print("[FC] Waiting for GPS fix …")
    while vehicle.gps_0.fix_type < 2:
        time.sleep(1)

    print("[FC] Setting GUIDED mode …")
    vehicle.mode = VehicleMode("GUIDED")
    while vehicle.mode.name != "GUIDED":
        time.sleep(0.5)

    print("[FC] Arming …")
    vehicle.armed = True
    while not vehicle.armed:
        time.sleep(0.5)

    print(f"[FC] Taking off to {target_alt}m …")
    vehicle.simple_takeoff(target_alt)

    # Wait until target altitude reached (within 95 %)
    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f"[FC]   Alt = {alt:.1f}m", end="\r")
        if alt >= target_alt * 0.95:
            break
        time.sleep(0.5)
    print(f"\n[FC] Reached {target_alt}m ✓")


# ── Goto Waypoint ─────────────────────────────────────────────────────────────
def goto(vehicle, location: LocationGlobalRelative, tolerance_m: float = 1.5):
    """
    Fly to location and block until within tolerance_m metres.
    """
    vehicle.simple_goto(location)
    while True:
        remaining = _distance_m(vehicle.location.global_frame, location)
        if remaining < tolerance_m:
            break
        time.sleep(0.5)
    print(f"[FC] Waypoint reached (±{tolerance_m}m)")


# ── Land → Hold → Takeoff ────────────────────────────────────────────────────
def land_hold_and_takeoff(vehicle, next_alt: float = CRUISE_ALT_M):
    """
    Land, hold for LAND_HOLD_SEC, then take off again to next_alt.
    """
    print("[FC] Landing …")
    vehicle.mode = VehicleMode("LAND")

    # Wait until actually on the ground (alt < 0.3m)
    while vehicle.location.global_relative_frame.alt > 0.3:
        time.sleep(0.5)

    print(f"[FC] Landed. Holding for {LAND_HOLD_SEC}s …")
    time.sleep(LAND_HOLD_SEC)

    print(f"[FC] Taking off again to {next_alt}m …")
    arm_and_takeoff(vehicle, next_alt)


# ── RTL ───────────────────────────────────────────────────────────────────────
def return_to_launch(vehicle):
    print("[FC] ── RTL initiated ──")
    vehicle.mode = VehicleMode("RTL")
    # Wait until landed
    while vehicle.armed:
        time.sleep(1)
    print("[FC] RTL complete. Vehicle disarmed ✓")


# ── Failsafe check ────────────────────────────────────────────────────────────
def check_failsafe(vehicle) -> bool:
    """
    Returns True if a failsafe condition is detected.
    Caller should trigger RTL immediately.
    """
    batt = vehicle.battery.level   # percent (None if unknown)
    if batt is not None and batt < 15:
        print(f"[FAILSAFE] Low battery: {batt}% → triggering RTL")
        return True
    if not vehicle.armed:
        print("[FAILSAFE] Vehicle unexpectedly disarmed → aborting")
        return True
    return False


# ── Utility ───────────────────────────────────────────────────────────────────
def _distance_m(loc1, loc2) -> float:
    """Haversine distance between two Location objects (metres)."""
    R   = 6378137.0
    lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
    lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))
