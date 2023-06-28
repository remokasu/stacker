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
