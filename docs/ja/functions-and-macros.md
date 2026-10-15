# 関数・ラムダ・マクロ

コードに名前を付けて再利用する方法は 4 つあります。違いは、引数をいつ・どのように受け取るかです。

| 手段 | 引数の受け取り方 | 呼び出し方 |
|------|------------------|------------|
| `defun` | スタックの値を名前に束縛する | 名前を書く |
| `lambda` | スタックの値を名前に束縛する | 値として扱い、`eval` で呼ぶ |
| `alias` | 受け取らない（呼び出し側のスタックをそのまま使う） | 名前を書く |
| `defmacro` | 引数を値ではなくコードとして受け取る | 名前を書く |

## defun

```
{引数1 引数2 ...} {本体} :名前 defun
```

呼び出すと、スタックの上から引数の個数だけ値が取り出され、書いた順に名前へ束縛されます。つまり最後の引数がスタックの一番上の値です。

```
stacker:0> {a b} {a b -} :sub2 defun
[]
stacker:1> 10 3 sub2
[7]
```

結果は本体がスタックに残した値です。引数が足りないとエラーになり、多く積んであれば余りはそのまま残ります。

```
stacker:0> {x y} {x y +} :add defun
[]
stacker:1> 3 4 5 add
[3 9]
```

引数の名前は、重複しない裸の名前でなければなりません。

```text
$ {x x} {x} :f defun
StackerSyntaxError: `defun` argument names must be unique: {x x}
$ {1} {2} :f defun
StackerSyntaxError: `defun` argument names must be bare names, got 1
```

引数は関数の中だけの変数です。`:名前 set` で関数の中に作った変数も関数の外には出ません。外にも残したいときは `global` を使います。関数の外の変数は、本体から読めます。

```
stacker:0> 10 :k set
[]
stacker:1> {a} {a k +} :addk defun
[]
stacker:2> 1 addk
[11]
```

関数の中で `global` を使うと、関数の外にも残る変数を作れます。

```
stacker:0> {a} {a 1 + :z global} :g defun
[]
stacker:1> 1 g
[]
stacker:2> z
[2]
```

### 再帰

本体の中で自分自身を呼べます。

```
stacker:0> {n} {n 1 <= {1} {n n 1 - fact *} ifelse} :fact defun
[]
stacker:1> 10 fact
[3628800]
```

再帰の深さの上限は [スクリプトとファイルの取り込み](scripts.md) を参照してください。

## lambda

```
{引数1 引数2 ...} {本体} lambda
```

名前を付けずに関数を作り、スタックに値として置きます。表示は `λxλy.{x y *}` の形です。作っただけでは実行されません。

```
stacker:0> {x y} {x y *} lambda
[λxλy.{x y *}]
```

### 変数に入れて呼ぶ

変数に入れたラムダは、名前を書いても値としてスタックに積まれるだけです。呼ぶには、引数を積んだあとにラムダを積み、`eval` を実行します。

```
stacker:0> {x y} {x y *} lambda :mul set
[]
stacker:1> 3 4 mul
[3 4 λxλy.{x y *}]
stacker:2> eval
[12]
stacker:3> 5 6 mul eval
[12 30]
```

裸の名前だけで呼びたいときは `defun` を使います。

### 高階関数に渡す

`map` などは、ブロックのかわりにラムダを受け取れます。

```
stacker:0> [1 2 3] {x} {x x *} lambda map
[[1 4 9]]
```

### 作った場所の変数を覚える

ラムダは、作られた時点の変数の環境を持ち歩きます。次の `adder` は、引数 `n` を足す関数を返します。`adder` から戻ったあとでも `n` は参照できます。

```
stacker:0> {n} {{x} {x n +} lambda} :adder defun
[]
stacker:1> 10 adder :add10 set
[]
stacker:2> 5 add10 eval
[15]
```

引数名は `defun` と同じく、重複しない裸の名前でなければなりません。

## alias

```
{本体} {名前} alias
```

コード片に名前を付けます。名前を書くと、本体がその場に書かれていたかのように、呼び出し側のスタックと変数の上で実行されます。引数の束縛はありません。

```
stacker:0> {2 ^ 3 * 5 +} {calculatePowerAndAdd} alias
[]
stacker:1> 5 calculatePowerAndAdd
[80]
```

本体が使う変数は、呼び出した場所の変数です。

```
stacker:0> {y 1 +} {incy} alias
[]
stacker:1> 3 :y set
[]
stacker:2> incy
[4]
```

名前は `{名前}` か `:名前` で書きます。

`alias` 自体も、Stacker で書かれた語です。インタプリタを起動するたびに自動で読み込まれる、Stacker で書かれた定義の集まりを prelude と呼びます。`alias` はその一つで、引数のない `defmacro` として定義されています。

## defmacro

```
{引数1 引数2 ...} {本体} :名前 defmacro
```

マクロは、引数を値ではなくコード（ブロックやシンボル）のまま受け取ります。本体は呼び出されるたびに「展開時」に一度実行され、実際に動かすコードを作ります。そのコードが、呼び出した場所のスタックの上で実行されます。新しい制御構文を Stacker 自身で書くのに使います。

### 例 unless

条件が偽のときだけ実行する `unless` です。

```
stacker:0> {cond body} { {cond eval not {body eval} if} } {unless} defmacro
[]
stacker:1> -3 {0 >} {"not positive" echo} unless
not positive
[]
```

`unless` の本体は `{cond eval not {body eval} if}` というブロックリテラル 1 つを残します。ブロックリテラルに含まれる `cond` と `body` が、呼び出し時に渡された引数に置き換わります。この置き換えを、パラメータ補間と呼びます。

### パラメータ補間

パラメータ補間は、本体のブロックリテラルをスタックに積む瞬間に行われます。ブロックの中のすべての深さで、展開時の変数に束縛された裸の名前が、その値で置き換わります。置き換わる名前は、マクロの引数と、本体で `=` や `set` により作った変数です。呼び出し側の変数は対象外です。置き換えは値の型で決まります。

| 束縛されている値 | 置き換わるもの |
|------------------|----------------|
| ブロック | そのブロック |
| 文字列 | 文字列リテラル |
| シンボル | 裸の名前 |
| それ以外（数など） | その値 |

置き換えたあとのコードは、もう一度は走査されません。本体に書いた `:名前`、文字列リテラル、リストリテラルは置き換えの対象外です。

### 本体が残す値

本体は専用のスタックと、引数を束縛した専用のスコープで実行され、値をちょうど 1 つ残さなければなりません。残した値がブロックなら呼び出し側で実行され、ブロック以外なら、その値がスタックに積まれます。本体の中での代入は、マクロの中だけで有効で、呼び出し側の変数は変わりません。

```
stacker:0> {n} {n 1 +} :inc defmacro
[]
stacker:1> 3 inc
[4]
```

値を 0 個または 2 個以上残すとエラーです。

```text
$ {} {1 2} :two defmacro
$ two
MacroExpansionError: Macro `two` must leave exactly one value as its expansion, but left 2.
```

### 引数は何回でも使われる

置き換えは、名前が現れた場所すべてに起こります。次の例では、引数のブロックが 2 回実行されます。

```
stacker:0> {x} {{x eval x eval *}} :sq defmacro
[]
stacker:1> {"eval" echo 3} sq
eval
eval
[9]
```

引数を 1 回だけ評価したいときは、`gensym` で作った名前に結果を入れます。`gensym` は、重複しない新しい名前（`__g` で始まるシンボル）を返します。この接頭辞は、自分の名前に使わないでください。

```
stacker:0> {x} { gensym :t = { x eval :t set t t + } } {double!} defmacro
[]
stacker:1> {3 4 +} double!
[14]
```

`gensym t =` は、新しい名前を展開時の変数 `t` に入れます。続くブロックリテラルの中の `t` は、その名前に置き換わります。生成されるコードの一時変数が毎回別の名前になるので、呼び出し側の変数とぶつかりません。

### macroexpand

`{名前} macroexpand` は、マクロを実行せずに、展開されたコードをスタックに積みます。引数はあらかじめスタックに積んでおきます。マクロの動作を調べるときに最も確実な方法です。

```
stacker:0> {cond body} { {cond eval not {body eval} if} } {unless} defmacro
[]
stacker:1> {0 >} {"neg" echo} {unless} macroexpand
[{{0 >} eval not {{"neg" echo} eval} if}]
```

`gensym` を使うマクロでは、生成された名前も見えます。名前は `__g` に通し番号を付けたもので、番号はそれまでに `gensym` が呼ばれた回数によって変わります。

```text
stacker> {x} { gensym :t = { x eval :t set t t + } } {double!} defmacro
[]
stacker> {3 4 +} {double!} macroexpand
[{{3 4 +} eval __g1 set __g1 __g1 +}]
```

## コードを組み立てる語

マクロの本体や、コードを値として扱うときに使う語です。

| 語 | 動作 |
|----|------|
| `concat-block` | 2 つのブロックを 1 つにつなぐ |
| `expand` | ブロックを、トークンごとの 1 トークンのブロックに分ける。リストなら要素をスタックに積む |
| `sub` | 一番上の値を、それ 1 つだけを含むブロックに包む |
| `subn` | 一番上の n 個の値を、1 つのブロックに包む |
| `read-from-string` | 文字列をコードのブロックに変換する |
| `eval` | ブロックやラムダを実行する |

```
stacker:0> {a b} {c} concat-block
[{a b c}]
```

```
stacker:0> {a b} expand
[{a} {b}]
```

`sub` と `subn` は、値をコードに埋め込むために使います。

```
stacker:0> :x sub
[{x}]
stacker:1> 3 sub
[{x} {3}]
stacker:2> 1 2 2 subn
[{x} {3} {1 2}]
```

`concat-block` と `sub` を使えば、`defmacro` の本体で補間を使わずにコードを組み立てられます。

```
stacker:0> {n} {n sub {2 *} concat-block} :times2 defmacro
[]
stacker:1> 3 times2
[6]
```

`3 times2` は `{3 2 *}` に展開されます。

`read-from-string` は文字列をコードに変えます。文字列に `eval` を直接使うことはできません。

```
stacker:0> "3 4 +" read-from-string
[{3 4 +}]
stacker:1> eval
[7]
stacker:2> "3 " "4 +" + read-from-string eval
[7 7]
```

```text
$ "hi" eval
StackerTypeError: `eval` expects a code block, a symbol or a lambda, got the string 'hi'. A string is text, not code: parse it first with `read-from-string`, e.g. "3 4 +" read-from-string eval
```

`eval` は、ブロックの中のコードを現在のスタックの上で実行します。ブロック以外の値（数など）に使うと、その値がそのまま残ります。

```
stacker:0> {1 2 +} eval
[3]
stacker:1> 5 eval
[3 5]
```

## 定義の一覧

`funcs`、`macros`、`vars` は、現在定義されている関数、マクロ、変数を表示します。prelude の定義には `(prelude)` が付きます。

```
stacker:0> {x} {x 2 *} :dbl defun
[]
stacker:1> funcs
mean: args=['xs'], body={xs sum xs len /} (prelude)
dbl: args=['x'], body={x 2 *}
[]
stacker:2> {2 *} {twice} alias
[]
stacker:3> macros
alias: {body name} {{{} {body} :name defmacro}} (prelude)
twice: {} {{2 *}}
[]
stacker:4> 1 :q set
[]
stacker:5> vars
e = 2.718281828459045
pi = 3.141592653589793
phi = 1.618033988749895
tau = 6.283185307179586
nan = nan
inf = inf
q = 1
[]
```

`alias` で付けた名前が `macros` に出ていることに注意してください。`alias` は引数なしのマクロとして定義されます。

制御構文は [制御構文](control.md) を参照してください。
