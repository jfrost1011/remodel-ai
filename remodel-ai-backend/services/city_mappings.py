# services/city_mappings.py
from typing import Optional

# ---------------------------------------------------------------------------
#  City / neighbourhood aliases that should resolve to “San Diego” or
#  “Los Angeles”.  Put the longer strings first so they win the match.
# ---------------------------------------------------------------------------
CITY_MAPPINGS = {
    # ── Los Angeles ──────────────────────────────────────────────────────
    "los angeles":        "Los Angeles",
    "l.a.":               "Los Angeles",
    "los angeles county": "Los Angeles",
    "la county":          "Los Angeles",

    # LA neighbourhoods / nearby cities
    "west hills":   "Los Angeles",
    "beverly hills":"Los Angeles",
    "santa monica": "Los Angeles",
    "pasadena":     "Los Angeles",
    "long beach":   "Los Angeles",
    "burbank":      "Los Angeles",
    "glendale":     "Los Angeles",

    # ── San Diego ───────────────────────────────────────────────────────
    "san diego":        "San Diego",
    "s.d.":             "San Diego",
    "san diego county": "San Diego",

    # SD suburbs / neighbourhoods
    "chula vista":    "San Diego",
    "la jolla":       "San Diego",
    "carlsbad":       "San Diego",
    "oceanside":      "San Diego",
    "escondido":      "San Diego",
    "coronado":       "San Diego",
    "del mar":        "San Diego",
    "encinitas":      "San Diego",
    "el cajon":       "San Diego",
    "national city":  "San Diego",
    "imperial beach": "San Diego",
    "poway":          "San Diego",
    "santee":         "San Diego",
    "la mesa":        "San Diego",

    # ── Short forms (KEEP LAST so longer phrases win first) ─────────────
    "la": "Los Angeles",
    "sd": "San Diego",
}

# ---------------------------------------------------------------------------
#  Helper
# ---------------------------------------------------------------------------
def normalize_location(location_text: str) -> Optional[str]:
    """
    Return “San Diego” or “Los Angeles” if the incoming text contains one
    of our known aliases; otherwise return None.
    """
    if not location_text:
        return None

    location_lower = location_text.lower().strip()
    print(f"DEBUG: normalize_location checking: '{location_lower}'")

    # longest aliases first → “chula vista” beats plain “la”
    for alias, canonical in sorted(
        CITY_MAPPINGS.items(),
        key=lambda kv: len(kv[0]),
        reverse=True
    ):
        if alias in location_lower:
            print(f"DEBUG: normalize_location MATCHED '{alias}' → '{canonical}'")
            return canonical

    print(f"DEBUG: normalize_location found NO MATCH for '{location_lower}'")
    return None
