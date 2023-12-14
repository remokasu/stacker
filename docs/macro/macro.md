## Macro Definitions in Stacker

In Stacker, you can define your own macros using a specific syntax. The general syntax for macro definition is as follows:

~~~bash
{body} $name alias
~~~

Here's how each part of the macro definition works:

1. `{body}`: This is the body of your macro, written in Stacker's Reverse Polish Notation (RPN) syntax. The body should be enclosed in curly braces `{}`.

2. `name`: This is the name you're assigning to your macro. `name` can be any valid string.
If "name" is an undefined symbol, you need to prefix the symbol name with a dollar sign ($) at the beginning.

3. `alias`: This is the operator that finalizes the macro definition.

Here's an example of a macro definition:

~~~bash
stacker 0:> {2 ^ 3 * 5 +} $calculatePowerAndAdd alias
~~~

This defines a macro with the body `{2 ^ 3 * 5 +}` and assigns it the name `calculatePowerAndAdd`. This macro squares the number on the stack, multiplies it by 3, and then adds 5.

You can execute this macro just like you'd perform any other operation:

~~~bash
stacker 1:> 4 calculatePowerAndAdd
~~~

This will push `53` (the result of `4 ^ 2 * 3 + 5`) onto the stack.
