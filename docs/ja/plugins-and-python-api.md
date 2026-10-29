# プラグインと Python からの利用

Stacker は Python で書かれているので、Python の関数を語として追加（プラグイン）したり、Python のプログラムの中でインタプリタを動かしたりできます。このページでは、その両方を説明します。

## プラグイン

プラグインは、`setup(stacker)` という関数を持つ Python ファイルです。Stacker は起動時にこの関数を呼び、`setup` の中で登録された語が使えるようになります。

### 例

`plugins/geometry.py`:

```python
import math


def hypot(a, b):
    return math.hypot(a, b)


def shout(text):
    print(text.upper() + "!")


def stack_summary(stacker):
    print(f"depth={len(stacker.stack)}")


def setup(stacker):
    stacker.register_plugin("hypot", hypot, desc="Length of the hypotenuse")
    stacker.register_plugin("shout", shout, push_result_to_stack=False)
    stacker.register_plugin(
        "stack-summary", stack_summary, push_result_to_stack=False, pass_core=True
    )
    stacker.register_parameter("golden", 1.618033988749895)
```

`plugins/` の置かれたディレクトリで、次のスクリプト `demo.stk` を実行します。

```stk
3 4 hypot echo
"hello" shout
1 2 3 stack-summary 3 dropn
golden 2 * echo
[3 4 5] {dup hypot} map echo
```

```bash
stacker demo.stk
```

```text
5.0
HELLO!
depth=3
3.23606797749979
[4.242640687119285 5.656854249492381 7.0710678118654755]
```

プラグインの語は組み込みの演算子と同じように使えます。引数は Python 関数の引数の数だけスタックから取られ（`hypot` なら 2 つ）、`{dup hypot} map` のようにブロックの中でも使えます。

### プラグインの置き場所

起動時に、次の 2 か所の `*.py` ファイルが、この順に読み込まれます。

1. Stacker のパッケージ内の `plugins/` ディレクトリ（`stacker/plugins/`）
2. コマンドを実行したディレクトリ（カレントディレクトリ）の `plugins/`。ディレクトリがなければ読み飛ばされます。

ファイル名が `__` で始まるファイルは読み込まれません。同じ名前の語が両方で登録されたときは、あとに読み込まれた 2 のものが使われます。

2 は、そのディレクトリで実行したときだけ有効です。プロジェクトごとに語を足したいときに向いています。スクリプトがあるディレクトリではなく、**実行したディレクトリ**の `plugins/` が見られる点に注意してください。

1 に入れると、どこで実行しても使えます。`--addplugin` はそのためのコマンドで、指定した Python ファイルをパッケージ内の `plugins/` にコピーします。

```bash
stacker --addplugin plugins/geometry.py
```

```text
Successfully added the plugin 'plugins/geometry.py' to Stacker.
/path/to/site-packages/stacker/plugins
```

プラグインの読み込みに失敗すると（`setup` がない、`setup` の中で例外が出るなど）、`Failed load plugin (ファイル名). 理由` と表示して Stacker は終了します。

Python から `Stacker()` を直接作る場合は、プラグインは自動では読み込まれません。次の節の方法で登録してください。

### register_plugin

```python
stacker.register_plugin(operator_name, operator_func, push_result_to_stack=True, pass_core=False, desc=None)
```

| 引数 | 意味 |
|---|---|
| `operator_name` | Stacker で使う語の名前。`stack-summary` のようにハイフンも使える |
| `operator_func` | 呼び出される Python 関数。スタックから取る引数の数は、`operator_func` の引数の数で決まる（`pass_core=True` のときは先頭の 1 つを除く） |
| `push_result_to_stack` | `True` なら戻り値をスタックに積む。`False` なら戻り値を捨てる。`None` を返す関数でも `True` なら `null` が積まれるので、何も積まない語は `False` にする |
| `pass_core` | `True` なら、`func` の第 1 引数として `Stacker` のインスタンスが渡される。変数やスタックを直接読み書きする語に使う |
| `desc` | REPL の `help` に表示される説明。省略できる |

`func` は Python で書かれた関数（`def` か `lambda`）でなければなりません。`math.hypot` のような組み込み関数は直接渡せないので、上の例のように包みます。引数の数は固定で、デフォルト値のある引数も 1 つの引数として数えられます。

プラグインの語は、同じ名前の組み込みの演算子より優先されます。`+` を登録すると、組み込みの `+` は使えなくなります。

### register_parameter

```python
stacker.register_parameter(name, value)
```

`name` という変数を `value` で作ります。上の例の `golden` のように、スクリプトからは変数として読めます。`0.1 :golden =` のように、あとからスクリプトで書き換えることもできます。

### プラグインの無効化

- `"hypot" disable_plugin`: 名前を指定して 1 つの語を無効にします。文字列で渡します。登録されていない名前を渡すと `Plugin 'hypot' is not registered.` と表示されます。組み込みの演算子には使えません。
- `disable_all_plugins`: すべてのプラグインの語を無効にします。

無効にしたあとにその語を使うと、`UndefinedSymbolError` になります。無効にできるのは語だけで、`register_parameter` で作った変数は残ります。

## Python から使う

```python
from stacker import Stacker
```

`stacker` パッケージが公開しているのは、`Stacker`（インタプリタ）、`Symbol`（後述）、`Array`（後述）、`Console` と `StreamConsole`（後述）、`__version__`、`error`（例外クラス）、`constant`、`include` です。

### eval と process_expression と stack

`Stacker` のインスタンスは、スタックと変数・関数・マクロを持ちます。式を評価する方法が 2 つあり、スタックの扱いが違います。

| 方法 | スタック |
|---|---|
| `eval(式)` | 新しいスタックで評価し、評価後のスタック（`collections.deque`）を返す。`stack=` に渡したスタックがあれば、そのスタックの続きから評価する。`stacker.stack` は変わらない |
| `process_expression(式)` | `stacker.stack` を直接更新する。戻り値はない。REPL やスクリプトの実行と同じ動き |
| `stack` | インスタンスが持つスタック（`deque`）。`process_expression` の結果が残る |

どちらの方法でも、変数・関数・マクロの定義はインスタンスに残ります。

```python
from stacker import Stacker, Symbol

s = Stacker()
print(s.eval("1 2 +"))                  # 評価後のスタックが返る
print(s.eval("10 *", stack=s.eval("4")))  # stack= で続きから評価する

s.eval("5 :x =")                        # 変数は Stacker に残る
print(s.eval("x 2 *"))

s.process_expression("1 2 +")           # s.stack を直接更新する
s.process_expression("10 *")
print(s.stack, s.get_stack_length())
print(s.stack.pop())
```

```text
deque([3])
deque([40])
deque([10])
deque([30]) 1
30
```

`pass_core=True` のプラグインが `stacker.stack` を読むとき、`eval` で評価している最中は空に見えます。スタックを読む語を Python から試すときは、`process_expression` を使ってください。

### Python から見た値の型

スタックの要素は、次の Python の値になります。

```python
for source in [':abc', '"hi"', '[1 2 3]', '{1 +}', '1 3 /', 'true', 'null']:
    (value,) = s.eval(source)
    print(f"{source:10} -> {type(value).__name__:8} {value!r}")
print(Symbol("abc") == Symbol("abc"), Symbol("abc").name)
```

```text
:abc       -> Symbol   Symbol('abc')
"hi"       -> String   'hi'
[1 2 3]    -> list     [1, 2, 3]
{1 +}      -> Stacker  {1 +}
1 3 /      -> float    0.3333333333333333
true       -> bool     True
null       -> NoneType None
True abc
```

- 整数・小数・真偽値・`null` は、Python の `int`・`float`・`bool`・`None` です。
- リストは `list` です。
- 配列（`[1 2 3] array`）は `list` を継承した `Array` で、`repr` は `Array([1, 2, 3])`。辞書（`dict`）は Python の `dict` そのものです。どちらもインタプリタの中と同じ実体なので、Python 側で書き換えるとスクリプトからも変わります。`from stacker import Array` で使えます。
- 文字列は `str` を継承した `String` です。`== "hi"` のように普通の `str` と比べられます。
- シンボルは `Symbol` で、`str` ではありません。名前は `.name` で読み、`Symbol("abc")` で作れます。文字列 `"abc"` とは等しくなりません。詳しくは[名前とシンボル](names-and-symbols.md)を参照してください。
- コードブロックは `Stacker` のインスタンスです。

### prelude を読み込まない

`Stacker()` は prelude（`alias` や `mean`。[スクリプトとファイルの取り込み](scripts.md)を参照）を読み込みます。素の状態から始めたいときは `prelude=False` にします。

```python
try:
    Stacker(prelude=False).eval("[1 2 3] mean")
except Exception as e:
    print(type(e).__name__, e)
print(Stacker().eval("[1 2 3] mean"))
```

```text
UndefinedSymbolError `mean` is not defined.
deque([2.0])
```

`include` / `require` したファイルは、そのインスタンスの中で評価されます。`prelude=False` のインスタンスなら、取り込んだファイルも prelude の語を使えません。Python からは `Stacker.include(path)` と `Stacker.require(path)` で同じことができます。

### スクリプトファイルを走らせる

`Stacker.run_file(path)` は、`stacker script.stk` と同じようにファイルを走らせます。式を 1 つずつ、`process_expression` と同じくインスタンスのスタックで評価するので、ファイルが残した値は `stack` に残り、`ans` でも読めます。走らせている間はそのファイルが今のファイルになり、`script-path`、相対パスの `include`、ファイルの中で定義した関数の定義場所は、そのファイルを指します。

`tool.stk` が次の内容だとします。

```text
{x} {x 2 *} :double defun
main? echo
21 double
```

```python
from pathlib import Path
from stacker import Stacker

s = Stacker()
s.run_file("tool.stk")
print(s.stack)
print(Path(s.eval("script-path")[0]).name, s.eval("5 double"))
```

```text
true
deque([42])
tool.stk deque([10])
```

| 引数 | 意味 |
|---|---|
| `main=True` | このファイルをメインのスクリプトにする。`main?` が真になり、`main-script-path` がこのファイルを返す。`False` なら変えない |
| `restore_location=False` | `True` にすると、走らせ終えたあと（エラーで止まったときも）今のファイルと行を元に戻す。あとから走るコードに、このファイルを今のファイルとして見せたくないときに使う。このときエラーには、ファイルと行が付く |
| `intercept=None` | 式の文字列を受け取る関数。真を返した式は評価しない |

ファイルが閉じていない文字列・リスト・ブロックで終わるときは、その前までの式を走らせてから `UnterminatedTokenError` が出ます。

止まった場所は `location` で読めます。`(ファイル, 行, その行の文字列)` の組です。エラーで止まったときはその式が始まる行、閉じていない文字列・リスト・ブロックで止まったときはそれが始まった行、最後まで走ったときは最後の式の行を指します。何も走らせていなければ `(None, None, None)` です。

`broken.stk` が次の内容だとします。

```text
1 drop
{
  nope
} eval
```

```python
from pathlib import Path
from stacker import Stacker

s = Stacker()
try:
    s.run_file("broken.stk")
except Exception as error:
    file, line, text = s.location
    print(type(error).__name__, Path(file).name, line, text)
```

```text
UndefinedSymbolError broken.stk 2 {
```

`include` したファイルの中でエラーが起きたときは、`location` は `include` を書いた行を指します。`restore_location=True` で走らせたときは、`location` も走らせる前に戻ります。

### 出力と入力の行き先

`echo`・`print`・`disp`・`vars` などの出力と、`read`・`read-line`・`read-stdin` などの入力は、既定では Python の `sys.stdout`・`sys.stderr`・`sys.stdin` を、語が動いた時点で使います。`Stacker()` を作ったあとで `sys.stdout` を差し替えても（`contextlib.redirect_stdout` など）、その差し替え先に書きます。

行き先をインスタンスごとに変えるときは、`console=` に `StreamConsole` を渡します。渡さなかったストリームには `sys` のものを使います。

```python
import io
from stacker import Stacker, StreamConsole

out = io.StringIO()
s = Stacker(console=StreamConsole(stdout=out, stdin=io.StringIO("3 4 *\n")))
s.eval('"hi" echo 1 2 disp')
print(repr(out.getvalue()))
print(s.eval("read eval"))
try:
    s.eval("read")
except EOFError:
    print("EOFError")
```

```text
'hi\n[1 2]\n'
deque([12])
EOFError
```

`read` は入力が終わると `EOFError` を出します。`StreamConsole` の `read` は、読む前に出力を flush し、行末の改行を落とします。ほかの行き先が必要なら `Console` を継承して `stdout()`・`stderr()`・`stdin()`・`input_line()` を上書きします。ストリームを返すメソッドは None を返してはいけません。`input_line()` は改行を落とした 1 行を返し、入力が終わったら `EOFError` を出します。

行き先が使われるのは、そのインスタンスの `eval`・`process_expression`・`run_file`・`include`・`require` が動いている間です。プラグインの語の中から別のインスタンスを呼んでも、戻れば元の行き先に戻ります。`evaluate` はこの切り替えをしないので、呼んだ側の行き先のままです。新しいスレッドは既定の行き先から始まるので、別のスレッドで評価するときは、そのスレッドの中で `eval` などを呼んでください。

プラグインの語が文字を出すときは、`print(..., file=console.stdout())` のように `stacker.engine.console` の `stdout()` に書くと、インスタンスの行き先に従います。

```python
from stacker.engine import console


def hello():
    print("hello", file=console.stdout())
```

`exit`・`abort`・`exit-code` は行き先に関係なく、Python の `SystemExit` を出します。`try` でも捕まりません。Python から使うときは `SystemExit` を捕まえてください。

```python
from stacker import Stacker

try:
    Stacker().eval("3 exit-code")
except SystemExit as e:
    print("exit code", e.code)
```

```text
exit code 3
```

### コマンドラインと同じにする

`stacker` コマンドは、`Stacker()` を作る前後に次の設定をしています。Python から使うインスタンスを同じ動きにしたいときは、同じことをしてください。

| コマンドラインがすること | Python から |
|---|---|
| 標準出力と標準エラーを UTF-8 にし、表せない文字はエスケープして書く | `sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")`（`sys.stderr` も） |
| 警告を `WARNING:stacker:...` の形で標準エラーに出す | `Stacker()` を作る前に `logging.basicConfig(level=logging.INFO)` |
| 再帰の上限を設定する | 下の「再帰の上限」を参照 |
| スクリプトをメインのスクリプトとして走らせる | `run_file(path)` |
| スクリプトの後ろの引数を、`args` の語が返す文字列のリストにする | `s.arguments = ["in.txt", "3"]` |

### プラグインを Python から登録する

`register_plugin` と `register_parameter` は Python から直接呼べます。プラグインのファイルを Python から読み込むには、`setup` を自分で呼びます。

```python
import importlib.util
from stacker import Stacker

s = Stacker()
spec = importlib.util.spec_from_file_location("geometry", "plugins/geometry.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.setup(s)
print(s.eval("3 4 hypot"))
print(s.plugin_descriptions)

s.register_plugin("triple", lambda x: x * 3)
print(s.eval("[1 2 3] {triple} map"))
```

```text
deque([5.0])
{'hypot': 'Length of the hypotenuse', 'shout': None, 'stack-summary': None}
deque([[3, 6, 9]])
```

### 語の一覧

`get_operator_groups()` は、組み込みの語を `operators` と同じ群・同じ順で返します。群ごとに `(キー, 見出し, {語: 説明})` の組です。呼ぶたびに作り直すので、`register_operator` で置き換えた語は新しい説明で、その群の最後に並びます。プラグインの語は入りません。プラグインの説明は `get_plugin_descriptions()` で読めます。

```python
from stacker import Stacker

s = Stacker()
groups = s.get_operator_groups()
print([key for key, heading, words in groups])
stack = {key: words for key, heading, words in groups}["stack"]
print(stack["swap"])
```

```text
['regular', 'hof', 'aggregate', 'transform', 'collection', 'stack', 'settings', 'system']
Swaps the top two elements of the stack.
```

### 整数の桁数

`Stacker()` を作ると、ホストが整数と文字列の変換に設けている桁数の上限（4300 桁）を外します（`sys.set_int_max_str_digits(0)`）。Stacker の整数には大きさの上限がなく、`2000 !` のような値を表示したり書き出したりするためです。この設定はプロセス全体に効き、信頼できない入力を `int` で読むと桁数の 2 乗の時間がかかります（100 万桁で約 1 秒）。信頼できない入力を扱うホストは、`Stacker()` を作ったあとに `sys.set_int_max_str_digits(4300)` などで上限を戻してください。

### 例外

Stacker が意図して出すエラーは、すべて `stacker.error.StackerError` を継承します。

| 例外 | 起きる場面 |
|---|---|
| `UndefinedSymbolError` | 定義されていない名前を使った |
| `StackUnderflowError` | スタックの値が足りない |
| `StackerSyntaxError` | 構文が不正（名前の位置に文字列を書いたなど） |
| `UnterminatedTokenError` | 閉じていない文字列・リスト・ブロック・ブロックコメント。`StackerSyntaxError` の子クラス |
| `StackerTypeError` | 語に渡した値の型が違う。Python の `TypeError` も継承する |
| `StackerIndexError` | `at` / `at!` の添字が範囲外、空の配列の `pop!`。Python の `IndexError` も継承する |
| `KeyNotFoundError` | `del!` に無いキーを渡した |
| `ResultCountError` | `map` / `filter` の関数や `reduce` / `fold` の本体が、要素ごとに 2 つ以上の値を残した |
| `StackerRecursionError` | 再帰の上限を超えた。`name`・`limit`・`kind` 属性を持つ |
| `IncludeError` | `include` / `require` に失敗した（見つからない、`.stk` でない、循環） |
| `ValidationError` | 値が語の範囲の外（`-1 sqrt`、`-1 5 array-of`、`0 trailing-zeros`、ホストが値を断った場合） |
| `StackerRuntimeError` | 実行環境の問題（開けないファイル、深すぎて表示できない値など） |
| `NoValueProducedError` | 値を残さなければならないブロックが何も残さなかった |
| `UserError` | `throw` で投げたエラー。`kind` 属性がそのまま表示される |
| `ScriptReadError` | スクリプトが読めない（`.stk` でない、UTF-8 でない） |
| `DupError` `DropError` `PickError` `RollError` `InsertError` | スタック操作の語が空のスタックや範囲外の位置を扱った |

語が利用者のコードを走らせずにホストの関数を呼ぶとき、ホストが出す `TypeError` は `StackerTypeError`、`ValueError` / `OverflowError` は `ValidationError`、`IndexError` は `StackerIndexError` として、語の名前と値つきで言い直されます。`ZeroDivisionError` と、`map` などの本体の中で起きたエラーは、そのまま伝わります。

```python
from stacker.error import StackerError, UndefinedSymbolError

for source in ["1 foo", "1 +", "[1 2", "1 0 /", '"a" 1 +']:
    try:
        Stacker().eval(source)
    except UndefinedSymbolError as e:
        print("UndefinedSymbolError:", e)
    except StackerError as e:
        print(f"{type(e).__name__}: {e}")
    except Exception as e:
        print(f"(Python) {type(e).__name__}: {e}")
```

```text
UndefinedSymbolError: `foo` is not defined.
StackUnderflowError: Operator `+` requires 2 arguments.
UnterminatedTokenError: Unterminated list starting at line 1
(Python) ZeroDivisionError: division by zero
StackerTypeError: `+` cannot use 'a' and 1 together; to join text, make both values strings with `str`
```

0 による除算（`ZeroDivisionError`）と、`map` などの本体の中でプラグインの関数が出した例外は、Python の例外のまま出ます。`StackerError` だけを捕まえると取りこぼすので、必要なら `Exception` も捕まえてください。

### 再帰の上限

コマンドラインの `--recursion-limit` に当たる設定は、`stacker.engine.recursion.set_limit(n)` です（1 から 1800）。ただし、Python のインタプリタ自身の再帰の上限（既定は 1000）のほうが低いので、既定のままでは深い再帰で `StackerRecursionError` より先に Python の `RecursionError` が出ます。Stacker の上限まで再帰させたいときは、先に `sys.setrecursionlimit` を上げてください。`stacker` コマンドは起動時にこの設定を済ませています。

```python
import sys
from stacker import Stacker
from stacker.error import StackerRecursionError

sys.setrecursionlimit(30_000)
s = Stacker()
s.eval("{n} {n f} :f defun")
try:
    s.eval("1 f")
except StackerRecursionError as e:
    print(e, e.name, e.limit, e.kind)
```

```text
Maximum recursion depth (1500) exceeded in function `f` f 1500 function
```
