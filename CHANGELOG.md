
# CHANGE LOG

## [1.2.9] - 2023-05-06

### Added

- Added a new plugin, matrix.py, which adds support for matrix operations.
  - 加算：Addition
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> B = [[5, 6], [7, 8]]
    stacker:2> A B +
    [[[6, 8], [10, 12]]]
    ~~~
  - 乗算：Multiplication
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> B = [[5, 6], [7, 8]]
    stacker:2> A B *
    [[[19, 22], [43, 50]]]
    ~~~
  - 要素ごとの乗算：Element-wise multiplication
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> B = [[5, 6], [7, 8]]
    stacker:2> A B .*
    [[[5, 12], [21, 32]]]
    ~~~
  - 要素ごとの除算：Element-wise division
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> B = [[5, 6], [7, 8]]
    stacker:2> A B ./
    [[[0.2, 0.3333333333333333], [0.42857142857142855, 0.5]]]
    ~~~
  - 転置：Transpose
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> A '
    [[[1, 3], [2, 4]]]
    ~~~
  - 逆逆行列：Inverse matrix
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> A inv
    [[[-2.0, 1.0], [1.5, -0.5]]]
    ~~~
  - ランク：Rank
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> A rank
    2
    ~~~
  - トレース：Trace
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> A trace
    5
    ~~~
  - 単位行列：Identity matrix
    ~~~
    stacker:0> 2 2 ones
    [[[1.0, 1.0], [1.0, 1.0]]]
    ~~~
  - ゼロ行列：Zero matrix
    ~~~
    stacker:0> 2 2 zeros
    [[[0.0, 0.0], [0.0, 0.0]]]
    ~~~
  - 対角行列：Diagonal matrix
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> A diag
    [[1, 4]]
    ~~~


- Added a new plugin, range.py, which adds support for custom range functionality.
  ~~~
  stacker:0> 10:
  [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]

  stacker:1> (3 10):
  [[3, 4, 5, 6, 7, 8, 9]]

  stacker:2> (0 1 0.2):
  [[0.0, 0.2, 0.4, 0.6000000000000001, 0.8]]
  ~~~

- Added a new plugin, tolist.py, which adds support for converting specified ranges to lists and expanding lists.
  - tolist
    ~~~
    stacker:0> 1 2 3 4 5 6 7 8 9 10
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stacker:1> 4 8 tolist
    [1, 2, 3, 4, [5, 6, 7, 8], 9, 10]
    ~~~
  - unlist
    ~~~
    [1, 2, 3, 4, [5, 6, 7, 8], 9, 10]
    stacker:3> 4 unlist
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ~~~

### Changed

- Added numpy to requirements.txt.
- Made the following changes to stacker/stacker.py:
   * Added insert and ans operators.
   * Added a non_destructive_operator set, which includes operators that do not store their return values on the stack.
   * Updated the get_n_args_for_operator method, allowing it to retrieve the number of arguments for operators.

<hr>

## [1.2.8] - 2023-05-04

### Added

- Added support for inputting multiple arrays on a single line.

- Added a command `rev` to reverse arrays.

- Added a feature to treat the content within {...} as a string.

- Increased the variety of test cases.

### Changed

- Changed the matrix input method.
  Example:
    stacker:0> [1 2 3; 4 5 6; 7 8 9]
    [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]

- Please note that the traditional Python input method is no longer supported.

<hr>

## [1.2.7] - 2023-04-31

### Added

- Added a new matrix input method.
  Example:
    ~~~ bash
    stacker:0> [1 2 3; 4 5 6; 7 8 9]
    [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
    ~~~

- The traditional input method is still available.

  Example:
    ~~~ bash
    stacker:0> [[1,2,3], [4,5,6], [7,8,9]]
    [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
    stacker:1>
    ~~~

### Changed

  - Changed input handling to allow continuing input on a new line while entering a matrix.

  - Changed output to display colors for improved readability.
    - Different colors are used to distinguish between different types of output.

<hr>

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