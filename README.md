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

- Variables:

  ```bash
  stacker:0> 3 $x set
  ```
  This sets the variable `x` to `3`.

- Define a macro:
  ```bash
  stacker:0> {2 ^ 3 * 5 +} $calculatePowerAndAdd alias
  stacker:1> 5 calculatePowerAndAdd
  [80]
  ```
    This defines a macro with the body `{2 ^ 3 * 5 +}` and assigns it the name `calculatePowerAndAdd`. This macro squares the number on the stack, multiplies it by 3, and then adds 5.

- Define a function:
  ```bash
  stacker:0> (x y) {x y *} $multiply defun
  stacker:1> 10 20 multiply
  [200]
  ```
    This defines a function named `multiply` that takes two arguments `x` and `y` and multiplies them together.

### Running Scripts
Stacker scripts can be created in *stk files. To run a script, simply execute it with Stacker. For example:

- my_script.stk:
  ```bash
    100000 $n set
    0 $p set
    0 n $k {
        -1 k ^ 2 k * 1 + / p + p set
    } do
    4 p * p set
    p echo
  ```

  Running the script:  
  ```bash
  stacker my_script.stk
  ```

### Include Scripts
Stacker scripts can be included in other scripts using the `include` command. For example:

``` bash
stacker:0>  "my_script.stk" include
```
All functions, macros and variables defined in "my_script.stk" are added to the current stack.


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

## Documentation
For more detailed documentation, please refer to [`stacker/docs`](https://github.com/remokasu/stacker/blob/main/docs/README.md).


## Supported Operations
`+` `-` `*` `/` `//` `/` `%` `++` `--` `bin` `oct` `dec` `hex` `band` `bor` `bxor` `~` `>>` `<<` `==` `!=` `<=` `<` `>=` `>` `eq` `noq` `le` `lt` `ge` `gt` `echo` `print` `and` `or` `not` `&&` `||` `^` `log` `log2` `log10` `exp` `sin` `cos` `tan` `asin` `acos` `atan` `sinh` `cosh` `tanh` `asinh` `acosh` `atanh` `sqrt` `gcd` `lcm` `radians` `!` `ceil` `floor` `comb` `perm` `abs` `cbrt` `ncr` `npr` `roundn` `round` `rand` `randint` `uniform` `dice` `int` `float` `str` `bool` `seq` `range` `min` `sum` `max` `len` `drop` `dup` `swap` `pick` `rot` `rotl` `insert` `rev` `clear` `disp` `eval` `asc` `chr` `concat` `time` `if` `ifelse` `times` `do` `set` `defun` `alias` `include`
