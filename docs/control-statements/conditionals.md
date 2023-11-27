# Conditional Statements

⚠ This feature is provisionally implemented and may change in future versions. If you have any feedback regarding its specifications, please contact us at [Issues](https://github.com/remokasu/stacker/issues).

You can use `if` or `ifelse` for conditional branching.

## if
~~~ bash
{true block} {condition} if
~~~

- Example
    ~~~ bash
    0 x set
    {...} {x 0 >=} if
    ~~~
In this example, `{...}` will be executed if `x` is greater than or equal to 0.
Both {true block} and {condition} must be enclosed in {}.

## ifelse
⚠ This feature is provisionally implemented and may change in future versions. If you have any feedback regarding its specifications, please contact us at [Issues](https://github.com/remokasu/stacker/issues).

If the condition is true, it executes the true block; otherwise, it executes the false block.
~~~ bash
{true block} {false block} {condition} ifelse
~~~

- Example
    ~~~ bash
    0 x set
    {...} {...} {x 0 >=} ifelse
    ~~~
In this example, `{...}` will be executed if `x` is greater than or equal to 0, and `{...}` will be executed if it's less than 0.