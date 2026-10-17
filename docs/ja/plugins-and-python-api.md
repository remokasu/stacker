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
1 2 3 stack-summary
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
[4.242640687119285, 5.656854249492381, 7.0710678118654755]
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
stacker.register_plugin(name, func, push_result_to_stack=True, pass_core=False, desc=None)
```

| 引数 | 意味 |
|---|---|
| `name` | Stacker で使う語の名前。`stack-summary` のようにハイフンも使える |
| `func` | 呼び出される Python 関数。スタックから取る引数の数は、`func` の引数の数で決まる（`pass_core=True` のときは先頭の 1 つを除く） |
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

`stacker` パッケージが公開しているのは、`Stacker`（インタプリタ）、`Symbol`（後述）、`error`（例外クラス）、`constant`、`include` です。

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

`prelude=False` のインスタンスから `include` したファイルも、prelude なしで読み込まれます。

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

### 例外

Stacker が意図して出すエラーは、すべて `stacker.error.StackerError` を継承します。

| 例外 | 起きる場面 |
|---|---|
| `UndefinedSymbolError` | 定義されていない名前を使った |
| `StackUnderflowError` | スタックの値が足りない |
| `StackerSyntaxError` | 構文が不正（名前の位置に文字列を書いたなど） |
| `UnterminatedTokenError` | 閉じていない文字列・リスト・ブロック・ブロックコメント。`StackerSyntaxError` の子クラス |
| `StackerTypeError` | 語に渡した値の型が違う。Python の `TypeError` も継承する |
| `ResultCountError` | `map` / `filter` の関数や `reduce` / `fold` の本体が、要素ごとに 2 つ以上の値を残した |
| `StackerRecursionError` | 再帰の上限を超えた。`name`・`limit`・`kind` 属性を持つ |
| `IncludeError` | `include` に失敗した |

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
UnterminatedTokenError: Unterminated array starting at line 1
(Python) ZeroDivisionError: division by zero
(Python) TypeError: can only concatenate str (not "int") to str
```

0 による除算や、文字列と数の足し算のように、Python の演算がそのまま失敗した場合は、`ZeroDivisionError` や `TypeError` といった Python の例外がそのまま出ます。`StackerError` だけを捕まえると取りこぼすので、必要なら `Exception` も捕まえてください。

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
