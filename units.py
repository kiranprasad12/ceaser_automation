"""Unit helpers for process data (DUMMY example code for the test branch).

CAESAR II gets temperature in degrees C and pressure in kPa (gauge).
"""

# kPa per one unit of the given pressure unit
PRESSURE_TO_KPA = {
    "kpa": 1.0,
    "bar": 100.0,
    "mpa": 1000.0,
    "kgcm2": 98.0665,
    "psi": 6.894757,
}

FULL_VACUUM_KPA = -101.325


def pressure_to_kpa(value, unit):
    """Convert a gauge pressure to kPa. Raises ValueError for an unknown unit."""
    key = unit.strip().lower()
    if key not in PRESSURE_TO_KPA:
        raise ValueError("Unknown pressure unit: %r (use one of %s)" % (unit, ", ".join(sorted(PRESSURE_TO_KPA))))
    return value * PRESSURE_TO_KPA[key]


def temperature_to_c(value, unit="C"):
    """Convert a temperature to degrees C. Accepts 'C' or 'F'."""
    key = unit.strip().upper()
    if key == "C":
        return float(value)
    if key == "F":
        return (value - 32.0) * 5.0 / 9.0
    raise ValueError("Unknown temperature unit: %r (use C or F)" % unit)
