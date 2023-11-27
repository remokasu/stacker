# Loops

⚠ This feature is provisionally implemented and may change in future versions.

You can perform loop operations using `times` or `for`.

## times
~~~ bash
{loop body} count times
~~~
The loop body is treated as a single operation enclosed in `{}`.

- Example
    Increment variable `x` 10 times and output its value.
    ~~~ bash
    0 x set
    {x ++ x set x echo} 10 times
    ~~~

## for
~~~ bash
start end seq {loop body} i for
~~~
Here, `i` is a variable that represents the number of iterations. You can use any variable name.
The loop body is also treated as a single operation enclosed in `{}`.
Within the loop body enclosed in `{}`, `i` is replaced by the current iteration number.

- Example
    Find the sum of squares from 1 to 100.

    \( S = 1^2 + 2^2 + 3^2 + ... + 100^2 = \sum_{i=1}^{100} i^2 \)

    ~~~ bash
    0 s set
    1 100 seq
    {
        s i 2 ^ + s set
    } i for
    s echo
    ~~~