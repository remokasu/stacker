# Unit Conversion Plugin

This plugin provides a simple function for converting between different units of measurement. It supports various units for length, mass, volume, temperature, area, speed, and time.

## Usage

The plugin registers a command `cu` (short for "convert unit") that takes three arguments:

1. Input unit
2. Value to convert
3. Output unit

The command will return the converted value.

### Examples

1. To convert 1000 meters to kilometers:

    ```
    m 1000 km cu
    ```

    This will return `1`, as 1000 meters is equal to 1 kilometer.

2. To convert 5 kilometers to miles:

    ```
    km 5 mi cu
    ```

    This will return `3.10686`, as 5 kilometers is approximately equal to 3.10686 miles.

3. To convert 60 minutes to seconds:

    ```
    minute 60 sec cu
    ```

    This will return `3600`, as 60 minutes is equal to 3600 seconds.

## Supported Units

The following units are supported:

- Length: meters (m), kilometers (km), miles (mi), feet (ft)
- Mass: kilograms (kg), grams (g), pounds (lb)
- Volume: liters (l), milliliters (ml), gallons (gal)
- Temperature: Celsius (c), Fahrenheit (f)
- Area: square meters (sq_m), square kilometers (sq_km), square feet (sq_ft), acres (acre)
- Speed: meters per second (m/s), kilometers per hour (km/h), miles per hour (mi/h)
- Time: minutes (minute), seconds (sec), hours (hour)

Additional unit conversions can be added by modifying the `CONVERSIONS` dictionary.

## Installation

To install the plugin, simply place the plugin file (`unit_conversion_plugin.py`) in the `plugins` directory of your Stacker installation and restart Stacker. The plugin will be loaded automatically, and the `cu` command will be available for use.

