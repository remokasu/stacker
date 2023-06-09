# Stacker: RPN Calculator in Python
~~~
  _____  _                 _
 / ____|| |               | |
| (___  | |_   __ _   ___ | | __  ___  _ __
 \___ \ | __| / _` | / __|| |/ / / _ \| '__|
 ____) || |_ | (_| || (__ |   < |  __/| |
|_____/  \__| \__,_| \___||_|\_\ \___||_|

~~~

Stacker is a simple yet powerful RPN calculator built with Python. It supports basic mathematical functions and allows users to define their own custom functions. The functionality of Stacker can be easily extended through the use of plugins, making it a versatile tool for various computational needs.


<br>
<hr>

# Install

If you don't have Python 3 installed, please install it beforehand.
Here are the installation instructions for `stacker`:

1. Install
    ~~~ bash
    > pip install pystacker
    ~~~

2. Run the program
    ~~~ bash
    > stacker
    ~~~

* or
    ~~~ bash
    > python -m stacker
    ~~~

<br>


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


# Feedback and Suggestions

We welcome your feedback and suggestions to improve Stacker. If you find a bug or have an idea for a new feature, please feel free to open an issue on the [Issues](https://github.com/remokasu/stacker/issues) page.


<br>
<hr>

# Dependencies and Licenses

Stacker uses the following external libraries:

- [Python Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit): Stacker uses the Python Prompt Toolkit library for providing an interactive and user-friendly command-line interface. This library allows Stacker to have features like syntax highlighting, autocompletion, and keyboard shortcuts. Python Prompt Toolkit is distributed under the [BSD 3-Clause License](https://github.com/prompt-toolkit/python-prompt-toolkit/blob/master/LICENSE).

- [NumPy](https://numpy.org/): NumPy is a fundamental library for scientific computing in Python. Stacker uses NumPy for the matrix operations plugin. NumPy is distributed under the [BSD 3-Clause License](https://github.com/numpy/numpy/blob/main/LICENSE.txt).

Please make sure to install these libraries when using Stacker. You can install them using the following command:

~~~
pip install numpy prompt_toolkit
~~~

It is important to respect and comply with the licenses of these dependencies while using Stacker.

<br>
<hr>


The following explanation will be provided in Japanese.

# 概要

ある晴れた日、学生Aは数学の試験に挑むため、緊張しながら教室へ向かっていました。しかし、彼はある重要なものを忘れてしまっていたのです。それは、関数電卓でした。

<br>

* 学生A（焦りながら）
    ~~~
    先生、電卓を忘れちゃったんですが、お借りできますか？
    ~~~

* 教授（待ってました！と言いたげな表情で）
    ~~~
    もちろんだ。特別に君にコレを貸してあげよう。
    ヒューレットパッカードの稀代の名機 「hp 50G」！！
    とっくに生産終了してしまって今では新品で買うことなど不可能なシロモノだ。
    Amaz●nではプレミアがついて10倍の値段で取引されている。
    このでっかい画面にはグラフも描画できちゃうぞ！
    さらにこの小さな端子はなななななんとRS-232！シリアル通信だってできちゃう！
    電卓のくせに一体何と通信するんだろうねぇ！？
    まあ、何故かコネクタは公式から発売されることは無かったから実質幻の機能だがな...
    どうだ？凄いだろう？
    ~~~

* 学生A（顔を輝かせつつ）
    ~~~
    ええっ！なにそれチートアイテムぅ！？（よく分かんないけど凄そう！デカイし！)
    やったあ...これで試験も余裕です！！(泣）
    ~~~

* 教授（ニヤリと笑いながら）
    ~~~
    ただし、これは逆ポーランド記法の電卓だぞ
    ~~~

* 学生A（戸惑いつつ）
    ~~~
    逆ポ...？逆ポーランドって何です？よく分かんないけど、なんかカッコいいですね！
    ~~~

* 教授（クスクス笑い）
    ~~~
    ちょっと普通の電卓とは扱い方が異なるだけだ。
    なに、心配することはないよ。普通の電卓のようなモードにも切り替えられるからね。
    ~~~

* 学生A（安心しながら）
    ~~~
    なるほど！ありがとうございます！！たすかりましたああ！！
    ~~~

* 教授（声には出さず）
    ~~~
    （ただし切り替え方は初見では分かり難いだろうねｸｸｸ...）
    ~~~


<br>
その試験で学生Aは泣いたという。

このプログラムは、A君のトラウマを追体験することができる。

<br>

<hr>

# ダウンロード & インストール

python3が無ければ事前にインストールしてください。
以下は`stacker`のインストール方法です。

1. ダウンロード & インストール
    ~~~ bash
    > pip install pystacker
    ~~~

2. 起動
    ~~~ bash
    > stacker
    ~~~

* または
    ~~~ bash
    > python -m stacker
    ~~~


* 遊び終わったら削除しましょう
    ~~~ bash
    > pip uninstall pystacker
    ~~~


# 使い方

| 演算子   | 説明                                                  | 使い方                      | 結果                       |
|--------|-----------------------------------------------------|--------------------------|--------------------------|
| +      | 加算                                                  | `3 5 +`                    | 8                        |
| -      | 減算                                                  | `10 3 -`                   | 7                        |
| *      | 乗算                                                  | `4 6 *`                    | 24                       |
| /      | 除算                                                  | `12 4 /`                   | 3                        |
| //     | 整数除算                                              | `7 2 //`                   | 3                        |
| %      | 剰余                                                  | `9 2 %`                    | 1                        |
| ^      | 累乗                                                  | `3 2 ^`                    | 9                        |
| neg    | 符号反転                                              | `5 neg`                    | -5                       |
| abs    | 絶対値                                                | `-3 abs`                   | 3                        |
| exp    | 指数関数                                              | `3 exp`                    | math.exp(3)              |
| log    | 自然対数                                              | `2 log`                    | math.log(2)              |
| log10  | 常用対数 (底10)                                       | `4 log10`                  | math.log10(4)            |
| log2   | 底2の対数                                             | `4 log2`                   | math.log2(4)             |
| sin    | 正弦                                                  | `30 sin`                   | math.sin(30)             |
| cos    | 余弦                                                  | `45 cos`                   | math.cos(45)             |
| tan    | 正接                                                  | `60 tan`                   | math.tan(60)             |
| asin   | 逆正弦                                                | `0.5 asin`                 | math.asin(0.5)           |
| acos   | 逆余弦                                                | `0.5 acos`                 | math.acos(0.5)           |
| atan   | 逆正接                                                | `1 atan`                   | math.atan(1)             |
| sinh   | 双曲線正弦                                            | `1 sinh`                   | math.sinh(1)             |
| cosh   | 双曲線余弦                                            | `1 cosh`                   | math.cosh(1)             |
| tanh   | 双曲線正接                                            | `1 tanh`                   | math.tanh(1)             |
| asinh  | 逆双曲線正弦                                          | `1 asinh`                  | math.asinh(1)            |
| acosh  | 逆双曲線余弦                                          | `2 acosh`                  | math.acosh(2)            |
| atanh  | 逆双曲線正接                                          | `0.5 atanh`                | math.atanh(0.5)          |
| sqrt   | 平方根                                                | `9 sqrt`                   | math.sqrt(9)             |
| ceil   | 切り上げ                                              | `3.2 ceil`                 | math.ceil(3.2)           |
| floor  | 切り捨て                                              | `3.8 floor`                | math.floor(3.8)          |
| round  | 四捨五入                                              | `3.5 round`                | round(3.5)               |
| roundn | 指定した小数点以下の桁数で四捨五入                    | `3.51 1 roundn`            | round(3.51, 1)           |
| float  | 浮動小数点数に変換                                    | `5 float`                  | 5.0                      |
| int    | 整数に変換                                            | `3.14 int`                 | 3                        |
| ==     | 等しい                                                | `1 1 ==`                   | True                     |
| !=     | 等しくない                                            | `1 0 !=`                   | True                     |
| <      | より小さい                                            | `1 2 <`                    | True                     |
| <=     | 以下                                                  | `3 3 <=`                   | True                     |
| >      | より大きい                                            | `2 1 >`                    | True                     |
| >=     | 以上                                                  | `3 3 >=`                   | True                     |
| and    | 論理積                                                | `true false and`           | False                    |
| or     | 論理和                                                | `true false or`            | True                     |
| not    | 論理否定                                              | `true not`                 | False                    |
| band   | ビットごとの論理積                                    | `3 2 band`                 | 3 & 2                    |
| bor    | ビットごとの論理和                                    | `3 2 bor`                  | 3 | 2                    |
| bxor   | ビットごとの排他的論理和                              | `3 2 bxor`                 | 3 ^ 2                    |
| >>     | 右ビットシフト                                        | `8 2 >>`                   | 2                        |
| <<     | 左ビットシ ト                                         | `2 2 <<`                   | 8                        |
| ~      | ビット反転                                            | `5 ~`                      | ~5                       |
| bin    | ２進数表示 (結果はstring)                             | `5 bin`                    | '0b101'                  |
| oct    | 8進数表示 (結果はstring)                              | `10 oct`                   | '0o12'                   |
| dec    | 10進数表示 (結果はinteger)                            | `0b101010 dec`             | 42                       |
| hex    | 16進数表示 (結果はstring)                             | `255 hex`                  | '0xff'                   |
| gcd    | 最大公約数                                            | `4 2 gcd`                  | math.gcd(4, 2)           |
| !      | 階乗                                                  | `4 !`                      | math.factorial(4)        |
| radians| 度数法から弧度法へ変換                                | `180 radians`              | math.radians(180)        |
| random | 0と1の間の乱数を生成                                  | `random`                   | random.random()          |
| randint| 指定した範囲内の整数乱数を生成                        | `1 6 randint`              | random.randint(1, 6)     |
| uniform| 指定した範囲内の浮動小数点数乱数を生成                | `1 2 uniform`              | random.uniform(1, 2)     |
| dice   | サイコロを振る (例：3d6)                              | `3 6 dice`                 | sum(random.randint(1, 6) for _ in range(3)) |
| delete   | 指定のindexを削除                                     | `2 delete`               | スタックからindex 2の要素を削除  |
| pluck    | 指定のindexを削除し、スタックのトップに移動           | `2 pluck`                | index 2の要素を削除し、スタックのトップに移動  |
| pick     | 指定されたインデックスの要素をスタックのトップにコピー | `2 pick`                | index 2の要素をスタックのトップにコピー  |
| pop      | スタックのトップを削除。popした値は`last_pop`で参照できます。 | `pop`            | スタックのトップを削除  |
| dup      | スタックのトップの要素を複製する                       | `dup`                   | スタックのトップの要素を複製 |
| swap     | スタックのトップの２つの要素を入れ替える               | `swap`                  | スタックのトップの２つの要素を入れ替え |
| exec     | 指定のPythonコードを実行                             | `{print(1+1)} exec`       | 1+1を出力し、2をプリント |
| eval     | 指定のPython式を評価                                 | `{1+1} eval`              | スタックに2を追加       |
| echo | 指定された値をstdoutに出力し、スタックには追加しない	| `3 4 + echo`	| 3+4の結果（7）をstdoutに出力し、スタックには追加しない |

<br>
<hr>

## 入力
* (例) 3 4 +
    ~~~ bash
    stacker:0> 3 4 +
    [7]
    ~~~

* または
    ~~~ bash
    stacker:0> 3
    [3]
    stacker:1> 4
    [3, 4]
    stacker:2> +
    [7]
    ~~~

* `"""`を使って複数行の入力ができます。`"""`で囲むことで、Enterキーを押しても入力が継続されます。以下に例を示します。
    ~~~
    stacker:0> """
    stacker:1> これは複数行の
    stacker:2> 入力の例です。
    stacker:3> """
    ['\nこれは複数行の\n入力の例です。\n']
    ~~~

入力は改行を含む1つの文字列として扱われます。

<br>
<hr>

## 配列の入力

配列は次のように入力します。
~~~ bash
stacker:0> [1 2 3; 4 5 6]
~~~

複数行にわたる配列の入力も可能です。例えば、以下のように入力できます。

~~~ bash
stacker:0> [1 2 3;
... > 4 5 6]
~~~

複数行入力中に配列が閉じられたとき、入力が終了します。ただし、複数行入力中に強制的に戻るには、`end`と入力してください。


<br>
<hr>

## Stackerにおける変数

Stackerでは、ユーザー自身が変数を定義することができます。これは`set`オペレータを用いて行います。変数定義の一般的な構文は以下の通りです：

~~~ bash
値 変数名 set
~~~


変数定義の各部分がどのように機能するかを以下に説明します：

1. `値`: これは変数に割り当てたい値です。

2. `変数名`: これは変数につける名前です。任意の有効な識別子を使用できます。

3. `set`: これはStackerに変数を定義していることを伝えるオペレータです。

変数定義の例を以下に示します：

~~~ bash
stacker 0:> 10 myVariable set
~~~

これにより、`10`という値を持つ`myVariable`という名前の変数が定義されます。 

この変数は他の任意の値と同様に使用することができます：

~~~ bash
stacker 1:> myVariable 20 +
~~~

これにより`30` ( `10 + 20`の結果)がスタックにプッシュされます。


<br>
<hr>

## Stackerにおける関数定義


Stackerでは、`fn`オペレータを使って自分自身の関数を定義することができます。関数定義の一般的な構文は次のようになります：

~~~ bash
(arg1 arg2 ... argN) {本体} 関数名 fn
~~~

以下に関数定義の各部分の働きを説明します：

1. `(arg1 arg2 ... argN)`: これは関数が受け入れる引数のリストです。必要なだけ引数を定義することができます。引数はスペースで区切られ、括弧で囲まれるべきです。

2. `{本体}`: これは関数の本体で、Stackerの逆ポーランド記法（RPN）構文で書かれます。本体は中括弧`{}`で囲むべきです。

3. `関数名`: これは関数に付ける名前です。有効な識別子であれば何でも良いです。

4. `fn`: これは関数を定義しているとStackerに指示するオペレータです。

関数定義の例を以下に示します：

~~~ bash
stacker 0:> (x y) {x y *} 掛け算 fn
~~~

これは`掛け算`という名前の関数を定義し、引数`x`と`y`を取り、それらを掛け合わせるというものです。

この関数は他のオペレータを呼び出すのと同じように呼び出すことができます：

~~~ bash
stacker 1:> 10 20 掛け算
~~~

これは`200`（`10 * 20`の結果）をスタックにプッシュします。

<br>
<hr>

## プラグインの使い方

Stackerのプラグインを作成するには、以下の手順に従ってください。

1. `plugins`ディレクトリに新しいPythonファイル（例：`my_plugin.py`）を作成します。
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


2. プラグインに必要な関数やクラスを定義します。
3. プラグインファイル内に、引数として`stacker_core`を1つ取る`setup`関数を定義します。
4. `setup`関数内で、`stacker_core`の`register_plugin`メソッドを使って、カスタムコマンドを登録します。例：
    ~~~ python
    description_en = "Returns the Collatz sequence for the given number."
    description_jp = "与えられた数値のコラッツ数列を返します。"

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
            description_en=description_en,  #  不要な場合はコメントアウトしてください。
            description_jp=description_jp   #  不要な場合はコメントアウトしてください。
        )
    ~~~

5. 以下のコマンドを実行してStackerを再インストールします：
    ~~~ bash
    python setup.py install
    ~~~

6. Stackerが起動すると、自動的にプラグインが読み込まれ、カスタムコマンドが利用可能になります。

英語（description_en）と日本語（description_jp）の説明の提供は任意です。必要がない場合は、それらの行をコメントアウトまたは削除してください。

<br>
<hr>


## clear
* `clear` でスタックを初期化
    ~~~ bash
    stacker:0> clear
    []
    ~~~

<br>
<hr>

## help
* `help` で使い方を表示
    ~~~ bash
    stacker:0> help
    ~~~

<br>
<hr>

## exit
* `exit` で終了
    ~~~ bash
    stacker:0> exit
    ~~~


<br>

# おまけ

## eval (逆ポーランドなんてクソ喰らえだ)
* '...'で囲った文字列を `eval` で評価できる。
やはり中置記法こそ正義なのです。
ところで、なんで君はStackerを使ってるんですか？
    ~~~
    stacker:0> '3 + 5' eval
    [8]
    ~~~
