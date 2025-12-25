# CHANGE LOG

## [1.9.0] - 2024-12-25

### Added

- **Parentheses `()` for Code Blocks**:
  - `()` can now be used in place of `{}` for code blocks
  - Example: `(1 2 +) eval`, `(x y) (x y *) mul defun`

- **Variable Prefix `$` is Optional**:
  - Variables can be used without `$` prefix (old syntax `$x` still works)
  - `=` operator added as an alias for `set`
  - Example: `5 x =` and `x echo`

- **Global Variables**:
  - New `global` keyword for global variable declaration
  - Syntax: `value variable global`
  - Example: `0 counter global`

- **VSCode Syntax Highlighting**:
  - Syntax highlighting extension for `.stk` files
  - Auto-closing pairs, code folding, comment toggling
  - Installation: `cp -r .vscode-extension ~/.vscode/extensions/stacker-language`

### Changed

- **Performance Optimization**:
  - Improved function call performance with scope chain implementation

- **Examples Directory**:
  - Reorganized into categories: `basics/`, `functions/`, `algorithms/`, `advanced/`
  - Updated to use new syntax (no `$` prefix)

### Fixed

- Fixed comment parsing when `#` appears mid-line
- Enhanced error messages
- Fixed multiline `()` code blocks in script files


## [1.8.3]

### Bug Fixes

- **Fixed File Naming Typos**:
  - Renamed `stacker/exec_modes/excution_mode.py` to `execution_mode.py`
  - Fixed method name typo: `disp_all_valiables()` → `disp_all_variables()`
  - Fixed attribute name typo: `self.oprerators` → `self.operators` (affected 16+ locations in core.py)

- **Code Cleanup**:
  - Removed unused file `stacker/valiable.py` (all content was commented out)

### Changed

- **Improved Package Configuration**:
  - Updated `pyproject.toml` to properly specify all subpackages
  - Added explicit Python version requirement: `requires-python = ">=3.10"`
  - Updated dependency specification: `prompt-toolkit>=3.0.0`
  - Corrected `package-data` to only include actual data files


## [1.8.2]

- **Changed**

  Stopped using the deprecated pkg_resources module in favor of standard library alternatives.


## [1.8.1]

### Improvements
- **Increased Maximum Regression Iterations**: The maximum number of regression iterations has been increased.
- **Improved Token Interpretation**: Tokens enclosed in `{}` are now correctly interpreted even when there are no spaces between them.
  Example: `{x} {x 2 ^} lambda` is now interpreted as `{x}{x 2 ^}lambda`.

### New Features
- **`frac` Command**:
  Example: `3 4 frac` returns `Fraction(3, 4)` and displays as `3/4`.
- **File Commands**:
  - `write-to-file`: Writes specified content to a file.
    Example: `"This is a test file." "test.txt" write-to-file`
  - `append-to-file`: Appends specified content to a file.
    Example: `"This is a test file." "test.txt" append-to-file`
  - `read-from-file`: Reads content from a file.
    Example: `"test.txt" read-from-file`
  - `file-exists`: Checks if a file exists.
    Example: `"test.txt" file-exists`

### Documentation Fixes
- Fixed incorrect explanation for the `read` command in `README.md`.


## [1.8.0]

- **Breaking Changes**

  - **Modified ifelse Syntax**:

    Before: <true-expr> <false-expr> condition ifelse
    After: condition <true-expr> <false-expr> ifelse

    Note: This change is not backwards compatible with previous versions.

  - **Modified if Syntax**:

    Before: <true-expr> condition if
    After: condition <true-expr> if

    Note: This change is not backwards compatible with previous versions.

- **Bug Fixes**

  Fixed variable scope handling in recursive function processing


## [1.7.0]

- **Support for Lambda Functions**:
  - Lambda functions are now supported, enabling inline definitions and executions of anonymous functions.
  - **Example**:
    ```
    stacker:0> {x} {x 2 *} lambda
    ```

- **Enforced Symbol Naming Conventions**:
  - Symbols used as arguments in `set`, `defun`, and `defmacro` now require a `$` prefix to improve clarity and prevent naming conflicts.
  - **Example**:
    ```
    stacker:0> 123 $a set
    ```

- **New Stack Manipulation Commands**:
  - **n listn**: Converts the top n elements from the stack into a list.
  - **extend**: Expands list objects onto the stack.

- **Input/Output Enhancements**:
  - **read**: Reads data from standard input.
  - **read-from-string**: Interprets a string as RPN expressions and reads it.

- **Bug Fixes**:
  - Resolved an issue where unnecessary values were being pushed onto the stack during function execution in sub-blocks, causing unexpected errors during recursive operations.

- **Display Command Improvement**:
  - The `disp` command has been updated to omit commas between elements, aligning with REPL mode display conventions.

- **New Command**:
  - **abort**: Immediately terminates the program with an exit status of 1, equivalent to `exit(1)`.

- **Unified Line Endings**:
  - Line endings across files have been unified; `.gitattributes` has been updated with `* text=auto`.

- **Comment Handling Improvement**:
  - Fixed an oversight where text following a `#` in the middle of a line was not being recognized as a comment.


## [1.6.1]

### Bug Fixes
- Resolved an issue where passing arrays to user-defined functions resulted in errors.

### Breaking Changes
- Changed the macro definition command from `alias` to `defmacro`.
  - Rationale: This change aligns the macro definition syntax with the function definition syntax (`defun`).
  - Note: This modification is not backwards compatible with previous versions.

### Migration
Users will need to update their existing macro definitions:
- Old syntax: `alias`
- New syntax: `defmacro`
