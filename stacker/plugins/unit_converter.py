# Dictionary for unit conversions
CONVERSIONS = {
    # Length
    ('m', 'km'): 0.001,             # meters to kilometers
    ('km', 'm'): 1000,              # kilometers to meters
    ('mi', 'km'): 1.60934,          # miles to kilometers
    ('km', 'mi'): 1 / 1.60934,      # kilometers to miles
    ('ft', 'm'): 0.3048,            # feet to meters
    ('m', 'ft'): 1 / 0.3048,        # meters to feet
    ('mi', 'ft'): 5280,             # miles to feet
    ('ft', 'mi'): 1 / 5280,         # feet to miles

    # Mass
    ('kg', 'g'): 1000,              # kilograms to grams
    ('g', 'kg'): 0.001,             # grams to kilograms
    ('lb', 'kg'): 0.453592,         # pounds to kilograms
    ('kg', 'lb'): 1 / 0.453592,     # kilograms to pounds

    # Volume
    ('l', 'ml'): 1000,              # liters to milliliters
    ('ml', 'l'): 0.001,             # milliliters to liters
    ('gal', 'l'): 3.78541,          # gallons to liters
    ('l', 'gal'): 1 / 3.78541,      # liters to gallons

    # Temperature
    ('c', 'f'): (1.8, 32),          # Celsius to Fahrenheit
    ('f', 'c'): (1 / 1.8, -32 / 1.8), # Fahrenheit to Celsius

    # Area
    ('sq_m', 'sq_km'): 1e-6,         # square meters to square kilometers
    ('sq_km', 'sq_m'): 1e6,          # square kilometers to square meters
    ('sq_ft', 'sq_m'): 0.092903,     # square feet to square meters
    ('sq_m', 'sq_ft'): 1 / 0.092903, # square meters to square feet
    ('acre', 'sq_m'): 4046.86,       # acres to square meters
    ('sq_m', 'acre'): 1 / 4046.86,   # square meters to acres

    # Speed
    ('m/s', 'km/h'): 3.6,            # meters per second to kilometers per hour
    ('km/h', 'm/s'): 1 / 3.6,        # kilometers per hour to meters per second
    ('mi/h', 'km/h'): 1.60934,       # miles per hour to kilometers per hour
    ('km/h', 'mi/h'): 1 / 1.60934,   # kilometers per hour to miles per hour

    # Time
    ('minute', 'sec'): 60,           # minutes to seconds
    ('sec', 'minute'): 1 / 60,       # seconds to minutes
    ('hour', 'minute'): 60,          # hours to minutes
    ('minute', 'hour'): 1 / 60,      # minutes to hours
    ('hour', 'sec'): 3600,           # hours to seconds
    ('sec', 'hour'): 1 / 3600,       # seconds to hours

    # Additional unit conversions can be added here
}


def convert_unit(input_unit, value, output_unit):
    if (input_unit, output_unit) not in CONVERSIONS:
        raise ValueError(f"Unsupported conversion: {input_unit} to {output_unit}")

    conversion = CONVERSIONS[(input_unit, output_unit)]

    # Check if the conversion is for temperature
    if isinstance(conversion, tuple):
        # Apply the multiplier and offset for temperature conversions
        result = value * conversion[0] + conversion[1]
    else:
        # Apply the conversion factor for all other unit conversions
        result = value * conversion

    return result


def setup(stacker_core):
    stacker_core.register_plugin("cu", convert_unit)
    # cu: convert unit
