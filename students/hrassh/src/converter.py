UNITS = {
    "length": {
        "mm": 0.001,
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "in": 0.0254,
        "ft": 0.3048,
        "mi": 1609.344,
    },
    "mass": {
        "g": 0.001,
        "kg": 1.0,
        "t": 1000.0,
        "lb": 0.45359237,
        "oz": 0.028349523125,
    },
    "temperature": {
        "C": None,
        "F": None,
        "K": None,
    },
}


class ConversionError(ValueError):
    pass


def to_celsius(value, unit):
    if unit == "C":
        return value
    if unit == "F":
        return (value - 32) * 5 / 9
    return value - 273.15


def from_celsius(value, unit):
    if unit == "C":
        return value
    if unit == "F":
        return value * 9 / 5 + 32
    return value + 273.15


def convert(category, value, from_unit, to_unit):
    if category not in UNITS:
        raise ConversionError(f"unknown category: {category}")
    units = UNITS[category]
    if from_unit not in units or to_unit not in units:
        raise ConversionError(f"unknown unit for {category}")
    if category == "temperature":
        result = from_celsius(to_celsius(value, from_unit), to_unit)
        if to_celsius(value, from_unit) < -273.15:
            raise ConversionError("temperature below absolute zero")
    else:
        result = value * units[from_unit] / units[to_unit]
    return round(result, 6)
