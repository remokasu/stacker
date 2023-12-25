[**日本語  (Japanese)**](https://github.com/remokasu/stacker/blob/main/README_JP.md)


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

- #### Variables:
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

- #### Conditionals:
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

- #### Loops:
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

- #### Define a function:
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

- #### Define a macro:
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

- #### Include Scripts
  Stacker scripts can be included in other scripts using the `include` command. For example:

  ``` bash
  stacker:0>  "my_script.stk" include
  ```
  All functions, macros and variables defined in "my_script.stk" are added to the current stack.


### Running Scripts
Stacker scripts can be created in *stk files. To run a script, simply execute it with Stacker. For example:

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


### Command Line Execution
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
  Note that it cannot be used on non-plugin oeratirs.

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

1. In the `plugins` directory, create a new Python file for your plugin (e.g., `my_plugin.py`). 
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

2. Alternatively, create a `plugins` directory in the directory where Stacker is executed. This allows you to use plugins without reinstalling Stacker.
3. Define required functions or classes in your plugin file.
4. Add a `setup` function to register these with Stacker.


Example:
```python
from stacker.stacker import Stacker

def function(a, b):
    # Do something

def setup(stacker: Stacker):
    stacker.register_plugin("command", function)
```

## Disabling Plugins
Use operatorName disable_plugin to disable a specific plugin.<br>
Use disable_all_plugins to disable all plugins.<br>


## Documentation
For more detailed documentation, please refer to [`stacker/docs`](https://github.com/remokasu/stacker/blob/main/docs/README.md).


## Supported Operations
`+` `-` `*` `/` `//` `/` `%` `++` `--` `neg` `bin` `oct` `dec` `hex` `band` `bor` `bxor` `~` `>>` `<<` `==` `!=` `<=` `<` `>=` `>` `eq` `noq` `le` `lt` `ge` `gt` `echo` `print` `and` `or` `not` `&&` `||` `^` `log` `log2` `log10` `exp` `sin` `cos` `tan` `asin` `acos` `atan` `sinh` `cosh` `tanh` `asinh` `acosh` `atanh` `sqrt` `gcd` `lcm` `radians` `!` `ceil` `floor` `comb` `perm` `abs` `cbrt` `ncr` `npr` `roundn` `round` `rand` `randint` `uniform` `dice` `int` `float` `str` `bool` `seq` `range` `min` `sum` `max` `len` `drop` `dup` `swap` `pick` `rot` `rotl` `insert` `rev` `clear` `disp` `eval` `asc` `chr` `concat` `time` `if` `ifelse` `times` `do` `set` `defun` `alias` `include`
