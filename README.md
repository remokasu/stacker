# Stacker: RPN Calculator in Python
~~~
  _____  _                 _
 / ____|| |               | |
| (___  | |_   __ _   ___ | | __  ___  _ __
 \___ \ | __| / _` | / __|| |/ / / _ \| '__|
 ____) || |_ | (_| || (__ |   < |  __/| |
|_____/  \__| \__,_| \___||_|\_\ \___||_|

~~~

Welcome to Stacker, where we stack things up - but only in the right order! 😉
This powerful, yet humble, Reverse Polish Notation (RPN) calculator is here to make your life easier.
We know, it's not every day you encounter a calculator that loves postfix expressions as much as we do. 🤓

With Stacker, you'll experience the joy of crunching numbers without the hassle of parentheses. 🥴

Our calculator is so dedicated to the cause that it even lets you define your own functions - isn't that fantastic? 🚀

So, go ahead and give Stacker a spin! Just remember, if you ever feel lost, type "help" and we'll be there for you.
Happy stacking! 🎉


# Download & Install

If you don't have Python 3 installed, please install it beforehand.
Here are the installation instructions for `stacker`:

1. Download
~~~ bash
> git clone git@github.com:remokasu/stacker.git
~~~

2. Install dependencies
~~~
pip install setuptools
~~~

* For Windows users only
~~~ bash
> pip install pyreadline
~~~

3. Run the program without installation
~~~ bash
> cd stacker/stacker
> python stacker.py
~~~

4. (Or) Install and run the program
~~~ bash
cd stacker
> python setup.py install
> stacker
~~~

* When you're done playing with it, uninstall
~~~ bash
> pip uninstall stacker
~~~


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
| gcd      | Greatest common divisor                               | `4 2 gcd`                  | math.gcd(4, 2)           |
| !        | Factorial                                             | `4 !`                      | math.factorial(4)        |
| radians  | Convert degrees to radians                            | `180 radians`              | math.radians(180)        |
| roundn   | Round to specified decimal places                     | `3.51 1 roundn`            | round(3.51, 1)           |
| random   | Generate a random floating-point number between 0 and 1| `random`                   | random.random()          |
| randint  | Generate a random integer within a specified range    | `1 6 randint`              | random.randint(1, 6)     |
| uniform  | Generate a random floating-point number within a specified range | `1 2 uniform` | random.uniform(1, 2) |
| d        | Roll dice (e.g., 3d6)                                 | `3 6 d`                     | sum(random.randint(1, 6) for _ in range(3)) |


<hr>

## Custom Functions::

### Example 2: Function to calculate the average of two numbers (average)
~~~ bash
stacker:0> x y average => x y + 2 /
stacker:1> 2 6 average
[4.0]
~~~


(Note that the function definition syntax is a custom RPN-like syntax, so please don't worry about it)

<br>

<hr>

## You can also enter input like this. In fact, this is the normal way to use it.
(Example) 3 4 +
~~~ bash
stacker:0> 3
[3.0]
stacker:1> 4
[3.0, 4.0]
stacker:2> +
[7.0]
~~~

## clear
Clear the stack with 'clear'
~~~
stacker:0> clear
[]
~~~

## exit
Exit the program with 'exit'
~~~
stacker:0> exit
~~~

## about
Display Stacler's information with `about` (not particularly meaningful)
~~~
stacker:0> about
~~~

## help
Display usage instructions with `help`
~~~
stacker:0> help
~~~


<br>
<hr>

# 概要

ある晴れた日、学生Aは数学の試験に挑むため、緊張しながら教室へ向かっていました。しかし、彼はある重要なものを忘れてしまっていたのです。それは、関数電卓でした。

<br>

`学生A（焦りながら）`
~~~
先生、電卓を忘れちゃったんですが、お借りできますか？
~~~

`教授（待ってました！と言いたげな表情で）`
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

`学生A（顔を輝かせつつ）`
~~~
ええっ！なにそれチートアイテムぅ！？（よく分かんないけど凄そう！デカイし！)
やったあ...これで試験も余裕です！！(泣）
~~~

`教授（ニヤリと笑いながら）`
~~~
ただし、これは逆ポーランド記法の電卓だぞ
~~~

`学生A（戸惑いつつ）`
~~~
逆ポ...？逆ポーランドって何です？よく分かんないけど、なんかカッコいいですね！
~~~

`教授（クスクス笑い）`
~~~
ちょっと普通の電卓とは扱い方が異なるだけだ。
なに、心配することはないよ。普通の電卓のようなモードにも切り替えられるからね。
~~~

`学生A（安心しながら）`
~~~
なるほど！ありがとうございます！！たすかりましたああ！！
~~~

`教授（声には出さず）`
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

1. ダウンロード
~~~ bash
> git clone git@github.com:remokasu/stacker.git
~~~

2. 依存環境インストール
~~~
> pip install setuptools
~~~

* windowsの場合のみ
~~~ bash
> pip install pyreadline
~~~

3. インストールせず直接起動
~~~ bash
> cd stacker/stacker
> python stacker.py
~~~

4. (または)インストールして起動
~~~ bash
cd stacker
> python setup.py install
> stacker
~~~

* 遊び終わったら削除しましょう
~~~ bash
> pip uninstall stacker
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
| floor  | 切り捨て                                              | 3.8 floor                  | math.floor(3.8)          |
| round  | 四捨五入                                              | 3.5 round                  | round(3.5)               |
| float  | 浮動小数点数に変換                                    | 5 float                    | 5.0                      |
| int    | 整数に変換                                            | 3.14 int                   | 3                        |
| ==     | 等しい                                                | 1 1 ==                     | True                     |
| !=     | 等しくない                                            | 1 0 !=                     | True                     |
| <      | より小さい                                            | 1 2 <                      | True                     |
| <=     | 以下                                                  | 3 3 <=                     | True                     |
| >      | より大きい                                            | 2 1 >                      | True                     |
| >=     | 以上                                                  | 3 3 >=                     | True                     |
| and    | 論理積                                                | true false and             | False                    |
| or     | 論理和                                                | true false or              | True                     |
| not    | 論理否定                                              | true not                   | False                    |
| band   | ビットごとの論理積                                    | 3 2 band                   | 3 & 2                    |
| bor    | ビットごとの論理和                                    | 3 2 bor                    | 3 | 2                    |
| bxor   | ビットごとの排他的論理和                              | 3 2 bxor                   | 3 ^ 2                    |
| gcd    | 最大公約数                                            | 4 2 gcd                    | math.gcd(4, 2)           |
| !      | 階乗                                                  | 4 !                        | math.factorial(4)        |
| radians| 度数法から弧度法へ変換                                | 180 radians                | math.radians(180)        |
| roundn | 指定した小数点以下の桁数で四捨五入                    | 3.51 1 roundn              | round(3.51, 1)           |
| random | 0と1の間の乱数を生成                                  | random                     | random.random()          |
| randint| 指定した範囲内の整数乱数を生成                        | 1 6 randint                | random.randint(1, 6)     |
| uniform| 指定した範囲内の浮動小数点数乱数を生成                | 1 2 uniform                | random.uniform(1, 2)     |
| d      | サイコロを振る (例：3d6)                              | 3 6 d                      | sum(random.randint(1, 6) for _ in range(3)) |


<br>
<hr>

## 自作関数:

### 例 1: 二つの数の平均を計算する関数 (average)
~~~ bash
stacker:0> x y average => x y + 2 /
stacker:1> 2 6 average
[4.0]
~~~


(関数定義の構文はRPN構文っぽい独自定義の構文なので突っ込まないでくれ)

<br>

<hr>

## こんな入力も出来るよ。というかこっちが普通の使い方
(例) 3 4 +
~~~ bash
stacker:0> 3
[3.0]
stacker:1> 4
[3.0, 4.0]
stacker:2> +
[7.0]
~~~

## clear
`clear` でスタックを初期化
~~~
stacker:0> clear
[]
~~~

## exit
`exit` で終了
~~~
stacker:0> exit
~~~

## about
`about` でStaclerの情報を表示(特に意味なし)
~~~
stacker:0> about
~~~

## help
`help` で使い方を表示
~~~
stacker:0> help
~~~


<br>
<hr>

