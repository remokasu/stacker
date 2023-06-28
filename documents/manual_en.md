# Usage

| Operator | Description                                           | Example                    | Result                   |
|----------|-------------------------------------------------------|----------------------------|--------------------------|
| +        | Add                                                   | `3 5 +`                    | 8                        |
| -        | Subtract                                              | `10 3 -`                   | 7                        |
| *        | Multiply                                              | `4 6 *`                    | 24                       |
| /        | Divide                                                | `12 4 /`                   | 3                        |
| //       | Integer divide                                        | `7 2 //`                   | 3                        |
| %        | Modulus                                               | `9 2 %`                    | 1                        |
| ^        | Power                                                 | `3 2 ^`                    | 9                        |
| neg      | Negate                                                | `5 neg`                    | -5                       |
| abs      | Absolute value                                        | `-3 abs`                   | 3                        |
| exp      | Exponential                                           | `3 exp`                    | math.exp(3)              |
| log      | Natural logarithm                                     | `2 log`                    | math.log(2)              |
| log10    | Common logarithm (base 10)                            | `4 log10`                  | math.log10(4)            |
| log2     | Logarithm base 2                                      | `4 log2`                   | math.log2(4)             |
| sin      | Sine                                                  | `30 sin`                   | math.sin(30)             |
| cos      | Cosine                                                | `45 cos`                   | math.cos(45)             |
| tan      | Tangent                                               | `60 tan`                   | math.tan(60)             |
| asin     | Arcsine                                               | `0.5 asin`                 | math.asin(0.5)           |
| acos     | Arccosine                                             | `0.5 acos`                 | math.acos(0.5)           |
| atan     | Arctangent                                            | `1 atan`                   | math.atan(1)             |
| sinh     | Hyperbolic sine                                       | `1 sinh`                   | math.sinh(1)             |
| cosh     | Hyperbolic cosine                                     | `1 cosh`                   | math.cosh(1)             |
| tanh     | Hyperbolic tangent                                    | `1 tanh`                   | math.tanh(1)             |
| asinh    | Inverse hyperbolic sine                               | `1 asinh`                  | math.asinh(1)            |
| acosh    | Inverse hyperbolic cosine                             | `2 acosh`                  | math.acosh(2)            |
| atanh    | Inverse hyperbolic tangent                            | `0.5 atanh`                | math.atanh(0.5)          |
| sqrt     | Square root                                           | `9 sqrt`                   | math.sqrt(9)             |
| ceil     | Ceiling                                               | `3.2 ceil`                 | math.ceil(3.2)           |
| floor    | Floor                                                 | `3.8 floor`                | math.floor(3.8)          |
| round    | Round                                                 | `3.5 round`                | round(3.5)               |
| roundn   | Round to specified decimal places                     | `3.51 1 roundn`            | round(3.51, 1)           |
| float    | Convert to floating-point number                      | `5 float`                  | 5.0                      |
| int      | Convert to integer                                    | `3.14 int`                 | 3                        |
| ==       | Equal                                                 | `1 1 ==`                   | True                     |
| !=       | Not equal                                             | `1 0 !=`                   | True                     |
| <        | Less than                                             | `1 2 <`                    | True                     |
| <=       | Less than or equal to                                 | `3 3 <=`                   | True                     |
| >        | Greater than                                          | `2 1 >`                    | True                     |
| >=       | Greater than or equal to                              | `3 3 >=`                   | True                     |
| and      | Logical and                                           | `true false and`           | False                    |
| or       | Logical or                                            | `true false or`            | True                     |
| not      | Logical not                                           | `true not`                 | False                    |
| band     | Bitwise and                                           | `3 2 band`                 | 3 & 2                    |
| bor      | Bitwise or                                            | `3 2 bor`                  | 3 | 2                    |
| bxor     | Bitwise xor                                           | `3 2 bxor`                 | 3 ^ 2                    |
| >>       | Right bit shit                                        | `8 2 >>`                   | 2                        |
| <<       | Left bit shit                                         | `2 2 <<`                   | 8                        |
| ~        | Bitwise not                                           | `5 ~`                      | ~5                       |
| bin      | Binary representation (result is a string)            | `5 bin`                    | '0b101'                  |
| oct      | Octal representation (result is a string)             | `10 oct`                   | '0o12'                   |
| dec      | Decimal representation (result is an integer)         | `0b101010 dec`             | 42                       |
| hex      | Hexadecimal representation (result is a string)       | `255 hex`                  | '0xff'                   |
| gcd      | Greatest common divisor                               | `4 2 gcd`                  | math.gcd(4, 2)           |
| !        | Factorial                                             | `4 !`                      | math.factorial(4)        |
| radians  | Convert degrees to radians                            | `180 radians`              | math.radians(180)        |
| random   | Generate a random floating-point number between 0 and 1| `random`                   | random.random()          |
| randint  | Generate a random integer within a specified range    | `1 6 randint`              | random.randint(1, 6)     |
| uniform  | Generate a random floating-point number within a specified range | `1 2 uniform` | random.uniform(1, 2) |
| dice     | Roll dice (e.g., 3d6)                                 | `3 6 dice`                 | sum(random.randint(1, 6) for _ in range(3)) |
| delete   | Remove the element at the specified index             | `2 delete`                 | Remove the element at index 2 from the stack  |
| pluck    | Remove the element at the specified index and move it to the top of the stack | `2 pluck`              | Remove the element at index 2 and move it to the top of the stack  |
| pick     | Copy the element at the specified index to the top of the stack | `2 pick`                   | Copy the element at index 2 to the top of the stack  |
| pop      | Remove the top element from the stack. The value popped can be referred to as `last_pop`.   | `pop`  | Remove the top element from the stack  |
| dup      | Duplicate the top element of the stack                | `dup`                   | Duplicate the top element of the stack |
| swap     | Swap the top two elements of the stack                | `swap`                  | Swap the top two elements of the stack |
| exec     | Execute the specified Python code                    | `{print(1+1)} exec`        | Execute 1+1 and print 2 |
| eval     | Evaluate the specified Python expression             | `{1+1} eval`               | Add 2 to the stack       |
| echo     | Print the specified value to stdout without adding it to the stack | `3 4 + echo` | Print the result of 3+4 (7) to stdout without adding it to the stack |

<br>
<hr>

## Input like this.

* (Example) 3 4 +
    ~~~ bash
    stacker:0> 3 4 +
    [7]
    ~~~

* Or,
    ~~~ bash
    stacker:0> 3
    [3]
    stacker:1> 4
    [3, 4]
    stacker:2> +
    [7]
    ~~~

* You can use triple quotes `"""` to enter multi-line input. When you enclose your input with triple quotes, you can continue entering text even after pressing Enter. Here's an example:
    ~~~
    stacker:0> """
    stacker:1> This is a multi-line
    stacker:2> input example.
    stacker:3> """
    ['\nThis is a multi-line\ninput example.\n']
    ~~~

The input will be treated as a single string containing line breaks:

<br>
<hr>

## Array Input

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



<br>
<hr>

## Variables in Stacker

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

<br>
<hr>


## Function Definitions in Stacker

In Stacker, you can define your own functions using the `fn` operator. The general syntax for function definition is as follows:

~~~ bash
(arg1 arg2 ... argN) {body} functionName fn
~~~

Here's how each part of the function definition works:

1. `(arg1 arg2 ... argN)`: This is a list of arguments that your function will accept. You can define as many arguments as needed. The arguments should be space-separated and enclosed in parentheses.

2. `{body}`: This is the body of your function, which is written in Stacker's Reverse Polish Notation (RPN) syntax. The body should be enclosed in curly braces `{}`.

3. `functionName`: This is the name you're giving to your function. It can be any valid identifier.

4. `fn`: This is the operator that tells Stacker you're defining a function.

Here's an example of a function definition:

~~~ bash
stacker 0:> (x y) {x y *} multiply fn
~~~

This defines a function named `multiply` that takes two arguments `x` and `y` and multiplies them together. 

You can call this function just like you'd call any other operator:

~~~ bash
stacker 1:> 10 20 multiply
~~~

This will push `200` (the result of `10 * 20`) onto the stack.

<br>
<hr>


## Plugin Usage

To create a plugin for Stacker, follow these steps:

1. Create a new Python file (e.g., `my_plugin.py`) in the `plugins` directory.
    ~~~
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
    ~~~


2. Define any functions or classes required for your plugin.
3. Define a `setup` function in your plugin file that takes a single argument: `stacker_core`.
4. In the `setup` function, use the `register_plugin` method of `stacker_core` to register your custom commands. For example:
    ~~~python
    description_en = "Returns the Collatz sequence for the given number."
    description_jp = ""

    def collatz_sequence(n):
        seq = [n]
        while n != 1:
            if n % 2 == 0:
                n //= 2
            else:
                n = n * 3 + 1
            seq.append(n)
        return seq

    def setup(stacker_core):
        stacker_core.register_plugin(
            "collatz", lambda x: collatz_sequence(x),
            description_en=description_en,  #  Please comment out if not necessary.
            description_jp=description_jp   #  不要な場合はコメントアウト
        )
    ~~~

5. Reinstall Stacker by running the following command:
    ~~~bash
    python setup.py install
    ~~~

5. Save your plugin file in the plugins directory.
6. When Stacker starts, it will automatically load your plugin, and your custom command will be available for use.


<br>
<hr>

## clear
* Clear the stack with 'clear'
    ~~~ bash
    stacker:0> clear
    []
    ~~~

<br>
<hr>

## help
* Display usage instructions with `help`
    ~~~ bash
    stacker:0> help
    ~~~

<br>
<hr>

## exit
* Exit the program with 'exit'
    ~~~ bash
    stacker:0> exit
    ~~~

<br>
