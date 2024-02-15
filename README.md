# Stacker: An RPN Calculator and Extensible Programming Language

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/pystacker.svg)](https://badge.fury.io/py/pystacker)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Stacker is a powerful Reverse Polish Notation (RPN) calculator built with Python, featuring basic mathematical operations and extensibility through plugins.

## Installation

### Prerequisites:
Ensure Python 3 is installed.

### Installation Options:

- Via pip:
    ```bash
    pip install pystacker
    ```

- From source:
    ```bash
    git clone git@github.com:remokasu/stacker.git
    cd stacker
    python setup.py install
    ```

## Feedback and Contributions

Feedback and contributions are welcome. Please submit issues or suggestions on the [Issues page](https://github.com/remokasu/stacker/issues).

## Dependencies

Stacker uses external libraries like NumPy and Python Prompt Toolkit. Ensure these are installed:
```bash
pip install numpy prompt_toolkit
```

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
    value $name set
    ```
  - example:
    ```bash
    stacker:0> 3 $x set
    ```
    In this example, we assign `3` to `x`.
    If you input an undefined symbol, you need to prefix the symbol name with a dollar sign ($). <br>
    From now on, when using `x`, the character 'x' will be pushed onto the stack and evaluated to return `3` when popped. <br>
    You can push the value of a symbol by prefixing it with @. <br>
    For example, `@x` will push `3`.
    ``` bash
    stacker:0> 3 $x set
    stacker:1> x
    [x]
    stacker:2> @x
    [x, 3]
    stacker:1> +
    [6]
    ```

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


- ### Block Stack:

  Code blocks are enclosed in curly braces ({}). These blocks are pushed onto the stack in their raw form and can be executed later. For example: {1 2 +}. These blocks are particularly useful for deferred (lazy) evaluation. Specific use-cases include conditional statements and loop controls.

  - syntax:
    ```bash
    {1 2 +}
    ```
  - example:
    ```bash
    stacker:0> {1 2 +}
    [{1 2 +}]
    ```
    In this command, the block `{1 2 +}` is pushed (added) to the stack.

- ### Conditionals:
  - if
    - syntax:
      ```bash
      {true_block} {condition} if
      ```
    - example:
      ``` bash
      stacker:0> 0 $x set
      stacker:1> {3 4 +} {x 0 ==} if
      [7]
      ```
      This example pushes `7` onto the stack because `x` is equal to `0`.
  - ifelse
    - syntax:
      ```bash
      {true_block} {false_block} {condition} ifelse
      ```
    - example:
      ``` bash
      stacker:0> 0 $x set
      stacker:1> {3 4 +} {3 4 -} {x 0 ==} ifelse
      [7]
      ```
      This example pushes `7` onto the stack because `x` is equal to `0`.

- ### Loops:
  - do
    - syntax:
      ```bash
      start_value end_value $symbol {body} do
      ```
    - example:
      ```bash
      stacker:0> 0 10 $i {i echo} do
      0
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
      This example prints the numbers from 0 to 10.
  - times
    - syntax:
      ```bash
      {body} n times
      ```
    - example:
      ```bash
      stacker:0> 1 {dup ++} 10 times
      [1 2 3 4 5 6 7 8 9 10 11]
      ```
      In this example, we push 1 onto the stack and then repeat {dup (duplicate the top element) and ++ (add 1 to the top element)} 10 times.

- ### break
  - syntax:
    ```bash
    {break}
    ```
  - example:
    ```bash
    stacker:0> 0 $i set
    stacker:1> 0 10 $i {{break} i 5 == if i echo} do
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
    (arg1 arg2 ... argN) {body} $name defun
    ```
  - example:
    ```bash
    stacker:0> (x y) {x y *} $multiply defun
    stacker:1> 10 20 multiply
    [200]
    ```
    This defines a function named `multiply` that takes two arguments `x` and `y` and multiplies them together.

- ### Define a macro:
  - syntax:
    ```bash
    {body} $name alias
    ```
  - example:
    ```bash
    stacker:0> {2 ^ 3 * 5 +} $calculatePowerAndAdd alias
    stacker:1> 5 calculatePowerAndAdd
    [80]
    ```
    This defines a macro with the body `{2 ^ 3 * 5 +}` and assigns it the name `calculatePowerAndAdd`. This macro squares the number on the stack, multiplies it by 3, and then adds 5.

- ### Include Scripts
  Stacker scripts can be included in other scripts using the `include` command. For example:

  ``` bash
  stacker:0>  "my_script.stk" include
  ```
  All functions, macros and variables defined in "my_script.stk" are added to the current stack.

- ### File Writing and Reading
  - Writing to a file:
    ```bash
    stacker:0> "output.txt" "hoge" write
    ```
    This writes the string "hoge" to the file "output.txt".

  - Reading from a file:
    ```bash
    stacker:0> "output.txt" read
    [hoge]
    ```
    This reads the contents of "output.txt" and executes it.

    ```
    stacker:0> "output.txt" read $text set
    ```
    You can also set the contents of the file to a variable using the `set` command. 

## Running Scripts
Stacker scripts can be created in `.stk` files. To run a script, simply execute it with Stacker. For example:

- my_script.stk:
  ```bash
  0 $p set
  0 100000 $k {
      -1 k ^ 2 k * 1 + / p + p set
  } do
  4 p * p set
  p echo
  ```

  Running the script:  
  ```bash
  stacker my_script.stk
  ```


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
| dice     | Roll dice (e.g., 3d6)                                 | `3 6 dice`                 |


### Stack Operators
| Operator | Description                                               | Example                |
|----------|-----------------------------------------------------------|------------------------|
| drop     | Drops the top element of the stack.                       | `drop`                 |
| dup      | Duplicate the top element of the stack.                   | `dup`                  |
| swap     | Swap the top two elements of the stack.                   | `swap`                 |
| rev      | Reverse the stack.                                        | `rev`                  |
| rot      | Rotate n by n to the right.                               | `n rot`                |
| rotl     | Rotate n by n to the left.                                | `n rotl`               |
| pick     | Pick the nth element from the top of the stack.           | `n pick`               |
| count    | Counts the number of occurrences of a value in the stack. | `count`                |
| clear    | Clear the stack.                                          | `clear`                |


### Other Operators
| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| time     | Get Python time time object.                          | `time`                     |
| include  | Include the specified file                            | `"file.stk" include`       |
| eval     | Evaluate the specified RPN expression                 | `'3 5 +' eval`             |
| evalpy   | Evaluate the specified Python expression              | `'3+5' evalpy`             |
| echo     | Print the specified value to stdout without adding it to the stack | `3 4 + echo`  |
| println  | Print the specified value to stdout without adding it to the stack | `3 4 + println`  |
| print    | Print the specified value to stdout without adding a newline character at the end or adding it to the stack. | `3 4 + print`  |
| input    | Get input from the user                               | `input`                    |
| read     | Read the contents of the specified file               | `"file.txt" read`          |
| write    | Write the specified value to the specified file       | `"hoge" "file.txt" write`  |


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
