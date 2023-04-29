
# CHANGE LOG

## [1.2.5a] - 2023-04-30

### Removed

- Removed unnecessary files from the project.
  - This helps to keep the project clean and organized.

<hr>

## [1.2.5] - 2023-04-30

### Fixed

- Fixed an issue where multi-dimensional arrays could not be entered as input.
  - Users can now input multi-dimensional arrays as expected.

- Changed input evaluation from `eval()` to `ast.literal_eval()`.
  - This improves the safety and reliability of input handling.

- Corrected typos in the README.
  - Improved readability and understanding of the documentation.

<hr>

## [1.2.4] - 2023-04-24

### Added

- Added support for multi-line input within triple quotes.
  - Users can now enter multi-line input by enclosing it within triple quotes.

    Example:

    ~~~
    stacker:0> """
    stacker:0> This is a multi-line
    stacker:0> input example.
    stacker:0> """
    ['\nThis is a multi-line\ninput example.\n']
    ~~~

### Fixed
- Fix Typo in README.md

<hr>

## [1.2.3] - 2023-04-23

### Fixed

- Fixed an issue where lists and tuples could not be entered as input.
  - Users can now input lists and tuples as expected.

### Added

- Added support for binary, octal, and hexadecimal number representations.
  - Users can now input and display numbers in binary, octal, and hexadecimal formats.

<hr>

## [1.2.0] - 2023-04-22

### Added

- Introduced plugin support for extending Stacker's functionality.
  - Users can now create and install custom plugins to add new features.
  - Provided documentation and examples for creating plugins.

<hr>

## [1.0.0] - 2023-04

### Added

- Initial release of the project with core functionalities.
- Basic mathematical operations support.

<hr>