# スクリプトとファイルの取り込み

REPL で試したコードは、`.stk` ファイルに書いて保存すればそのまま実行できます。このページでは、スクリプトの書き方と実行方法、別ファイルを取り込む `include`、起動時に読み込まれる prelude、再帰の上限、スクリプトでエラーが起きたときの表示を説明します。

## スクリプトを書いて実行する

拡張子 `.stk` のファイルに式を書き、ファイル名を引数にして実行します。

```bash
stacker fact.stk
```

リポジトリを clone しただけでインストールしていない場合は、`python -m stacker fact.stk` で同じことができます。拡張子が `.stk` でないファイル、存在しないファイルを指定すると `ScriptReadError` で終了します。

`fact.stk` の例です。

```stk
# 階乗
{n} {
  n 1 <=
  {1}
  {n n 1 - fact *}
  ifelse
} :fact defun

#|
ブロックコメントは
複数行にわたってよい
|#
5 fact echo   # 行末コメント
[1 2 3
 4 5] sum echo
```

実行結果です。

```text
120
15
```

スクリプトの実行では、REPL と違って終了時のスタックは表示されません。結果を見たい値は `echo` で出力してください。スタックは行をまたいで引き継がれるので、`1 2` の次の行に `+ echo` と書いても動きます。

### コメント

- `#` から行末まで: 行コメント。式のあとに書けます。
- `#|` から `|#` まで: ブロックコメント。複数行にわたってよく、式の途中にも置けます。

### 複数行にまたがる式

スクリプトは、上から順に「閉じていない括弧や文字列がない」ところまでを 1 つの式としてまとめ、その式を評価します。つまり、改行で式が終わるのが基本で、次のものが閉じていないあいだだけ式が次の行へ続きます。

- `{` ... `}`（コードブロック）
- `[` ... `]`（リスト）
- `"` ... `"` や `"""` ... `"""`（文字列。改行は文字列の一部になります）
- `#|` ... `|#`（ブロックコメント）

上の `fact.stk` では、`{n} {` から `} :fact defun` までが 1 つの式、`[1 2 3` から `4 5] sum echo` までがもう 1 つの式です。

`do`・`dolist`・`times` の本体も、ブロックが閉じるまで次の行へ続けて書けます。

```stk
1 3 :i {
  i echo
} do
```

スタックは行をまたいで引き継がれるので、引数を前の行で積んでおくこともできます。

```stk
1 3 :i
{ i echo } do
```

## 別のファイルを取り込む: include

`"ファイル名" include` で、別の `.stk` ファイルを読み込みます。取り込んだファイルは、取り込んだ側のインタプリタの、`include` を書いた場所のスコープで評価されます。ファイルの中身をその場に書いたのと同じで、ファイルで定義した変数・関数・マクロが、取り込んだ側でそのまま使えます。同じファイルを一度だけ読みたいときは `require` を使います（後述）。

次の 3 つのファイルを考えます。

```text
project/
├── main.stk
└── lib/
    ├── geometry.stk
    └── helpers.stk
```

`main.stk`:

```stk
"lib/geometry.stk" include
3 area echo
tau echo
```

`lib/geometry.stk`:

```stk
"helpers.stk" include
6.28 :tau =
{r} {r square r *} :area defun
```

`lib/helpers.stk`:

```stk
{x} {x x *} :square defun
```

```bash
cd project
stacker main.stk
```

```text
27
6.28
```

`geometry.stk` が取り込んでいる `helpers.stk` は、`lib/` の下にあります。入れ子の `include` では、取り込む側のファイルがあるディレクトリが基準になるので、`main.stk` からどのディレクトリで実行しても `"helpers.stk"` と書けば見つかります。

### 探索の順序

相対パスは、次の順に探し、最初に見つかったファイルを使います。

1. `include` を書いたファイルがあるディレクトリ
2. カレントディレクトリ（実行したときのディレクトリ）

絶対パスはそのまま使われます。REPL と `-e` にはファイルの位置がないので、カレントディレクトリだけが探されます。ファイル名の拡張子は `.stk` でなければなりません。

スクリプトや取り込んだファイルが終わったときにスタックに値が残っていると、標準エラーに `WARNING:stacker:1 value left on the stack at the end of main.stk: 3` のように知らせます（引数を 1 つ多く積んだ、結果を使い忘れた、という間違いの印です。REPL と `-e` では出ません）。組み込みの語と同じ名前のグローバル変数を作ったときも、`defun` と同じ警告が出ます。`defun` や `defmacro` が、別のファイルで定義した自分の語を定義し直したときは、`redefining word '__call' (defined at parser.stk:62) at interp.stk:84` のように両方の場所を知らせます（同じファイルの中での定義し直しには出ません）。

モジュールの末尾に、コマンドラインから実行されたときだけ動くクライアントを書くには `main?` を使います（`main? {args 0 at int run} if`）。`require` で取り込まれたときは偽になります。

実行中のファイルの位置は語 `script-path`（絶対パス）と `script-dir`（そのディレクトリ）で読めます。取り込まれたファイルの中ではそのファイル自身、REPL と `-e` では `null` です。`read-lines` などのファイルの語の相対パスはカレントディレクトリ基準なので、スクリプトの隣のデータを読むときは `script-dir` から組み立てます（`script-dir "data.txt" path-join read-lines`）。

同じ名前のファイルが両方にあるときは、1 の取り込む側のディレクトリが優先されます。

### 取り込まれるもの

取り込んだファイルは、取り込んだ側と同じインタプリタで評価されます。

- 変数は 1 つです。ファイルの関数が更新する変数と、取り込んだ側が読む変数は同じものです。ファイルのトップレベルの `set` も関数の中の `set` も、取り込んだ側に同じ名前の変数があればそれを書き換えます（名前は共有されます）。
- ファイルの関数は、取り込んだ側や、先に取り込んだ別のファイルが定義した関数を呼べます。ファイルは、取り込む時点で定義済みの変数・関数・マクロ・プラグインの語を使えます。
- 取り込むたびに評価されます。`0 :counter set` のように状態を作るファイルは、2 回目の `include` で状態を作り直します。状態を持つライブラリは `require` で読んでください。
- ファイルは空のスタックで始まり、取り込んだ側のスタックの値は見えません。ファイルが最後に残した値は捨てられ、`depth` は `include` の前後で変わりません。
- 関数の中で取り込むと、ファイルが作った変数はその呼び出しの中だけで使えます。関数・マクロはどこで定義しても全体から使えます。
- ファイルの途中でエラーになると、そこまでに定義したものは残ります。

### 一度だけ読む: require

`"ファイル名" require` は、そのファイルをこのインタプリタでまだ読んでいなければ `include` と同じように評価し、すでに読んでいれば何もしません。

```stk
# lib/counter.stk
0 :counter set
{} {counter 1 + :counter set counter} :tick defun
```

```stk
# a.stk
"lib/counter.stk" require
{} {tick drop} :bump defun
```

```stk
# main.stk
"lib/counter.stk" require
tick drop            # counter = 1
"a.stk" require      # a.stk は初めてなので評価される。その中の counter.stk の require は何もしない
bump                 # counter = 2
tick echo            # 3
```

同じものをすべて `include` で書くと、`a.stk` の中の `include` が `0 :counter set` をもう一度走らせるので、最後の `tick echo` は `2` になります。

- 読んだ記録はインタプリタごとです。`"lib.stk"`、`"./lib.stk"`、絶対パスのように書き方が違っても、同じファイルなら 1 回だけ評価されます。
- `include` で最後まで評価したファイルも「読んだ」ことになり、そのあとの `require` は何もしません。逆に `require` のあとの `include` は評価します。
- 途中でエラーになったファイルは記録されません。直してもう一度 `require` すると評価されます。
- ファイルを直しても `require` は読み直しません。REPL で読み直すときは `include` を使ってください。
- `require` は、どこに書いてもトップレベルに書いたのと同じで、ファイルが作った変数は全体から見えます。

### エラー

次の場合は `IncludeError` になります。

- ファイルが見つからない。メッセージに、探したパスがすべて載ります。
- 拡張子が `.stk` ではない（`File x.txt is not a stacker script.`）。
- ファイルが循環して取り込まれている（`a.stk` が `b.stk` を、`b.stk` が `a.stk` を取り込むなど。`Circular include detected: b.stk`）。実行中のスクリプト自身を取り込むのも循環です。`require` も同じです。

取り込んだファイルの中で起きたエラーについては、後述の「エラーの表示」を参照してください。

## prelude

Stacker は起動するたびに、Stacker 自身のコードで書かれた定義を読み込みます。これを prelude と呼びます。`include` を書かなくても、次の語が最初から使えます。

| 語 | 内容 |
|---|---|
| `alias` | コードに名前を付ける。`{dup *} {sq} alias` と書くと、`sq` が `dup *` として働く |
| `mean` | 数のリストの平均 |

```
stacker:0> {dup *} {sq} alias
[]
stacker:1> 5 sq
[25]
stacker:2> [1 2 3 4] mean
[25 2.5]
```

`alias` の詳しい使い方は[関数・ラムダ・マクロ](functions-and-macros.md)、すべての語の一覧は[演算子リファレンス](operators.md)にあります。

prelude の語は、自分のスクリプトで同じ名前を定義し直せます。そのときは `redefining prelude word 'mean'` という警告が表示されます。取り込んだファイルは同じインタプリタで評価されるので、取り込んだファイルが prelude の語を再定義すると、取り込んだ側でもその定義になります。取り込む前に再定義した語は、取り込んだファイルの中でもその定義です。

Python から使うときは `Stacker(prelude=False)` で prelude を読み込まないようにできます。詳しくは[プラグインと Python からの利用](plugins-and-python-api.md)を参照してください。

## 再帰の上限

自分自身を呼ぶ関数が止まらなくなったときに備えて、Stacker は関数やマクロの呼び出しが入れ子になる深さを制限しています。上限を超えると `StackerRecursionError` で止まります。

| 項目 | 値 |
|---|---|
| 既定の上限 | 1500 |
| 指定できる最大値 | 1800 |

上限は `--recursion-limit` で変えられます。1 から 1800 の整数だけが指定でき、範囲外の値は起動時にエラーになります。

```bash
stacker --recursion-limit 1800 deep.stk
```

数えているのは、実行中の関数呼び出し（入れ子の深さ）です。呼び出しが終わった関数は数えません。上限が 1500 のとき、深さ 1500 までは動き、1501 段目の呼び出しで止まります。

止まったときの表示です（`{n} {n f} :f defun` のあとに `3 f` を実行した場合）。

```text
/home/user/project/loop.stk:2: error: Maximum recursion depth (1500) exceeded in function `f`
  [StackerRecursionError]
  | 
2 | 3 f
```

深い再帰が必要なときは `--recursion-limit` で上限を上げるか、`loop`・`times` などの繰り返しに書き換えてください。

## エラーの表示

スクリプトの実行中にエラーが起きると、その式で実行を止め、標準エラー出力に次の形式で表示して、終了ステータス 1 で終わります。エラーより前の式の出力は、そのまま残ります。

`errors.stk`:

```stk
1 2 +
echo
10 total +
```

```bash
stacker errors.stk
```

```text
3
/home/user/project/errors.stk:3: error: `total` is not defined.
  [UndefinedSymbolError]
  | 
3 | 10 total +
hint: To use the name itself, write `:total` or `{total}`
```

最初の `3` は `1 2 + echo` の出力です。残りがエラーの表示で、上から次の内容です。

1. `ファイルの絶対パス:行番号: error: メッセージ`
2. `[エラーの種類]`（例外クラスの名前）
3. エラーが起きた式の行番号と、その行のソース
4. `hint:` 対処のヒント（エラーの種類によっては付きません）

知っておくと便利な点です。

- 列の位置は表示されません。どの語でエラーになったかは、メッセージ（上の例では `` `total` ``）から読み取ります。
- 式が複数行にわたるときは、その式の最初の行が表示されます。たとえば `1 3 :i {` で始まる `do` のブロックの途中で起きたエラーは、`do` を書いた最初の行を指します。
- `include` / `require` したファイルの中で起きたエラーは、そのファイルと行で表示され、その下に取り込んだ側のファイルと行が `included from` として、取り込みの段ごとに 1 行ずつ付きます。`main.stk` の 1 行目が `lib/geometry.stk` を取り込み、その 1 行目が `helpers.stk` を取り込み、`helpers.stk` の 2 行目でエラーになると次のようになります。

  ```text
  /home/user/project/lib/helpers.stk:2: error: `total` is not defined.
    [UndefinedSymbolError]
    | 
  2 | 10 total +
    included from /home/user/project/lib/geometry.stk:1
    included from /home/user/project/main.stk:1
  hint: To use the name itself, write `:total` or `{total}`
  ```

  REPL や `-e` から取り込んだときは、入口には行がないので、その段の `included from` は付きません。
- 閉じていない文字列や括弧は、`Unterminated string starting at line 2` のように、開始した行を示すメッセージになります。
- `-e` で渡した式のエラーも、同じ形式で標準エラー出力に表示されます。ファイルがないので 1 行目は `stacker: error: メッセージ` になり、ソース行は表示されません。

### --debug

`--debug` を付けると、上の表示のあとに Python のトレースバックが続き、起動時のプラグイン読み込みなどのデバッグログも出ます。Stacker 自体の不具合を調べるとき以外は、通常は不要です。

```bash
stacker --debug errors.stk
```

オプションの一覧は[REPL とコマンドライン](repl-and-cli.md)を参照してください。
