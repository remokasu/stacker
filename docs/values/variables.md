# Variables

In Stacker, you can define your own variables. This is done by using the `def` operator. The general syntax for variable definition is as follows:

~~~
value variableName set
~~~


Here's how each part of the variable definition works:

1. `value`: This is the value that you want to assign to the variable.

2. `variableName`: This is the name you're giving to your variable. It can be any valid identifier.

3. `set`: This is the operator that tells Stacker you're defining a variable.

Here's an example of a variable definition:

~~~ bash
stacker 0:> 10 myVariable set
~~~

This defines a variable named `myVariable` that holds the value `10`. 

You can use this variable just like you'd use any other value:

~~~ bash
stacker 1:> myVariable 20 +
~~~

This will push `30` (the result of `10 + 20`) onto the stack.