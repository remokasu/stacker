# Block stack

Code blocks are enclosed in curly braces ({}). These blocks are pushed onto the stack in their raw form and can be executed later. For example: {1 2 +}. These blocks are particularly useful for deferred (lazy) evaluation. Specific use-cases include conditional statements and loop controls.


## Adding Basic Blocks

~~~ bash
stacker:0> {1 2 +}
[{1 2 +}]
~~~

In this command, the block {1 2 +} is pushed (added) to the stack. 
