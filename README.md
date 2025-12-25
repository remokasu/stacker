# Stacker: An RPN Calculator and Extensible Programming Language

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Stacker is a powerful Reverse Polish Notation (RPN) calculator built with Python, featuring basic mathematical operations and extensibility through plugins.

## Table of Contents

- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Running Scripts](#running-scripts)
- [VSCode Syntax Highlighting](#vscode-syntax-highlighting)
- [Error Formatting](#error-formatting)
- [Command Line Execution](#command-line-execution)
- [Configuration File](#configuration-file)
- [Creating Plugins](#creating-plugins)
- [Supported Operations](#supported-operations)

## Installation

```bash
git clone git@github.com:remokasu/stacker.git
cd stacker
pip install .
```

### Optional: VSCode Syntax Highlighting

For syntax highlighting support in VSCode:

```bash
cp -r .vscode-extension ~/.vscode/extensions/stacker-language
```

Reload VSCode (Ctrl+Shift+P → "Developer: Reload Window") and `.stk` files will be highlighted. 


## Dependencies

Python Prompt Toolkit is required for Stacker. Install it using the following command:
```bash
pip install prompt_toolkit
```

## Feedback and Contributions

Feedback and contributions are welcome. Please submit issues or suggestions on the [Issues page](https://github.com/remokasu/stacker/issues).


## Usage

Run Stacker:
```bash
stacker
```
Or:
```bash
python -m stacker
```

Stacker supports standard arithmetic operations (+, -, *, /) and advanced functions (sin, cos, tan, etc.). Users can input commands in RPN format and extend functionality using custom plugins.

### Input Examples

Stacker allows for straightforward RPN input. For example:

- Single-line input:
  ```bash
  stacker:0> 3 4 +
  [7]
  ```

- Multi-line input:
  ```bash
  stacker:0> 3
  [3]
  stacker:1> 4
  [3, 4]
  stacker:2> +
  [7]
  ```

- ### Numbers:
  The Stacker command allows you to directly push integers, floating-point numbers, and complex numbers onto the stack. This facilitates easy management of various types of numerical data.

  - Integers:
    ```bash
    stacker:0> 3
    [3]
    ```
    In this example, the integer 3 is added to the stack.

  - Floating-Point Numbers:
    ```bash
    stacker:1> 3.14
    [3.14]
    ```
    Here, the floating-point number 3.14 is added to the stack.

  - Complex Numbers:
    ```bash
    stacker:2> 1+2j
    [(1+2j)]
    ```
    In this case, the complex number 1+2j (with a real part of 1 and an imaginary part of 2) is added to the stack. Complex numbers are denoted by combining the real and imaginary parts with a +, and the imaginary part is indicated using j.

- ### Strings:
  - syntax:
    ```bash
    "Hello, World!"
    ```
  - example:
    ```bash
    stacker:0> "Hello, World!"
    ["Hello, World!"]
    ```
    In this example, the string "Hello, World!" is added to the stack.


- ### Variables:
  - syntax:
    ``` bash
    value name set
    # or
    value name =
    ```
  - example:
    ```bash
    stacker:0> 3 x set
    stacker:1> x
    [3]

    # Using = operator (equivalent to set)
    stacker:2> 5 y =
    stacker:3> y
    [5]
    ```
    In this example, we assign `3` to `x` using `set`, and `5` to `y` using `=`. Both operators work identically.

    **Note:** The `$` prefix (e.g., `$x`) is supported for backward compatibility but no longer required.

    **Note:** The `=` operator is an alias for `set` and can be used interchangeably. Use whichever feels more natural for your coding style.

    **Important:** Avoid using built-in operator names (like `sum`, `max`, `min`) as variable names,
    as this will shadow the operator. See [VARIABLE_NAMING.md](VARIABLE_NAMING.md) for details.

- Arrays:
  - Single-line array:
    ```bash
    stacker:0> [1 2 3; 4 5 6]
    [[1, 2, 3], [4, 5, 6]]
    ```

  - Multi-line array:
    ```bash
    stacker:0> [1 2 3;
    ... > 4 5 6]
    [[1, 2, 3], [4, 5, 6]]
    ```


- ### Code Blocks

  Code blocks are fundamental structures in Stacker that enable deferred evaluation and control flow management. They are enclosed in curly braces `{}`.

  **Syntax:**
  ```bash
  {code_elements}
  ```

  **Key Characteristics:**
  1. **Deferred Evaluation**: Code blocks are not executed immediately when encountered
  2. **Stack Interaction**: Pushed onto the stack as single units in their raw form
  3. **Delayed Execution**: Can be executed later when needed (via `eval`, `if`, `times`, etc.)

  **Common Use Cases:**
  - Conditional statements (`if`, `ifelse`)
  - Loop controls (`times`, `do`, `dolist`)
  - Function definitions (`defun`, `lambda`)
  - Lazy evaluation patterns

  **Examples:**
  ```bash
  # Create a code block
  stacker:0> {1 2 +}
  [{1 2 +}]

  # Execute with eval
  stacker:1> {1 2 +} eval
  [3]

  # Use in function definitions
  stacker:2> {x y} {x y *} multiply defun
  ```

  **Note**: Code blocks are stored but not executed until explicitly triggered. This allows for flexible program control, lazy evaluation, and higher-order programming patterns.

- ### Control Structures in Stacker

  Stacker provides two main types of control structures: conditionals and loops. These allow for dynamic program flow based on conditions and repetitive execution of code blocks.

  - #### Conditionals

    Conditionals in Stacker enable execution of code based on specified conditions.

  - ##### if Statement

    The `if` statement executes a code block if a condition is true.

    Syntax:
    ```bash
    condition <true-expr> if
    ```

    Example:
    ```bash
    stacker:0> 0 x set
    stacker:1> x 0 == {3 4 +} if
    [7]
    ```

    Result: Pushes `7` onto the stack as `x` equals `0`.

  - ##### ifelse Statement

    The `ifelse` statement provides branching based on a condition, executing one of two code blocks.

    Syntax:
    ```bash
    condition <true-expr> <false-expr> ifelse
    ```

    Example:
    ```bash
    stacker:0> 0 x set
    stacker:1> x 0 == {3 4 +} {3 4 -} ifelse
    [7]
    ```

    Result: Pushes `7` onto the stack as `x` equals `0`.

  - #### Loops

    Loops in Stacker allow for repeated execution of code blocks.

  - ##### do Loop

    The `do` loop iterates over a range of values.

    Syntax:
    ```bash
    start_value end_value symbol {body} do
    ```

    Example:
    ```bash
    stacker:0> 1 10 i {i echo} do
    1
    2
    3
    4
    5
    6
    7
    8
    9
    10
    ```

    Result: Prints numbers from 1 to 10.

  - ##### dolist

      The `dolist` loop iterates over a list of values.

      Syntax:
      ```bash
      [value1 value2 ... valueN] symbol {body} dolist
      ```

      Example:
      ```bash
      stacker:0> [1 2 3 4 5] i {i echo} dolist
      1
      2
      3
      4
      5
      ```

      Result: Prints numbers 1 through 5.

      Note:
        When expressing a list of consecutive values, the concise notation value1 valueN `seq` can be used instead of `[value1 value2 ... valueN]` to efficiently describe a sequence with a constant step size.

  - ##### times

    The `times` loop repeats a code block a specified number of times.

    Syntax:
    ```bash
    {body} n times
    ```

    Example:
    ```bash
    stacker:0> 1 {dup ++} 10 times
    [1 2 3 4 5 6 7 8 9 10 11]
    ```

    Result: Pushes numbers 1 through 11 onto the stack by repeatedly duplicating and incrementing.

  - #### break
    - syntax:
      ```bash
      {break}
      ```
    - example:
      ```bash
      stacker:0> 0 i set
      stacker:1> 0 9 i {{break} i 5 == if i echo} do
      0
      1
      2
      3
      4
      5
      ```
      This example prints the numbers from 0 to 5. When `i` is equal to `5`, the loop is terminated by `break`.

- ### Define a function:
  - syntax:
    ```bash
    {arg1 arg2 ... argN} {body} name defun
    ```
  - example:
    ```bash
    stacker:0> {x y} {x y *} multiply defun
    stacker:1> 10 20 multiply
    [200]
    ```
    This defines a function named `multiply` that takes two arguments `x` and `y` and multiplies them together.

- ### Define a macro:
  - syntax:
    ```bash
    {body} name defmacro
    ```
  - example:
    ```bash
    stacker:0> {2 ^ 3 * 5 +} calculatePowerAndAdd defmacro
    stacker:1> 5 calculatePowerAndAdd
    [80]
    ```
    This defines a macro with the body `{2 ^ 3 * 5 +}` and assigns it the name `calculatePowerAndAdd`. This macro squares the number on the stack, multiplies it by 3, and then adds 5.

- ### Lambda Functions
  Lambda functions are anonymous functions that can be defined and executed on the fly. They are useful for creating temporary functions without the need for a formal definition.

  - syntax:
    ```bash
    {arg1 arg2 ... argN} {body} lambda
    ```
  - example:
    ```bash
    stacker:0> {x y} {x y *} lambda
    [λxλy.{x y *}]
    ```

  - example:
    ```bash
    stacker:0> {x y} {x y *} lambda multiply set
    stacker:1> 3 4 multiply
    [12]
    ```
    This example defines a lambda function that multiplies two numbers and assigns it to the variable `multiply`. The function is then called with the arguments `3` and `4`.


- ### Include Scripts
  Stacker scripts can be included in other scripts using the `include` command. For example:

  ``` bash
  stacker:0>  "my_script.stk" include
  ```
  All functions, macros and variables defined in "my_script.stk" are added to the current stack.


## Running Scripts
Stacker scripts can be created in `.stk` files. To run a script, simply execute it with Stacker. For example:

- my_script.stk:
  ```bash
  0 p set
  0 100000 k {
      -1 k ^ 2 k * 1 + / p + p set
  } do
  4 p * p set
  p echo
  ```

  Running the script:
  ```bash
  stacker my_script.stk
  ```


## VSCode Syntax Highlighting

Stacker provides syntax highlighting support for `.stk` files in Visual Studio Code, making it easier to read and write Stacker code.

### Installation

Install the syntax highlighting extension by copying it to your VSCode extensions directory:

```bash
# For VSCode Server (Remote SSH)
mkdir -p ~/.vscode-server/extensions/stacker-language-0.1.0
cp -r .vscode-extension/* ~/.vscode-server/extensions/stacker-language-0.1.0/

# For local VSCode
mkdir -p ~/.vscode/extensions/stacker-language-0.1.0
cp -r .vscode-extension/* ~/.vscode/extensions/stacker-language-0.1.0/
```

Then reload VSCode (Ctrl+Shift+P → "Developer: Reload Window").

### Features

- **Comment highlighting** (`#`) - Green, italic
- **String literals** (`"..."`, `'...'`) - Brown
- **Number literals** (`42`, `3.14`, `0xFF`, `0b1010`) - Light green
- **Operators** (`+`, `-`, `and`, `or`, etc.) - Blue
- **Control flow** (`if`, `do`, `times`) - Purple
- **Function definitions** (`defun`, `defmacro`, `lambda`) - Teal, bold
- **Variables** (`$x`, `a`) - Light blue
- **Assignment** (`set`, `=`, `global`) - White, bold
- Auto-closing brackets (`{`, `[`, `"`, `'`)
- Code folding support

For detailed installation instructions, see [VSCODE_SETUP.md](VSCODE_SETUP.md).


## Command Line Execution
You can directly execute a specified RPN expression from the command line.

```bash
stacker -e "3 4 + echo"
```


## Settings
- disable_plugin
  Disable a specified plugin:
  ```bash
  stacker:0> "hoge" disable_plugin
  ```
  This command deactivates the `hoge` operator added as a plugin.
  Note that it cannot be used on non-plugin operators.

- disable_all_plugins
  Disable all plugins at once.
  ```bash
  stacker:0> disable_all_plugins
  ```

- enable_disp_ans
  Enables the display of the last result (ans) at the end of the stack.
  ```bash
  stacker:0> enable_disp_ans
  stacker:1> 3 4 +
  7
  [7]
  ```

- disable_disp_ans
  Disables the display of the last result (ans) at the end of the stack.
  ```bash
  stacker:0> disable_disp_ans
  stacker:1> 3 4 +
  [7]
  ```

- enable_disp_stack
  Enables the setting to display the stack contents each time. By default, this setting is already active.
  ```bash
  stacker:0> enable_disp_stack
  ```

- disable_disp_stack
  Sets the display of stack contents to be disabled. When this setting is enabled, only the latest element of the stack is displayed.
  ```bash
  stacker:0> disable_disp_stack
  ```

- disable_disp_logo
  Disables the display of the logo at startup.
  ```bash
  stacker:0> disable_disp_logo
  ```



## Configuration File
You can automatically load settings at startup. The configuration file should be placed in ~/.stackerrc. For example, if you write the following contents in ~/.stackerrc, the disable_disp_logo and disable_disp_stack will be automatically activated at startup.
```bash
disable_disp_logo
disable_disp_stack
enable_disp_ans
```

## Creating Plugins

Create custom plugins for Stacker using Python:

1. **Creating the Plugin**:
 In the `plugins` directory, create a new Python file for your plugin (e.g., `my_plugin.py`). 

    ``` 
    stacker/
    │
    ├── stacker/
    │   ├── plugins/
    │   │   ├── my_plugin.py
    │   │   └── ...
    │   │
    │   ├── data/
    │   ├── stacker.py
    │   ├── test.py
    │   └── ...
    │
    └── ...
    ```

    Adding your plugin here and reinstalling Stacker will apply the plugin permanently.

2. **Defining Functions and Classes**:
   Define the necessary functions and classes in `my_plugin.py`.

3. **Defining the `setup` Function**:
   In `my_plugin.py`, define a `setup` function that takes `stacker` as its only argument.

4. **Registering Custom Commands and Parameters**:

    Within the `setup` function, use the `register_plugin` method of `stacker` to register custom commands. Additionally, you can also register custom parameters using the `register_parameter` method. This allows for greater flexibility and customization in your plugin's behavior.

    Here's an example where custom commands for matrix operations and a custom parameter are registered:

    Example:
    ```python
    from stacker.stacker import Stacker

    def function(a, b):
        # Do something

    def setup(stacker: Stacker):
        stacker.register_plugin("command", function)
    ```

    You can specify the command description for the help command using desc. This field is optional.

    This example demonstrates how to register functions for matrix operations and how to set a custom parameter within a plugin. The register_parameter method is used to add a custom parameter to the Stacker environment, allowing for additional customization and control within your plugin.

5. **Reinstalling Stacker**:
   Run the following command to reinstall Stacker:
    ```
    > python setup.py install
    ```

    **Note**: If you want to apply the plugin only temporarily, create a `plugins` directory in the directory where Stacker is executed and add your plugin there. The method for creating it is the same as described above. This method does not require reinstalling Stacker.


6. **Using the Plugin**:
   When Stacker is launched, the plugin will automatically be loaded, and the custom commands will be available for use.

7. **Disabling Plugins**:
Use operatorName disable_plugin to disable a specific plugin.<br>
Use disable_all_plugins to disable all plugins.<br>


## Running on Python
You can also run Stacker as a Python module. For example:
```python
from stacker import Stacker
stacker = Stacker()
print(stacker.eval("3 4 +"))
```

## Supported Operations

### Basic Operators

| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| +        | Add                                                   | `3 5 +`                    |
| -        | Subtract                                              | `10 3 -`                   |
| *        | Multiply                                              | `4 6 *`                    |
| /        | Divide                                                | `12 4 /`                   |
| //       | Integer divide                                        | `7 2 //`                   |
| %        | Modulus                                               | `9 2 %`                    |
| ^        | Power                                                 | `3 2 ^`                    |
| ==       | Equal                                                 | `1 1 ==`                   |
| !=       | Not equal                                             | `1 0 !=`                   |
| <        | Less than                                             | `1 2 <`                    |
| <=       | Less than or equal to                                 | `3 3 <=`                   |
| >        | Greater than                                          | `2 1 >`                    |
| >=       | Greater than or equal to                              | `3 3 >=`                   |
| neg      | Negate                                                | `5 neg`                    |
| and      | Logical and                                           | `true false and`           |
| or       | Logical or                                            | `true false or`            |
| not      | Logical not                                           | `true not`                 |
| band     | Bitwise and                                           | `3 2 band`                 |
| bor      | Bitwise or                                            | `3 2 bor`                  |
| bxor     | Bitwise xor                                           | `3 2 bxor`                 |
| >>       | Right bit shit                                        | `8 2 >>`                   |
| <<       | Left bit shit                                         | `2 2 <<`                   |
| ~        | Bitwise not                                           | `5 ~`                      |
| bin      | Binary representation (result is a string)            | `5 bin`                    |
| oct      | Octal representation (result is a string)             | `10 oct`                   |
| dec      | Decimal representation (result is an integer)         | `0b101010 dec`             |
| hex      | Hexadecimal representation (result is a string)       | `255 hex`                  |


### Math Operator

| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| abs      | Absolute value                                        | `-3 abs`                   |
| exp      | Exponential                                           | `3 exp`                    |
| log      | Natural logarithm                                     | `2 log`                    |
| log10    | Common logarithm (base 10)                            | `4 log10`                  |
| log2     | Logarithm base 2                                      | `4 log2`                   |
| sin      | Sine                                                  | `30 sin`                   |
| cos      | Cosine                                                | `45 cos`                   |
| tan      | Tangent                                               | `60 tan`                   |
| asin     | Arcsine                                               | `0.5 asin`                 |
| acos     | Arccosine                                             | `0.5 acos`                 |
| atan     | Arctangent                                            | `1 atan`                   |
| sinh     | Hyperbolic sine                                       | `1 sinh`                   |
| cosh     | Hyperbolic cosine                                     | `1 cosh`                   |
| tanh     | Hyperbolic tangent                                    | `1 tanh`                   |
| asinh    | Inverse hyperbolic sine                               | `1 asinh`                  |
| acosh    | Inverse hyperbolic cosine                             | `2 acosh`                  |
| atanh    | Inverse hyperbolic tangent                            | `0.5 atanh`                |
| sqrt     | Square root                                           | `9 sqrt`                   |
| ceil     | Ceiling                                               | `3.2 ceil`                 |
| floor    | Floor                                                 | `3.8 floor`                |
| round    | Round                                                 | `3.5 round`                |
| roundn   | Round to specified decimal places                     | `3.51 1 roundn`            |
| float    | Convert to floating-point number                      | `5 float`                  |
| int      | Convert to integer                                    | `3.14 int`                 |
| gcd      | Greatest common divisor                               | `4 2 gcd`                  |
| !        | Factorial                                             | `4 !`                      |
| radians  | Convert degrees to radians                            | `180 radians`              |
| random   | Generate a random floating-point number between 0 and 1| `random`                  |
| randint  | Generate a random integer within a specified range    | `1 6 randint`              |
| uniform  | Generate a random floating-point number within a specified range | `1 2 uniform`   |
| frac     | Fraction                                              | `3 6 frac`                 |
| dice     | Roll dice (e.g., 3d6)                                 | `3 6 dice`                 |


### Stack Operators
| Operator | Description                                               | Example                |
|----------|-----------------------------------------------------------|------------------------|
| drop     | Drops the top element of the stack.                       | `drop`                 |
| drop2    | Drops the top two elements of the stack.                  | `drop2`                |
| dropn    | Drops the nth element from the top of the stack.          | `n drop`               |
| dup      | Duplicate the top element of the stack.                   | `dup`                  |
| dup2     | Duplicate the top two elements of the stack.              | `dup2`                 |
| dupn     | Duplicate the nth element from the top of the stack.      | `n dup`                |
| swap     | Swap the top two elements of the stack.                   | `swap`                 |
| rev      | Reverse the stack.                                        | `rev`                  |
| rot      | Move the third element to the top of the stack.           | `rot`                  |
| unrot    | Move the top element to the third position of the stack.  | `unrot`                |
| roll     | Moves the nth element to the top of the stack.            | `roll`                 |
| over     | Copy the second element from the top of the stack.        | `over`                 |
| pick     | Copies the nth element to the top of the stack.           | `n pick`               |
| nip      | Remove the second element from the top of the stack.      | `nip`                  |
| depth    | Returns the depth of the stack.                           | `depth`                |
| ins      | Insert the specified value at the specified position.     | `3 1 ins`              |
| count    | Counts the number of occurrences of a value in the stack. | `count`                |
| clear    | Clear the stack.                                          | `clear`                |
| disp     | Display the stack.                                        | `disp`                 |


### Control Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| if       | Conditional statement                                 | `{...} true  if`           |
| ifelse   | Conditional statement with an else block              | `{true block} {false block} true ifelse`  |
| iferror  | Conditional statement for error handling              | `{try block} {catch block} iferror` |
| do       | Loop                                                  | `0 10 i {i echo} do`      |
| times    | Loop a specified number of times                      | `{dup ++} 10 times`        |
| break    | Break out of a loop                                    | `break`                   |


### Function, Macro, Lambda, and Variable Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| defun    | Define a function                                     | `{x y} {x y *} multiply defun` |
| defmacro    | Define a macro                                     | `{2 ^ 3 * 5 +} calculatePowerAndAdd defmacro` |
| lambda   | Create a lambda function                              | `{x y} {x y *} lambda`    |
| set      | Assign a value to a variable                          | `3 x set`                |
| =        | Assign a value to a variable (alias for `set`)        | `3 x =`                  |
| global   | Assign a value to a global variable                   | `42 $answer global`      |


### Array Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| map      | Apply a function to each element of an array          | `[1 2 3] {dup} map`        |
| zip      | Combine two arrays into a single array                | `[1 2 3] [4 5 6] zip`      |
| filter   | Filter an array based on a condition                  | `[1 2 3 4 5] {2 % 0 ==} filter` |
| all      | Check if all elements of an array satisfy a condition  | `[1 2 3 4 5] {2 % 0 ==} all` |
| any      | Check if any element of an array satisfies a condition | `[1 2 3 4 5] {2 % 0 ==} any` |


### Other Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| sub      | Substack the top element of the stack                 | `sub`                      |
| subn     | Cluster elements between the top and the nth (make substacks) | `3 subn`           |
| include  | Include the specified file                            | `"file.stk" include`       |
| eval     | Evaluate the specified RPN expression                 | `'3 5 +' eval`             |
| echo     | Print the specified value to stdout without adding it to the stack | `3 4 + echo`  |
| input    | Get input from the user                               | `input`                    |
| read     | Reads a string from the console                       | `read`                     |
| write-to-file | Write the top element of the stack to a file       | `3 "output.txt" write-to-file` |
| append-to-file | Append the top element of the stack to a file      | `3 "output.txt" append-to-file` |
| read-from-file | Read the contents of a file and push it to the stack | `"input.txt" read-from-file` |
| file-exists | Check if a file exists                                | `"file.txt" file-exists`    |



## Constants
| Constants | Description      |
|-----------|------------------|
| e         | Euler's number   |
| pi        | Pi               |
| tau       | Tau              |
| nan       | Not a number     |
| inf       | Infinity         |
| true      | Boolean true     |
| false     | Boolean false    |