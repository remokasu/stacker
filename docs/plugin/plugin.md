## Creating and Using Stacker Plugins

To create and use plugins in Stacker, follow these steps:

### Adding Directly to the Installation Directory

1. **Creating the Plugin**:
   Create a new Python file in the `plugins` directory (e.g., `my_plugin.py`).
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

2. **Defining Functions and Classes**:
   Define the necessary functions and classes in `my_plugin.py`.

3. **Defining the `setup` Function**:
   In `my_plugin.py`, define a `setup` function that takes `stacker` as its only argument.

4. **Registering Custom Commands and Parameters**:

    Within the `setup` function, use the `register_plugin` method of `stacker` to register custom commands. Additionally, you can also register custom parameters using the `register_parameter` method. This allows for greater flexibility and customization in your plugin's behavior.

    Here's an example where custom commands for matrix operations and a custom parameter are registered:

    ```python
    import numpy as np
    from stacker.stacker import Stacker

    # Write your function definitions here

    def _is_matrix_or_vector(value):
        if not isinstance(value, list):
            return False
        if len(value) == 0:
            return False
        return isinstance(value[0], list) or isinstance(value[0], (int, float))

    def matrix_add(a, b):
        if _is_matrix_or_vector(a) and _is_matrix_or_vector(b):
            return np.add(a, b).tolist()
        elif not _is_matrix_or_vector(a) and not _is_matrix_or_vector(b):
            return a + b
        else:
            raise ValueError("Both operands must be matrices (or vectors) for matrix addition.")

    def matrix_sub(a, b):
        if _is_matrix_or_vector(a) and _is_matrix_or_vector(b):
            return np.subtract(a, b).tolist()
        elif not _is_matrix_or_vector(a) and not _is_matrix_or_vector(b):
            return a - b
        else:
            raise ValueError("Both operands must be matrices (or vectors) for matrix subtraction.")

    def matrix_mul(a, b):
        if _is_matrix_or_vector(a) and _is_matrix_or_vector(b):
            return np.matmul(a, b).tolist()
        elif not _is_matrix_or_vector(a) and not _is_matrix_or_vector(b):
            return a * b
        else:
            raise ValueError("Both operands must be matrices (or vectors) for matrix multiplication.")

    # Example of setting up custom commands and a parameter
    def setup(stacker: Stacker):
        stacker.register_plugin("+", matrix_add, description_en="Matrix addition")
        stacker.register_plugin("-", matrix_sub, description_en="Matrix subtraction")
        stacker.register_plugin("*", matrix_mul, description_en="Matrix multiplication")
        
        # Registering a custom parameter
        stacker.register_parameter("custom_param", custom_value)

        # Additional plugin setup can go here
        ...
    ```
    You can specify the command description for the help command using description_en or description_jp. This field is optional.

    This example demonstrates how to register functions for matrix operations and how to set a custom parameter within a plugin. The register_parameter method is used to add a custom parameter to the Stacker environment, allowing for additional customization and control within your plugin.

5. **Reinstalling Stacker**:
   Run the following command to reinstall Stacker:
    ```
    > python setup.py install
    ```

6. **Using the Plugin**:
   When Stacker is launched, the plugin will automatically be loaded, and the custom commands will be available for use.

### Adding to the Execution Directory

1. **Creating the Directory and Adding the Plugin**:
   Create a `plugins` directory in the directory where Stacker is executed and add your plugin there. The method for creating it is the same as described above. This method does not require reinstalling Stacker.
