# REPL とコマンドライン

## コマンドライン

```text
stacker [-h] [--addplugin path] [--debug] [-e E] [--recursion-limit N] [script]
```

`stacker` の代わりに `python -m stacker` でも同じオプションを使えます。

| オプション | 説明 |
| --- | --- |
| `script` | 実行する `.stk` ファイル。指定すると、REPL を開かずにファイルを実行して終了します。 |
| `-e E` | 式 `E` を実行して終了します。 |
| `--debug` | デバッグモード。ログを DEBUG レベルで出力し、REPL ではエラー時に評価の経過と Python のトレースバックも表示します。 |
| `--recursion-limit N` | ユーザー定義関数の再帰の深さの上限。1 から 1800 までで、省略時は 1500 です。範囲外の値はエラーになります。 |
| `--addplugin path` | プラグインのファイルを Stacker のインストール先のプラグインディレクトリにコピーして終了します。 |
| `-h`, `--help` | ヘルプを表示して終了します。 |

`script` も `-e` も指定しなければ REPL が始まります。`-e` と `script` を同時に指定すると、`-e` だけが実行されます。

どちらの実行方法でも、実行時エラーが起きると、エラーメッセージを表示して終了コード 1 で終了します。スクリプトの場合はファイル名と行番号が付きます。

```bash
stacker script.stk
stacker -e "3 4 + echo"
stacker --recursion-limit 3000 script.stk
stacker --addplugin my_plugin.py
```

`--recursion-limit` に 1800 を超える値を渡すと、実行せずに終了コード 2 で終了します。上限に達した再帰は `StackerRecursionError` で止まります。

```text
$ stacker --recursion-limit 50 -e "{n} {n 0 == {0} {n 1 - f} ifelse} :f defun 100 f echo"
StackerRecursionError: Maximum recursion depth (50) exceeded in function `f`
```

`script` と `-e` はスタックの内容を表示しません。結果は `echo` で出力します。

プラグインは、起動のたびに Stacker のインストール先の `plugins` ディレクトリと、カレントディレクトリの `plugins` ディレクトリから読み込まれます。書き方は[プラグインと Python からの利用](plugins-and-python-api.md)を参照してください。

## REPL の操作

### プロンプト

```text
Stacker X.Y.Z on linux
Type "help" to get more information.
stacker:0>
```

プロンプトの `stacker:N>` の `N` は、入力前のスタックにある値の個数です。式を実行するたびに、結果のスタックが `[ ]` で表示されます。

```
stacker:0> 1 2 3
[1 2 3]
stacker:3> +
[1 5]
stacker:2> clear
[]
```

`clear` はスタックを空にするので、プロンプトの番号が 0 に戻ります。

### 終了

`exit` を入力するか、Ctrl+D を押します。Ctrl+D のときは `See you!` と表示して終了します。

### 複数行入力

ブロック `{ }`、リスト `[ ]`、文字列、ブロックコメント `#| |#` が閉じていない間は、REPL が次の行を待ちます。続きの行のプロンプトは `>` だけになります。

```text
stacker> {1
       > 3
       > +}
[{1 3 +}]
stacker> [1 2
       > 3 4]
[{1 3 +} [[1 2] [3 4]]]
```

リストを複数行で書くと、行ごとに区切られた行列になります（`[1 2; 3 4]` と同じです）。リストの続きの入力中に `end` と入力すると入力を打ち切りますが、閉じていないリストとしてエラーになります。

### 履歴と補完

入力した式はホームディレクトリの `~/.stacker_history` に保存され、次回の起動でも上下キーで呼び出せます。Tab キーで、演算子、変数、関数、マクロ、REPL 専用コマンドの名前を補完できます。

### エラー

エラーが起きても REPL は終了しません。エラーの種類と原因を表示し、可能なら対処のヒントを付けます。エラーになった式より前のスタックはそのまま残ります。

```text
stacker> 1 0 /
stacker: error: division by zero
  [ZeroDivisionError]
hint: Cannot divide by zero
```

## REPL 専用コマンド

次のコマンドは REPL だけで使えます。行全体がコマンド名だけのときに限り、REPL が処理します。他の式と同じ行には書けません。大文字と小文字は区別されません。スタックには影響しません。

```text
help                     使い方と、すべての演算子の一覧を表示します。
about                    Stacker の紹介文を表示します。
delete_history           履歴ファイル（~/.stacker_history）を削除します。
enable_disp_stack        式を実行するたびにスタックを表示します（初期設定）。
disable_disp_stack       スタックを表示しません。
enable_disp_ans          式を実行するたびに、スタックの一番上の値（ans）を 1 行で表示します。
disable_disp_ans         ans を表示しません（初期設定）。
enable_disp_logo         起動時にロゴを表示します（初期設定）。
disable_disp_logo        起動時にロゴを表示しません。
```

`enable_disp_ans` を有効にすると、スタックの表示の前に一番上の値が出力されます。

```text
stacker> enable_disp_ans
stacker> 3 4 +
7
[7]
stacker> disable_disp_stack
stacker> 5 *
35
```

`disable_disp_stack` の状態では、スタックの内容は表示されません。`enable_disp_stack` で戻します。

ロゴは起動時に表示されるだけなので、REPL の中で `disable_disp_logo` を入力しても、表示は変わりません。起動時のロゴを消すには、`~/.stackerrc` に書きます（次節）。

これらの名前は REPL が処理するものであり、Stacker の式の中では使えません。`3 enable_disp_ans` のように他の式と同じ行に書くと、未定義のシンボルとしてエラーになります。

## 設定の演算子

プラグインを無効にする演算子は、通常の演算子なので、スクリプトや `-e` でも使えます。

| 演算子 | 説明 |
| --- | --- |
| `"name" disable_plugin` | 名前が `name` のプラグインの演算子を無効にします。プラグインでない演算子には使えません。登録されていない名前を渡すと `Plugin 'name' is not registered.` と表示します。 |
| `disable_all_plugins` | すべてのプラグインを無効にします。 |

```
stacker:0> disable_all_plugins
[]
stacker:0> "x" disable_plugin
Plugin 'x' is not registered.
[]
```

## ~/.stackerrc

ホームディレクトリに `~/.stackerrc` があると、REPL、スクリプト、`-e` のいずれでも、起動時にそのファイルが Stacker の式として評価されます。よく使う関数や変数の定義を書いておくと便利です。

```stk
# ~/.stackerrc
{x} {x x *} :sq defun
```

```text
$ stacker -e "7 sq echo"
49
```

REPL の表示設定（`enable_disp_stack` / `disable_disp_stack`、`enable_disp_logo` / `disable_disp_logo`、`enable_disp_ans` / `disable_disp_ans`）も、1 行に 1 つずつ書けます。REPL では起動時に適用され、スクリプトと `-e` では無視されます。

```stk
# ~/.stackerrc
disable_disp_logo
enable_disp_ans
{x} {x x *} :sq defun
```

`help`、`about`、`delete_history` は、`~/.stackerrc` に書いても実行されません。
