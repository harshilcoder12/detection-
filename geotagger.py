# ─────────────────────────────────────────────
#  geotagger.py  –  Geotag & Log Target GPS
# ─────────────────────────────────────────────
import json, time
from config import LOG_FILE

_tags = []   # list of dicts stored in memory

def geotag(vehicle, target_id: int) -> dict:
    """
    Read current GPS from vehicle and store it as a geotag.
    Returns the tag dict.
    """
    loc = vehicle.location.global_frame
    tag = {
        "id"        : target_id,
        "lat"       : loc.lat,
        "lon"       : loc.lon,
        "alt"       : loc.alt,
        "timestamp" : time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    _tags.append(tag)
    _save()
    print(f"[GEOTAG] Target {target_id} → lat={loc.lat:.7f}  lon={loc.lon:.7f}  alt={loc.alt:.1f}m")
    return tag


def get_all() -> list:
    return list(_tags)


def _save():
    """Persist all tags to JSON log file."""
    with open(LOG_FILE, "w") as f:
        json.dump({"targets": _tags}, f, indent=2)
    print(f"[GEOTAG] Saved {len(_tags)} tag(s) → {LOG_FILE}")
