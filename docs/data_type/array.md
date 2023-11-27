# Array Input

You can input arrays in Stacker using the following format:
~~~ bash
stacker:0> [1 2 3; 4 5 6]
~~~

Multi-line array input is also possible. For example, you can enter an array as follows:

~~~ bash
stacker:0> [1 2 3;
... > 4 5 6]
~~~

The input will be considered complete when the array is closed with a matching bracket. However, if you want to forcibly go back while in multi-line input mode, type `end`.
