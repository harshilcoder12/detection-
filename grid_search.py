# ─────────────────────────────────────────────
#  grid_search.py  –  Lawnmower Grid Generator
# ─────────────────────────────────────────────
import math
from dronekit import LocationGlobalRelative
from config import ARENA_WIDTH_M, ARENA_HEIGHT_M, GRID_SPACING_M, CRUISE_ALT_M

# Earth radius for offset calculations
_EARTH_R = 6378137.0


def _offset_location(origin, d_north_m: float, d_east_m: float, alt_m: float):
    """
    Return a LocationGlobalRelative shifted by d_north_m / d_east_m
    from origin (a LocationGlobal* object).
    """
    d_lat = d_north_m / _EARTH_R
    d_lon = d_east_m  / (_EARTH_R * math.cos(math.radians(origin.lat)))
    return LocationGlobalRelative(
        origin.lat + math.degrees(d_lat),
        origin.lon + math.degrees(d_lon),
        alt_m
    )


def generate_grid(home_location) -> list:
    """
    Generate a lawnmower (boustrophedon) pattern over the arena.
    home_location : vehicle.location.global_frame at takeoff point
    Returns       : list of LocationGlobalRelative waypoints
    """
    waypoints = []
    rows = int(ARENA_HEIGHT_M / GRID_SPACING_M) + 1
    left_to_right = True

    for row in range(rows):
        north_offset = row * GRID_SPACING_M
        east_start   = 0.0
        east_end     = ARENA_WIDTH_M

        if left_to_right:
            wp_a = _offset_location(home_location, north_offset, east_start, CRUISE_ALT_M)
            wp_b = _offset_location(home_location, north_offset, east_end,   CRUISE_ALT_M)
        else:
            wp_a = _offset_location(home_location, north_offset, east_end,   CRUISE_ALT_M)
            wp_b = _offset_location(home_location, north_offset, east_start, CRUISE_ALT_M)

        waypoints.extend([wp_a, wp_b])
        left_to_right = not left_to_right

    print(f"[GRID] Generated {len(waypoints)} waypoints "
          f"({rows} rows × 2, spacing={GRID_SPACING_M}m)")
    return waypoints
