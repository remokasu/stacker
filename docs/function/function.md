## Function Definitions in Stacker

In Stacker, you can define your own functions using the `defun` operator. The general syntax for function definition is as follows:

~~~ bash
(arg1 arg2 ... argN) {body} functionName defun
~~~

Here's how each part of the function definition works:

1. `(arg1 arg2 ... argN)`: This is a list of arguments that your function will accept. You can define as many arguments as needed. The arguments should be space-separated and enclosed in parentheses.

2. `{body}`: This is the body of your function, which is written in Stacker's Reverse Polish Notation (RPN) syntax. The body should be enclosed in curly braces `{}`.

3. `functionName`: This is the name you're giving to your function. It can be any valid identifier.

4. `defun`: This is the operator that tells Stacker you're defining a function.

Here's an example of a function definition:

~~~ bash
stacker 0:> (x y) {x y *} multiply defun
~~~

This defines a function named `multiply` that takes two arguments `x` and `y` and multiplies them together. 

You can call this function just like you'd call any other operator:

~~~ bash
stacker 1:> 10 20 multiply
~~~

This will push `200` (the result of `10 * 20`) onto the stack.