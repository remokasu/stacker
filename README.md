# Stacker: An RPN Calculator and Extensible Programming Language

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Stacker is a powerful Reverse Polish Notation (RPN) calculator built with Python, featuring basic mathematical operations and extensibility through plugins.

## Table of Contents

- [Installation](#installation)
- [Dependencies](#dependencies)
- [Feedback and Contributions](#feedback-and-contributions)
- [Usage](#usage)
- [Running Scripts](#running-scripts)
- [VSCode Syntax Highlighting](#vscode-syntax-highlighting)
- [Command Line Execution](#command-line-execution)
- [Settings](#settings)
- [Configuration File](#configuration-file)
- [Creating Plugins](#creating-plugins)
- [Running on Python](#running-on-python)
- [Supported Operations](#supported-operations)
- [Constants](#constants)

## Installation

```bash
git clone git@github.com:remokasu/stacker.git
cd stacker
pip install .
```

### Optional: VSCode Syntax Highlighting

For syntax highlighting support in VSCode:

```bash
mkdir -p ~/.vscode/extensions/stacker-language-0.1.0
cp -r .vscode-extension/* ~/.vscode/extensions/stacker-language-0.1.0/
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
  [3 4]
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
    ['Hello, World!']
    ```
    In this example, the string "Hello, World!" is added to the stack. Strings are written with double quotes and shown on the stack with single quotes.


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
    stacker:0> 5 y =
    stacker:1> y
    [5]
    ```
    In this example, we assign `3` to `x` using `set`, and `5` to `y` using `=`. Both operators work identically.

    **Note:** The `=` operator is an alias for `set` and can be used interchangeably. Use whichever feels more natural for your coding style.

    **Three ways to write a name.** A name can be written bare (`x`), as a symbol (`:x`) or quoted (`{x}`).
    The rule is short: a bare name is a *reference*, `:x` and `{x}` are the *name itself*, and `"x"` is a
    string, never a name.

    - A bare name is looked up: as a macro, then a variable, then a function or operator. A macro is expanded,
      a variable's value is pushed (a lambda too; call it with `eval`), a function or operator is run. A name
      that is none of these is an error right there, so a typo stops where it is written.
    - `:x` pushes the symbol `x` itself as a value, whatever a variable `x` holds. A symbol is a type of its
      own: `:x "x" ==` is false, `symbol?` tells it from a string, `str` gives its text and `symbol` makes one
      from text (`"x" symbol`). `:` must be followed by a name (`:1` and `:{x}` are errors). Symbols are how a
      name is handed to a word that does not read it from the position right before itself, such as a macro,
      and `[:a :b]` is a list of names.
    - `{x}` (a block holding only the name) means "this name" everywhere a name is read, and as code it means
      the same as `:x`: `:x eval` and `{x} eval` both do what writing `x` does.
    - Right before `set`, `=`, `global`, `defun`, `defmacro` or `macroexpand`, as the loop variable of
      `do` / `dolist`, and as the two names before the block of `reduce` / `fold`, a bare name is read as the
      name being bound (shorthand for `:name`), so `3 x set`, `0 10 i {i echo} do` and
      `[1 2 3] 0 acc x {acc x +} reduce` need no `:`. The one exception is a built-in operator name right
      before `set`, `=`, `global`, `defun`, `defmacro` or `macroexpand`: `3 dup set` runs `dup` (and `set`
      then fails). To bind a built-in name on purpose, write `3 :dup set` or `3 {dup} set`. (A loop or
      accumulator variable may have any name.) Your own variables, functions and macros can be redefined by
      their bare name; redefining a prelude word such as `alias` logs a warning. A literal is never a name
      (`5 3 set` and `5 true set` are errors) and neither is a string (`5 "x" set` is an error too).
    - Words you define yourself (macros, `alias`) take their names in the `{x}` or `:x` form.

- Arrays:
  - Single-line array:
    ```bash
    stacker:0> [1 2 3; 4 5 6]
    [[[1 2 3] [4 5 6]]]
    ```

  - Multi-line array:
    ```bash
    stacker:0> [1 2 3;
    ... > 4 5 6]
    [[[1 2 3] [4 5 6]]]
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
  stacker:0> {1 2 +} eval
  [3]

  # Use in function definitions
  stacker:2> {x y} {x y *} multiply defun
  ```

  **Note**: Code blocks are stored but not executed until explicitly triggered. This allows for flexible program control, lazy evaluation, and higher-order programming patterns.

  **Quoted names:** a block holding a single name, such as `{double}`, is the way to pass a *name* as a value.
  Every word that takes a name (`set`, `=`, `global`, `defun`, `defmacro`, `alias`) accepts `{name}` as well as
  `:name`. Macros that define things take their names in this form. This is also how a *variable name* is passed to
  a macro: `{n} incr!` and `:n incr!` both hand over the name `n`, whereas `n incr!` hands over the variable's
  current value.

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

  - ##### cond Statement

    The `cond` statement evaluates condition-result pairs in order and executes the first matching branch.

    Syntax:
    ```bash
    {condition1} {result1} {condition2} {result2} ... n cond
    ```

    `n` is the number of condition-result pairs.

    Example:
    ```bash
    stacker:0> 5 :x set
    stacker:1> {x 0 >} {"positive"} {x 0 <} {"negative"} {true} {"zero"} 3 cond
    ['positive']
    ```

    Result: Pushes `"positive"` onto the stack as `x` is greater than `0`. Use `{true}` as the last condition to provide a default branch.

  - #### Loops

    Loops in Stacker allow for repeated execution of code blocks.

  - ##### do Loop

    The `do` loop iterates over a range of values.

    Syntax:
    ```bash
    start_value end_value name {body} do
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
      [value1 value2 ... valueN] name {body} dolist
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

  - ##### while Loop

    The `while` loop repeats a code block while a condition is true.

    Syntax:
    ```bash
    {condition} {body} while
    ```

    Example:
    ```bash
    stacker:0> 1 :i set 0 :s set
    stacker:2> {i 6 <=} {s i + :s set i ++ :i set} while
    stacker:2> s
    [21]
    ```

    Result: Sums numbers from 1 to 6.

    Note: Use `{condition}` as a code block that leaves a boolean on the stack. The loop terminates when the condition evaluates to false.

  - ##### loop

    `loop` repeats a code block forever until `break` is executed. It is the primitive every other loop
    can be built from; the body runs on the current stack, in the current scope.

    Syntax:
    ```bash
    {body} loop
    ```

    Example:
    ```bash
    stacker:0> 0 {1 + dup 10 > {break} if} loop
    [11]
    ```

  - #### break

    `break` immediately exits the innermost loop (`do`, `dolist`, `times`, `while`, `loop`).

    Syntax:
    ```bash
    {break}
    ```

    Example:
    ```bash
    stacker:0> 0 :s set 1 10 :i {i 5 == {break} if s i + :s set} do s
    [10]
    ```

    Result: Sums 1 through 4, then exits when `i` reaches 5. Note that `break` inside `if` immediately stops execution of the current block — `s i + :s set` is not executed when `i` equals 5.

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

- ### Define an alias:
  - syntax:
    ```bash
    {body} {name} alias
    ```
  - example:
    ```bash
    stacker:0> {2 ^ 3 * 5 +} {calculatePowerAndAdd} alias
    stacker:1> 5 calculatePowerAndAdd
    [80]
    ```
    An alias names a code snippet. Calling the name runs the body right there, on the caller's stack and in
    the caller's scope, exactly as if the body had been written in place. (Before 1.15.0 this was what
    `defmacro` did.)

- ### Define a macro:
  - syntax:
    ```bash
    {args} {body} name defmacro
    ```
  - example:
    ```bash
    stacker:0> {cond body} { {cond eval not {body eval} if} } {unless} defmacro
    stacker:1> -3 {0 >} {"not positive" echo} unless
    not positive
    ```
    A macro receives its arguments as *code* (blocks are not evaluated) and runs its body when it is called
    to build the code that will actually run. Inside a block literal of the body, an argument name is
    replaced by the argument passed in, so the body above produces
    `{{0 >} eval not {{"not positive" echo} eval} if}`, which is then evaluated on the caller's stack.
    This lets you define new control structures in Stacker itself.

    The rules:
    - The body runs on its own stack, in a scope of its own where the arguments are bound. It must leave
      exactly one value: a code block is evaluated in the caller's context, any other value is pushed as is.
    - Every name bound in that scope (the arguments, and variables assigned with `=` / `set` inside the body)
      is substituted into the body's block literals at the moment each literal is pushed: a symbol (`:name`,
      a `gensym` name) becomes a bare name in the generated code, a string becomes a string literal, a block
      stays a block and any other value is spliced as a value. The substituted values are not scanned again,
      and `:name`, string literals and list literals written in the body are left untouched.
    - Assignments inside the body are local to the macro; they never change the caller's variables.
    - Argument names may be anything, including built-in names; every occurrence in the block literals is
      replaced, so choose them with care.
    - `gensym` returns a fresh unique name (prefixed `__g`; do not use that prefix yourself) for temporaries
      in generated code:
      ```bash
      stacker:0> {x} { gensym t = { x eval t set t t + } } {double!} defmacro
      stacker:1> {3 4 +} double!
      [14]
      ```
    - `{name} macroexpand` pushes the expansion without running it, which is the easiest way to debug a macro.

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
    [3 4 λxλy.{x y *}]
    stacker:3> eval
    [12]
    ```
    This example defines a lambda function that multiplies two numbers and assigns it to the variable `multiply`.
    A lambda held in a variable is a value: writing `multiply` pushes it, and `eval` calls it with the arguments
    `3` and `4` (`3 4 multiply eval`). To call a function by its bare name, define it with `defun` instead.


- ### Include Scripts
  Stacker scripts can be included in other scripts using the `include` command. For example:

  ``` bash
  stacker:0>  "my_script.stk" include
  ```
  All functions, macros and variables defined in "my_script.stk" are added to the current stack.

- ### The prelude
  Some words are written in Stacker itself and loaded into every interpreter at start-up (`alias` and `mean`
  for now). They behave like any other word; `macros` and `funcs` mark them with `(prelude)`.


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
- **Variables and symbols** (`a`, `:x`) - Light blue
- **Assignment** (`set`, `=`, `global`) - White, bold
- Auto-closing brackets (`{`, `[`, `"`, `'`)
- Code folding support


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

    Here's an example that registers a custom command:

    Example:
    ```python
    from stacker.stacker import Stacker

    def function(a, b):
        return a + b

    def setup(stacker: Stacker):
        stacker.register_plugin("command", function, desc="Add two numbers")
    ```

    You can specify the command description for the help command using desc. This field is optional.

    The register_parameter method is used to add a custom parameter to the Stacker environment, allowing for additional customization and control within your plugin.

5. **Reinstalling Stacker**:
   Run the following command to reinstall Stacker:
    ```
    > pip install .
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
`Stacker()` loads the prelude like the command line does. Pass `Stacker(prelude=False)` for a bare interpreter.

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
| >>       | Right bit shift                                       | `8 2 >>`                   |
| <<       | Left bit shift                                        | `2 2 <<`                   |
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
| sin      | Sine (argument in radians)                            | `pi 2 / sin`               |
| cos      | Cosine (argument in radians)                          | `pi cos`                   |
| tan      | Tangent (argument in radians)                         | `pi 4 / tan`               |
| asin     | Arcsine (result in radians)                           | `0.5 asin`                 |
| acos     | Arccosine (result in radians)                         | `0.5 acos`                 |
| atan     | Arctangent (result in radians)                        | `1 atan`                   |
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
| gcd      | Greatest common divisor                               | `4 2 gcd`                  |
| !        | Factorial                                             | `4 !`                      |
| radians  | Convert degrees to radians                            | `180 radians`              |
| rand     | Generate a random floating-point number between 0 and 1| `rand`                    |
| randint  | Generate a random integer within a specified range    | `1 6 randint`              |
| uniform  | Generate a random floating-point number within a specified range | `1 2 uniform`   |
| frac     | Fraction                                              | `3 6 frac`                 |
| dice     | Roll dice (e.g., 3d6)                                 | `3 6 dice`                 |


### Stack Operators
| Operator | Description                                               | Example                |
|----------|-----------------------------------------------------------|------------------------|
| drop     | Drops the top element of the stack.                       | `drop`                 |
| drop2    | Drops the top two elements of the stack.                  | `drop2`                |
| dropn    | Drops the top n elements of the stack.                    | `2 dropn`              |
| dup      | Duplicate the top element of the stack.                   | `dup`                  |
| dup2     | Duplicate the top two elements of the stack.              | `dup2`                 |
| dupn     | Duplicate the top n elements of the stack.                | `2 dupn`               |
| swap     | Swap the top two elements of the stack.                   | `swap`                 |
| rev      | Reverse the stack.                                        | `rev`                  |
| rot      | Move the third element to the top of the stack.           | `rot`                  |
| unrot    | Move the top element to the third position of the stack.  | `unrot`                |
| roll     | Moves the nth element to the top of the stack.            | `2 roll`               |
| over     | Copy the second element from the top of the stack.        | `over`                 |
| pick     | Copies the nth element to the top of the stack.           | `2 pick`               |
| nip      | Remove the second element from the top of the stack.      | `nip`                  |
| depth    | Returns the depth of the stack.                           | `depth`                |
| ins      | Insert a value below the top n elements: `n value ins` | `3 1 ins`              |
| count    | Pop a value and count its occurrences in the rest of the stack. | `5 5 7 5 count` |
| clear    | Clear the stack.                                          | `clear`                |
| disp     | Display the stack.                                        | `disp`                 |


### Control Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| if       | Conditional statement                                 | `true {...} if`            |
| ifelse   | Conditional statement with an else block              | `true {"yes"} {"no"} ifelse`  |
| iferror  | Conditional statement for error handling              | `{1 0 /} {"caught"} iferror` |
| cond     | Multi-branch conditional (first matching pair wins)   | `5 x set {x 0 >} {"pos"} {true} {"other"} 2 cond` |
| do       | Loop                                                  | `0 10 i {i echo} do`      |
| dolist   | Loop over the elements of a list                      | `[1 2 3] x {x echo} dolist` |
| times    | Loop a specified number of times                      | `{dup ++} 10 times`        |
| while    | Loop while a condition is true                        | `0 :i set {i 10 <} {i ++ :i set} while` |
| loop     | Repeat a block until `break`                          | `0 {1 + dup 10 > {break} if} loop` |
| break    | Break out of a loop                                    | `break`                   |


### Function, Macro, Lambda, and Variable Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| defun    | Define a function                                     | `{x y} {x y *} multiply defun` |
| alias    | Name a code snippet (prelude)                         | `{2 ^ 3 * 5 +} {calculatePowerAndAdd} alias` |
| defmacro | Define a macro                                        | `{c b} {{c eval not {b eval} if}} {unless} defmacro` |
| macroexpand | Push a macro's expansion without running it        | `{0 >} {"neg" echo} {unless} macroexpand` |
| gensym   | Push a fresh unique name for macro temporaries        | `gensym t =`               |
| symbol   | Make a symbol from a string or a quoted name          | `"x" symbol`               |
| lambda   | Create a lambda function                              | `{x y} {x y *} lambda`    |
| set      | Assign a value to a variable                          | `3 x set`                |
| =        | Assign a value to a variable (alias for `set`)        | `3 x =`                  |
| global   | Assign a value to a global variable                   | `42 :answer global`      |


### Array Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| map      | Apply a function to each element of an array          | `[1 2 3] {2 *} map`        |
| zip      | Combine two arrays into a single array                | `[1 2 3] [4 5 6] zip`      |
| filter   | Filter an array based on a condition                  | `[1 2 3 4 5] {2 % 0 ==} filter` |
| all      | Check if all elements of a list are true              | `[true true false] all`    |
| any      | Check if any element of a list is true                | `[true false false] any`   |
| car      | Return the first element of a list                    | `[1 2 3] car`              |
| cdr      | Return the list without its first element             | `[1 2 3] cdr`              |
| cons     | Prepend an element to a list                          | `1 [2 3] cons`             |
| pair?    | Return true if the value is a non-empty list          | `[1 2 3] pair?`            |
| apply    | Expand list elements onto the stack and apply a function | `[3 4] {+} apply`       |
| expand   | Push the elements of a list, or each token of a code block as a one-token block | `[1 2 3] expand`, `{a b} expand` |
| concat-block | Join two code blocks                              | `{a b} {c} concat-block`   |

Note: Blocks passed to `map`, `filter`, `reduce`, and `fold` must leave a value on the stack. For side-effect-only iteration (e.g. printing each element), use `dolist` instead.


### Type Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| int      | Convert to int                                        | `3.7 int`                  |
| float    | Convert to float                                      | `3 float`                  |
| str      | Convert to string                                     | `42 str`                   |
| bool     | Convert to bool                                       | `1 bool`                   |
| complex  | Convert to complex number                             | `3 complex`                |
| type     | Get the type of a value                               | `42 type`                  |
| int?     | Returns true if the value is an int (not bool)        | `42 int?`                  |
| float?   | Returns true if the value is a float                  | `3.14 float?`              |
| str?     | Returns true if the value is a string                 | `"hello" str?`             |
| symbol?  | Returns true if the value is a symbol                 | `:x symbol?`               |
| bool?    | Returns true if the value is a bool                   | `true bool?`               |
| complex? | Returns true if the value is a complex number         | `1+2j complex?`            |
| list?    | Returns true if the value is a list                   | `[1 2 3] list?`            |
| null?    | Returns true if the value is null or an empty list    | `null null?`               |
| number?  | Returns true if the value is a number (int, float, or complex) | `42 number?`    |


### Other Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| sub      | Wrap the top value in a one-token code block          | `:x sub`                   |
| subn     | Wrap the top n values in one code block               | `1 2 2 subn`               |
| include  | Include the specified file                            | `"file.stk" include`       |
| eval     | Run a code block, a symbol or a lambda (text: `read-from-string` first) | `{3 5 +} eval`, `'3 5 +' read-from-string eval` |
| echo     | Print the specified value to stdout without adding it to the stack | `3 4 + echo`  |
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
| phi       | Golden ratio     |
| tau       | Tau              |
| nan       | Not a number     |
| inf       | Infinity         |

`true`, `false` and `null` are literals rather than constants: they are values, never names, and cannot be redefined.
