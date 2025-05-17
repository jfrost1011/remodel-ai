from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
#  City and county mappings for California
# ─────────────────────────────────────────────────────────────────────────────
CITY_MAPPINGS = {
    # Los Angeles variations
    "los angeles":        "Los Angeles",
    "l.a.":               "Los Angeles",
    "los angeles county": "Los Angeles",
    "la county":          "Los Angeles",

    # LA neighborhoods / nearby cities
    "west hills":   "Los Angeles",
    "beverly hills": "Los Angeles",
    "santa monica": "Los Angeles",
    "pasadena":     "Los Angeles",
    "long beach":   "Los Angeles",
    "burbank":      "Los Angeles",
    "glendale":     "Los Angeles",

    # San Diego variations
    "san diego":        "San Diego",
    "s.d.":             "San Diego",
    "san diego county": "San Diego",

    # SD neighborhoods / nearby cities
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

    # Short forms – keep AFTER longer matches
    "la": "Los Angeles",
    "sd": "San Diego",
}

# ─────────────────────────────────────────────────────────────────────────────
#  Helper: normalize location strings
# ─────────────────────────────────────────────────────────────────────────────
def normalize_location(location_text: str) -> Optional[str]:
    """Normalize any California city / neighborhood text to
    either 'San Diego' or 'Los Angeles'.

    Returns:
        'San Diego', 'Los Angeles', or None if no match found.
    """
    if not location_text:
        return None

    # Lower-case for case-insensitive matching
    location_lower = location_text.lower().strip()
    print(f"DEBUG: normalize_location checking: '{location_lower}'")

    # Sort mappings by length (longest first) so specific strings win
    sorted_mappings = sorted(
        CITY_MAPPINGS.items(),
        key=lambda x: len(x[0]),
        reverse=True,
    )

    # Look for a substring match
    for variation, normalized in sorted_mappings:
        if variation in location_lower:
            print(f"DEBUG: normalize_location MATCHED '{variation}' → '{normalized}'")
            return normalized

    print(f"DEBUG: normalize_location found NO MATCH for '{location_lower}'")
    return None
