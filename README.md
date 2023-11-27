[**日本語  (Japanese)**](https://github.com/remokasu/stacker/blob/main/README_JP.md)


# Stacker: An RPN Calculator

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

### Running Scripts
Stacker scripts can be created in *stk files. To run a script, simply execute it with Stacker. For example:
```bash
stacker my_script.stk
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

## Documentation
For more detailed documentation, please refer to [`stacker/docs`](https://github.com/remokasu/stacker/blob/main/docs/README.md).
