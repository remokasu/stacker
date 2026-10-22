# 制御構文

条件分岐、ループ、エラー処理の書き方をまとめます。どれも特別な構文ではなく、ブロック（`{...}`）を受け取る演算子です。ブロックは「あとで実行するコード」で、実行するかどうか、何回実行するかを各演算子が決めます。ブロックの基本は [構文と値](syntax.md) を参照してください。

## 条件の真偽

`if` などは、条件の値が真か偽かで動作を決めます。偽になる値は次のものだけで、それ以外はすべて真です。

| 値 | 判定 |
|----|------|
| `false` | 偽 |
| `0`、`0.0`、`0+0j`（数値のゼロ） | 偽 |
| `null` | 偽 |
| `[]`（空のリスト） | 偽 |
| `""`（空の文字列） | 偽 |
| `true`、`1`、`-1` など、ゼロでない数 | 真 |
| `[0]` のように要素のあるリスト | 真 |
| `"a"`、`"false"` のように空でない文字列 | 真 |
| `:x` のようなシンボル | 真 |

文字列 `"false"` は空でないので真です。

```
stacker:0> 0 {"真" echo} {"偽" echo} ifelse
偽
[]
stacker:1> [] {"真" echo} {"偽" echo} ifelse
偽
[]
stacker:2> "false" {"真" echo} {"偽" echo} ifelse
真
[]
stacker:3> :x {"真" echo} {"偽" echo} ifelse
真
[]
```

条件の位置にブロックを書くと、そのブロックが **今のスタックの上で** 実行され、そのあとスタックの一番上にある値が条件になります。ブロック以外の値は、その値自身が条件です。

```
stacker:0> 5 :x set
[]
stacker:1> x 0 > {"正" echo} if
正
[]
stacker:2> {x 0 >} {"正" echo} if
正
[]
```

条件ブロックは、スタックからスタックへの関数です。下にある値を使って（消費して）よく、何も書かない `{}` は何もしない関数なので、そのときスタックの一番上にあった値がそのまま条件になります。ブロックを実行したあとスタックが空なら、判定する値がないのでエラーです。

```
stacker:0> 7 {} {"真" echo} if
真
[]
```

```text
{} {1} if
NoValueProducedError: The condition block of `if` left nothing on the stack to test.
```

条件の位置に置いた文字列やシンボルは、変数としては参照されません。シンボルは常に真、文字列は空でなければ真です。変数の値で判定したいときは、裸の名前（`x`）を書きます。

## if と ifelse

`if` は条件が真のときだけブロックを実行します。

```
stacker:0> 1 {2} if
[2]
stacker:1> 0 {3} if
[2]
```

`ifelse` は真のときと偽のときで別のブロックを実行します。条件、真ブロック、偽ブロックの順に書きます。

```
stacker:0> -2 {"負" echo} {"0 以上" echo} ifelse
負
[]
```

選ばれたブロックは、呼び出し側のスタックと変数をそのまま使います。結果を値として残すこともできます。

```
stacker:0> 7 :n set
[]
stacker:1> n 5 > {"大"} {"小"} ifelse
['大']
```

## cond

`cond` は、条件とその結果のブロックを対にして並べ、最初に真になった対の結果だけを実行します。末尾に対の個数を書きます。

```
{条件1} {結果1} {条件2} {結果2} 2 cond
```

条件のブロックはスタックの上で実行され、一番上の値を取り出して判定します。`==` などは比較した値を消費するので、あとの結果ブロックでも値を使いたいときは `dup` で複製します。

```
stacker:0> 5 {dup 1 ==} {"one"} {dup 5 ==} {"five"} 2 cond
[5 'five']
```

どの条件にも当てはまらなかったときのために、最後の条件を `{true}` にして「それ以外」を書けます。

```
stacker:0> 9 {dup 1 ==} {"one"} {true} {"other"} 2 cond
[9 'other']
```

## iferror

`iferror` は、最初のブロックを実行し、エラーが起きたら 2 つ目のブロックを実行します。他の言語の try / catch に相当します。

```
{try} {catch} iferror
```

```
stacker:0> {1 0 /} {"ゼロ除算" echo} iferror
ゼロ除算
[]
stacker:1> {1 2 +} {"エラー" echo} iferror
[3]
```

catch ブロックにはエラーの内容は渡されません。try ブロックが途中までに行ったスタック操作は戻りません。次の例では、`/` が `3` と `0` を取り出した時点でエラーになるので、`1 2` だけが残ります。

```
stacker:0> 1 2 {3 0 /} {"エラー" echo} iferror
エラー
[1 2]
```

try ブロックの中で `break` を使うと、catch は実行されず、囲んでいるループが抜けます（次節）。

## throw と try

`throw` は自分でエラーを起こします。種類（文字列かシンボル）とメッセージを取ります。種類は、組み込みのエラーがクラス名を出す場所に表示されます。

```
"IllegalArgumentException" "row 5 is outside 0..4" throw
```

```
stacker: error: row 5 is outside 0..4
  [IllegalArgumentException]
```

`try` は `iferror` と同じようにエラーを捕まえますが、handler を実行する前に**エラーを辞書としてスタックに積みます**。キーは文字列の `"kind"`（`throw` の種類。組み込みのエラーならクラス名）と `"message"` です。

```
{try} {handler} try
```

```
stacker:0> {"E" "boom" throw} {:e set e "kind" get e "message" get} try
['E' 'boom']
stacker:1> {1 0 /} {"kind" get} try
['E' 'boom' 'ZeroDivisionError']
stacker:2> {1 2 +} {drop "never" echo} try
['E' 'boom' 'ZeroDivisionError' 3]
```

`if` / `ifelse` / `iferror` / `try` / `times` / `cond` のブロックの位置にラムダやシンボルを書くと、`eval` と同じように実行されます（ラムダは引数をスタックから取り、シンボルはその名前を実行）。数や文字列などの値はそのまま積まれるので、`true 1 2 ifelse` は値を選びます。シンボルそのものを選びたいときは `true {:a} {:b} ifelse` と書きます。

handler はラムダでも書けます。エラーの辞書がスタックにあるので、引数を 1 つ取るラムダがそれを受け取ります（`{try} {e} {e "kind" get echo} lambda try`）。`if` や `times` などブロックを実行する語はどれも、ラムダとシンボルを `eval` と同じように実行します。

エラーをそのまま投げ直すには、辞書の 2 つの値で `throw` します（`e "kind" get e "message" get throw`）。`iferror` と同じく、スタックは戻りませんし、`break` と `exit` は捕まえません。

## ループ

### do

数の範囲を順に回します。

```
開始 終了 :変数 {本体} do
```

終了値を含みます。変数の名前は、そのまま（裸の名前）で書きます。ループの外では参照できません。

```
stacker:0> 1 3 :i {i echo} do
1
2
3
[]
stacker:1> 1 3 :i {i} do
[1 2 3]
```

開始が終了より大きいと、本体は一度も実行されません。

```
stacker:0> 3 1 :i {i echo} do
[]
```

### dolist

リストの要素を順に回します。

```
リスト :変数 {本体} dolist
```

```
stacker:0> [10 20 30] :x {x echo} dolist
10
20
30
[]
```

空のリストでは何も実行されません。

### times

ブロックを決まった回数だけ実行します。ブロックが先、回数があとです。

```
stacker:0> {"hi" echo} 3 times
hi
hi
hi
[]
```

回数が 0 なら実行されません。

### while

条件ブロックを実行して真の間、本体を繰り返します。条件は本体の前に毎回評価されます。

```
{条件} {本体} while
```

```
stacker:0> 3 :n set
[]
stacker:1> {n 0 >} {n echo n 1 - :n set} while
3
2
1
[]
```

### loop

`break` が呼ばれるまで、ブロックを繰り返します。

```
stacker:0> 0 :n set
[]
stacker:1> {n 1 + :n set n 3 == {break} if} loop
[]
stacker:2> n
[3]
```

### break

`break` は、いちばん内側のループ（`do`、`dolist`、`times`、`while`、`loop`）を抜けます。`if` の中で呼んでも、実行中のブロックはその場で終わります。次の例では、`i` が 3 になった時点で `echo` は実行されずにループが終わります。

```
stacker:0> 1 5 :i {i 3 == {break} if i echo} do
1
2
[]
```

入れ子のループでは、内側のループだけが終わります。次の例では、内側が `j` が 2 の回で終わり、外側は 3 回とも回るので、`n` は 6 になります。

```
stacker:0> 0 :n set
[]
stacker:1> 1 3 :i {1 3 :j {n 1 + :n set j 2 == {break} if} do} do
[]
stacker:2> n
[6]
```

関数の中の `break` は、その関数を呼んだループを抜けます。どのループの中でもないところで `break` を実行すると、エラーになります。

```text
stacker> break
stacker: error: `break` can only be used inside a loop
  [StackerSyntaxError]
```

## map・filter・reduce とループの使い分け

`map`、`filter`、`reduce`（`fold` も同じ）に渡すブロックは、スタックに値をちょうど 1 つ残さなければなりません。`map` と `filter` はブロックの実行前にスタックへ要素を積み、ブロックが残した値を結果に使います。ブロックは呼び出し側の変数をそのまま使うので、ブロックの中の `set` はループのあとも残ります。

```
stacker:0> [1 2 3] {2 *} map
[[2 4 6]]
stacker:0> [1 2 3 4] {2 % 0 ==} filter
[[2 4]]
```

`reduce` は、初期値、累積用の名前、要素用の名前をブロックの前に書きます。

```
stacker:0> [1 2 3] 0 :acc :x {acc x +} reduce
[6]
```

`dolist` は配列も回せます。回るのは始めた時点の要素で、本体で配列を書き換えても回数は変わりません。辞書は列ではないので、`d keys :k {...} dolist` のようにキーを回します（[配列と辞書](arrays-and-dicts.md)）。

値を残さず、表示などの副作用だけが目的のときは `dolist` を使います。`map` に `echo` のように値を残さないブロックを渡すと、エラーになります。

```text
$ [1 2 3] {echo} map
NoValueProducedError: The block passed to `map` must leave a value on the stack. Use `dolist` for side-effect-only iteration.
```

2 つ以上残してもエラーになります。要素ごとに複数の値がほしいときは、`listn` で 1 つにまとめます。

```text
$ [1 2 3] {dup} map
ResultCountError: `map` needs one value from the block for each element, but it left 2
```

```
stacker:0> [1 2 3] {dup 2 listn} map
[[[1 1] [2 2] [3 3]]]
```

```
stacker:0> [1 2 3] :x {x echo} dolist
1
2
3
[]
```

関数やマクロの定義は [関数・ラムダ・マクロ](functions-and-macros.md) を参照してください。
