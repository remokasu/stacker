# 名前とシンボル

変数・関数・マクロには名前が付きます。Stacker では、名前を **値として参照する** のか、**名前そのものを指す** のかを書き分けます。このページでは、その書き分け（裸名、`:x`、`{x}`）、名前を表す型 Symbol、変数の束縛とスコープを説明します。数値・文字列・ブロックなどの基本的な書き方は [構文と値](syntax.md) を参照してください。

## 名前の 3 つの書き方

名前 `x` は 3 通りに書けます。

| 書き方 | 意味 |
| --- | --- |
| `x`（裸名） | 参照。`x` が表すものを使う |
| `:x` | シンボル。名前 `x` そのものを値としてスタックに積む |
| `{x}` | 名前 `x` だけを入れたブロック。「名前そのもの」を表す書き方 |

### 裸名は参照

裸名を書くと、その名前が次の順に調べられます。

1. マクロなら、展開される
2. 変数なら、その値がスタックに積まれる
3. 関数や演算子なら、実行される

どれでもない名前は、書かれた位置でエラーになります（[未定義の名前](#未定義の名前)）。

```
stacker:0> 3 :x set
stacker:1> x
[3]
stacker:2> x 2 *
[3 6]
```

### `:x` と `{x}` は名前そのもの

`:x` は、`x` という変数があるかどうかや、その値に関係なく、名前 `x` を表す値（**シンボル**）を積みます。

```
stacker:0> 3 :x set
stacker:1> :x
[x]
stacker:2> x
[x 3]
```

`{x}` は、名前 1 つだけを含むブロックです。名前を受け取る場所（`set` の名前など）では `:x` と同じく名前として扱われます。コードとして実行したときも `:x` と同じ意味になり、`:x eval` も `{x} eval` も、`x` と書いたときと同じ結果になります（変数 `x` の値が積まれます）。`{x}` のように名前 1 つだけのブロックを **quote 済みシンボル** と呼ぶことがあります。

```
stacker:0> 5 :x set
stacker:1> :x eval
[5]
stacker:2> {x} eval
[5 5]
```

文字列 `"x"` は名前になりません。文字列を名前に変える方法は次の節で説明します。

`:` の後ろには名前が必要です。`:1` のような書き方はエラーになります。

## Symbol 型

`:x` が作る値は **Symbol** という独立した型で、スタックには裸の `x` と表示されます。文字列 `'x'` とは別の値です。

```
stacker:0> :x
[x]
stacker:1> :x symbol?
[x true]
stacker:2> "x" str?
[x true true]
```

Symbol に関する語は次の 3 つです。

- `symbol?` は、値が Symbol なら `true` を返します。文字列や、変数の値は Symbol ではありません
- `str` は、Symbol の名前を文字列にします
- `symbol` は、文字列を Symbol にします

```
stacker:0> :x str
['x']
stacker:1> "x" symbol
['x' x]
```

Symbol と文字列は **等しくなりません**。

```
stacker:0> :x "x" ==
[false]
stacker:1> "x" symbol :x ==
[false true]
```

文字列で名前を組み立てたいときは、`symbol` で Symbol にします。たとえば `"x" symbol` は `:x` と同じ値です。文字列のまま `set` に渡しても名前にならず、エラーです。

```text
5 "x" set
StackerSyntaxError: `set` expects a name, got the string 'x'. Write :x or {x}, or convert a string with `symbol`.
```

```
stacker:0> 5 "x" symbol set
stacker:1> x
[5]
```

`:x` はリストの要素にも書けます。`[:a :b]` は名前のリストです。

```
stacker:0> [:a :b]
[[a b]]
```

## 名前を受け取る語には `:name` を渡す

Stacker はトークンを左から右へ 1 つずつ読み、後ろのトークンを見ることはありません。だから裸名は、**どこに書いても参照**です。`set` の直前でも例外ではありません。名前を受け取る語には、名前そのものを `:name`（または `{name}`）で渡します。

| 語 | 書き方 |
| --- | --- |
| `set`、`=`、`global` | `3 :x set`、`5 :y =`、`42 :answer global` |
| `defun`、`defmacro`、`macroexpand` | `{a} {a 1 +} :inc defun`、`:inc macroexpand` |
| `do` / `dolist` のループ変数 | `0 10 :i {i echo} do`、`[1 2 3] :x {x echo} dolist` |
| `reduce` / `fold` のブロックの前にある 2 つの名前 | `[1 2 3] 0 :acc :x {acc x +} reduce` |
| `alias`、マクロの引数 | `{2 *} :double alias`、`:n incr!` |

裸名で `3 x set` と書くと、`x` の参照が先に評価されます。`x` が未定義なら、その場で止まります。

```text
3 x set
UndefinedSymbolError: `x` is not defined.
hint: To use the name itself, write `:x` or `{x}`
```

`x` が定義済みなら、その値が積まれて `set` に渡り、`set` は名前の代わりに値を受け取ってエラーになります。

```text
5 :x set 7 x set
StackerSyntaxError: `set` expects a name, got 5. A bare name pushes what it refers to; write the name itself as `:name` or `{name}`.
```

ただし、`x` が名前（Symbol や `{y}`）を持っているときは、その名前が `set` に渡り、**その名前に束縛されます**（間接束縛）。名前を変数で受け渡すときの書き方です。

```
stacker:0> 1 :y :x set
[1]
stacker:1> 7 x set
[1]
stacker:1> y
[1 7]
stacker:2> x
[1 7 y]
```

```
stacker:0> 3 :x set
stacker:1> 5 :y =
stacker:2> 0 3 :i {i echo} do
0
1
2
3
[]
```

```
stacker:0> [1 2 3] :x {x echo} dolist
1
2
3
[]
stacker:1> [1 2 3] 0 :acc :x {acc x +} reduce
[6]
```

`reduce` の例では、`:acc`（途中の結果）と `:x`（各要素）が、本体の中で使う 2 つの名前です。

マクロに変数の名前を渡すときも同じで、`:n` か `{n}` と書くと名前 `n` が渡り、裸の `n` と書くと `n` の現在の値が渡ります。詳しくは [関数・ラムダ・マクロ](functions-and-macros.md) を参照してください。

なお、リテラルと文字列は名前になりません。`5 3 set`、`5 true set`、`5 "x" set` はいずれもエラーです。

## 変数

### 束縛: set、=、global

`値 名前 set` で変数に値を束縛します。`=` は `set` と同じです。

```
stacker:0> 3 :x set
stacker:1> 5 :y =
stacker:2> x y +
[8]
```

同じ名前に再度束縛すると、値が置き換わります。

```
stacker:0> 5 :x set
stacker:1> 7 :x set
stacker:2> x
[7]
```

### スコープ

トップレベルで `set` した変数は、以後どこからでも参照できます。関数の中では次のように扱われます。

- 関数の引数と、関数の中で新しく `set` した変数は、その関数の中だけで使える（ローカル）
- すでに外側に同じ名前の変数があるときは、関数の中の `set` が外側の変数を書き換える
- `global` で束縛した変数は、関数の中で束縛しても、関数の外から参照できる

```
stacker:0> {a} {5 :tmp set} :f defun
stacker:1> 1 f
stacker:2> {a} {7 :total global} :g defun
stacker:3> 1 g
stacker:4> total
[7]
```

`f` の中で束縛した `tmp` は、`f` の外では参照できません。`g` の中で `global` した `total` は参照できます。

```text
{a} {5 :tmp set} :f defun
1 f
tmp
UndefinedSymbolError: `tmp` is not defined.
```

`do` / `dolist` のループ変数も、ループの外では参照できません。

関数の定義そのものは [関数・ラムダ・マクロ](functions-and-macros.md)、ループは [制御構文](control.md) を参照してください。

### 未定義の名前

束縛されていない名前を参照すると、**参照が書かれた位置で** エラーになります。後続の処理に進まないので、タイプミスは書いた場所で止まります。スタックには、エラーの前までの結果が残ります。

```text
1 zzz 2
UndefinedSymbolError: `zzz` is not defined.
```

この例ではスタックに `1` が残り、`2` は積まれません。関数の本体は、定義時ではなく **呼び出したとき** に評価されるので、本体の中の未定義名は呼び出し時にエラーになります。

## 組み込みの語も同じ規則で束縛する

`dup` や `+` のような組み込みの演算子も、裸で書けば実行されるだけです。`3 dup set` では `dup` が実行されて `3 3` になり、その上で `set` が名前の代わりに `3` を受け取ってエラーになります。

```text
3 dup set
StackerSyntaxError: `set` expects a name, got 3. A bare name pushes what it refers to; write the name itself as `:name` or `{name}`.
```

組み込みの語を束縛するときも、他の名前と同じく `:name` か `{name}` と書きます。特別な保護はありません。

```
stacker:0> 3 :dup set
stacker:1> dup
[3]
stacker:2> 3 {dup} set
```

変数・関数・マクロの名前は、同じ書き方で何度でも再定義できます。ループ変数や `reduce` の変数には、組み込みの語と同じ名前（`:e`、`:dup` など）も使えます。

`alias` のように、起動時に Stacker 自身が用意している語（prelude の語）を再定義すると、警告が出ます。

```text
{1} :alias set
redefining prelude word 'alias'
```

## ブロックを束縛すると評価せずに保存される

`set` や `defun` の値としてブロックを渡すと、ブロックは **評価されずにそのまま** 変数に保存されます。変数を参照すると、ブロックがスタックに積まれます。実行するには `eval` を使います。

```
stacker:0> 3 :x set
stacker:1> {x 1 +} :y set
stacker:2> y
[{x 1 +}]
stacker:3> eval
[4]
```

保存されたブロックは、`eval` したときの変数の値で評価されます（`y` の中の `x` は、`y` を実行する時点の値が使われます）。

```
stacker:0> 3 :x set
stacker:1> {x 1 +} :y set
stacker:2> 10 :x set
stacker:3> y eval
[11]
```

関数の引数に渡したブロックも、同じように評価されずに受け取られます。引数に対して `eval` を呼ぶと実行されます。

```
stacker:0> {n} {n eval 1 +} :f defun
stacker:1> {3 4 +} f
[8]
```

関数として呼べる値が欲しいときは `lambda` を使います（[関数・ラムダ・マクロ](functions-and-macros.md)）。
