# ─────────────────────────────────────────────
#  main.py  –  Master Mission Controller
#  DronoWar Autonomous Drone Mission – Round 2
# ─────────────────────────────────────────────
#
#  PIPELINE:
#  1. Connect & Takeoff
#  2. Grid Search  → detect 3 bullseye targets → geotag each
#  3. Visit each geotagged target → land → hold 3s → takeoff
#  4. RT
#
import time
import threading

import cv2
from dronekit import LocationGlobalRelative

import config 
import geotagger
import detection
import grid_search
import flight_control as fc

# ─────────────────────────────────────────────
#  Shared state (grid search ↔ camera thread)
# ─────────────────────────────────────────────
_detected_targets  = []   # list of geotag dicts
_detection_active  = True # set False to stop camera thread
_cap               = None


# ─────────────────────────────────────────────
#  Camera / Detection thread
# ─────────────────────────────────────────────
def _camera_thread(vehicle):
    """
    Runs in background during grid search.
    Whenever a new target is detected it is geotagged and appended
    to _detected_targets.
    """
    global _detection_active, _cap, _detected_targets

    _cap = detection.open_camera()
    frame_delay = 1.0 / config.DETECTION_FPS

    while _detection_active:
        try:
            frame = detection.read_frame(_cap)
        except RuntimeError as e:
            print(f"[CAM] {e}")
            time.sleep(1)
            continue

        if detection.is_target_visible(frame):
            # Only geotag if this location is sufficiently far from existing tags
            if _is_new_target(vehicle):
                tid  = len(_detected_targets) + 1
                tag  = geotagger.geotag(vehicle, tid)
                _detected_targets.append(tag)
                print(f"[MISSION] ★ Target {tid}/{config.NUM_TARGETS} found & geotagged")

                if len(_detected_targets) >= config.NUM_TARGETS:
                    print("[MISSION] All targets found – stopping grid search")
                    _detection_active = False
                    break

        time.sleep(frame_delay)

    if _cap:
        _cap.release()
    print("[CAM] Camera thread stopped")


def _is_new_target(vehicle, min_dist_m: float = 3.0) -> bool:
    """
    Return True if the current GPS position is at least min_dist_m
    away from every already-detected target (avoids double-tagging).
    """
    if not _detected_targets:
        return True
    loc = vehicle.location.global_frame
    for tag in _detected_targets:
        from flight_control import _distance_m
        from dronekit import LocationGlobal
        existing = LocationGlobal(tag["lat"], tag["lon"], tag["alt"])
        if _distance_m(loc, existing) < min_dist_m:
            return False
    return True


# ─────────────────────────────────────────────
#  Phase 1 – Grid Search
# ─────────────────────────────────────────────
def phase_grid_search(vehicle):
    global _detection_active

    home = vehicle.location.global_frame
    waypoints = grid_search.generate_grid(home)

    print(f"\n[MISSION] ── PHASE 1: Grid Search ({len(waypoints)} wps) ──")

    # Start camera detection in background
    _detection_active = True
    cam_thread = threading.Thread(target=_camera_thread, args=(vehicle,), daemon=True)
    cam_thread.start()

    for i, wp in enumerate(waypoints):
        # Stop early if all targets already found
        if not _detection_active:
            break

        # Failsafe check before each waypoint
        if fc.check_failsafe(vehicle):
            _detection_active = False
            fc.return_to_launch(vehicle)
            return False

        print(f"[MISSION] Grid WP {i+1}/{len(waypoints)} → "
              f"lat={wp.lat:.6f} lon={wp.lon:.6f}")
        fc.goto(vehicle, wp, tolerance_m=1.5)

    # Signal camera thread to stop (if not already)
    _detection_active = False
    cam_thread.join(timeout=5)

    print(f"[MISSION] Grid search done. Targets detected: {len(_detected_targets)}")
    return True


# ─────────────────────────────────────────────
#  Phase 2 – Visit, Land, Geotag, Repeat
# ─────────────────────────────────────────────
def phase_landing_mission(vehicle):
    print(f"\n[MISSION] ── PHASE 2: Landing Mission ({len(_detected_targets)} targets) ──")

    for idx, tag in enumerate(_detected_targets):
        print(f"\n[MISSION] ── Target {idx+1} ──")
        print(f"           lat={tag['lat']:.7f}  lon={tag['lon']:.7f}")

        # Failsafe check
        if fc.check_failsafe(vehicle):
            fc.return_to_launch(vehicle)
            return False

        target_wp = LocationGlobalRelative(tag["lat"], tag["lon"], config.CRUISE_ALT_M)

        # Fly to target
        fc.goto(vehicle, target_wp, tolerance_m=1.0)

        # Land, hold 3s, take off (skip takeoff after last target)
        is_last = (idx == len(_detected_targets) - 1)
        if is_last:
            # Just land – RTL will be triggered next
            print("[FC] Last target – landing (no re-takeoff)")
            from dronekit import VehicleMode
            vehicle.mode = VehicleMode("LAND")
            while vehicle.location.global_relative_frame.alt > 0.3:
                time.sleep(0.5)
            print(f"[FC] Landed. Holding for {config.LAND_HOLD_SEC}s …")
            time.sleep(config.LAND_HOLD_SEC)
        else:
            fc.land_hold_and_takeoff(vehicle, config.CRUISE_ALT_M)

        # Confirm geotag at landing position
        confirmed = geotagger.geotag(vehicle, tag["id"])
        print(f"[MISSION] ✓ Landing confirmed: {confirmed}")

    return True


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def run_mission():
    print("=" * 55)
    print("  DronoWar – Autonomous Drone Mission  (Round 2)")
    print("=" * 55)

    # ── Connect ──────────────────────────────────────────
    vehicle = fc.connect_vehicle()

    try:
        # ── Takeoff ───────────────────────────────────────
        fc.arm_and_takeoff(vehicle, config.CRUISE_ALT_M)
        time.sleep(2)   # stabilise

        # ── Phase 1: Grid Search + Detection ──────────────
        ok = phase_grid_search(vehicle)
        if not ok:
            return

        if len(_detected_targets) == 0:
            print("[MISSION] No targets detected – initiating RTL")
            fc.return_to_launch(vehicle)
            return

        # ── Fly back to cruise alt before Phase 2 ─────────
        fc.arm_and_takeoff(vehicle, config.CRUISE_ALT_M)
        time.sleep(2)

        # ── Phase 2: Landing Mission ───────────────────────
        ok = phase_landing_mission(vehicle)
        if not ok:
            return

        # ── RTL ────────────────────────────────────────────
        print("\n[MISSION] ── All targets complete → RTL ──")
        fc.return_to_launch(vehicle)

    except KeyboardInterrupt:
        print("\n[MISSION] Interrupted by user → RTL")
        fc.return_to_launch(vehicle)

    except Exception as e:
        print(f"\n[MISSION] UNEXPECTED ERROR: {e} → RTL")
        fc.return_to_launch(vehicle)

    finally:
        print("\n[MISSION] Closing vehicle connection …")
        vehicle.close()
        print("[MISSION] Done ✓")


if __name__ == "__main__":
    run_mission()
