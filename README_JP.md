
[**英語  (English)**](https://github.com/remokasu/stacker/blob/main/README.md)


```
  _____  _                 _
 / ____|| |               | |
| (___  | |_   __ _   ___ | | __  ___  _ __
 \___ \ | __| / _` | / __|| |/ / / _ \| '__|
 ____) || |_ | (_| || (__ |   < |  __/| |
|_____/  \__| \__,_| \___||_|\_\ \___||_|
```

## 概要

ある晴れた日、学生Aは数学の試験に挑むため、緊張しながら教室へ向かっていました。しかし、彼はある重要なものを忘れてしまっていたのです。それは、関数電卓でした。

<br>

- 学生A（焦りながら）
    ~~~
    先生、電卓を忘れちゃったんですが、お借りできますか？
    ~~~

- 教授（待ってました！と言いたげな表情で）
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

- 学生A（顔を輝かせつつ）
    ~~~
    ええっ！なにそれチートアイテムぅ！？（よく分かんないけど凄そう！デカイし！)
    やったあ...これで試験も余裕です！！(泣）
    ~~~

- 教授（ニヤリと笑いながら）
    ~~~
    ただし、これは逆ポーランド記法の電卓だぞ
    ~~~

- 学生A（戸惑いつつ）
    ~~~
    逆ポ...？逆ポーランドって何です？よく分かんないけど、なんかカッコいいですね！
    ~~~

- 教授（クスクス笑い）
    ~~~
    ちょっと普通の電卓とは扱い方が異なるだけだ。
    なに、心配することはないよ。普通の電卓のようなモードにも切り替えられるからね。
    ~~~

- 学生A（安心しながら）
    ~~~
    なるほど！ありがとうございます！！たすかりましたああ！！
    ~~~

- 教授（声には出さず）
    ~~~
    （ただし切り替え方は初見では分かり難いだろうねｸｸｸ...）
    ~~~


<br>
その試験で学生Aは泣いたという。

このプログラムは、A君のトラウマを追体験することができる。


## インストール

### 前提条件:
Python 3がインストールされていることを確認してください。

### インストールオプション:

- pip経由:
  ```bash
  pip install pystacker
  ```

- ソースから:
  ```bash
  git clone git@github.com:remokasu/stacker.git
  cd stacker
  python setup.py install
  ```

- 遊び終わったら削除しましょう
  ~~~ bash
  > pip uninstall pystacker
  ~~~

## フィードバック

フィードバックを歓迎します。[Issuesページ](https://github.com/remokasu/stacker/issues)で問題や提案を提出してください。

## 依存関係

Stackerは`NumPy`や`Python Prompt Toolkit`などの外部ライブラリを使用します。以下のコマンドでインストールしてください:
```bash
pip install numpy prompt_toolkit
```

## 使用方法

Stackerの実行:
```bash
stacker
```
または:
```bash
python -m stacker
```

Stackerは標準的な算術演算（+、-、*、/ など）の他、高度な関数（sin、cos、tanなど）をサポートしています。ユーザーはRPN形式でコマンドを入力し、カスタムプラグインを使用して機能を拡張できます。

### 入力例

StackerのRPN入力の例を示します

- シングルライン入力:
  ```bash
  stacker:0> 3 4 +
  [7]
  ```

- マルチライン入力:
  ```bash
  stacker:0> 3
  [3]
  stacker:1> 4
  [3, 4]
  stacker:2> +
  [7]
  ```

- #### 変数定義:
  - 構文:
    ```bash
    value $name set
    ```
  - 例:
    ```bash
    stacker:0> 3 $x set
    ```
    この例では, `x`に`3`を代入します。
    未定義のシンボルを入力する場合、シンボル名の先頭にドル記号（$）を付ける必要があります。<br>
    以後、xを使用すると`x`の文字がスタックにプッシュされ、pop時に評価され`3`が返されます。<br>
    シンボルに@を付けると、シンボルの値をプッシュすることができます。<br>
    例えば、`@x`は`3`をプッシュします。
    ``` bash
    stacker:0> 3 $x set
    stacker:1> x
    [x]
    stacker:2> @x
    [x, 3]
    stacker:1> +
    [6]
    ```

- #### 条件分岐
  - if
    - 構文:
      ```bash
      {true_block} condition if
      ```
    - 例:
      ``` bash
      stacker:0> 0 $x set
      stacker:1> {3 4 +} {x 0 ==} if
      [7]
      ```
      ConditionがTrueの場合、{true_block}が実行されます。Falseの場合、何も実行されません。
      この例では {3 4 +} が実行されます。

  - ifelse
    - 構文:
      ```bash
      {true_block} {false_block} condition ifelse
      ```
    - 例:
      ``` bash
      stacker:0> 0 $x set
      stacker:1> {3 4 +} {3 4 -} {x 0 ==} ifelse
      [7]
      ```
      ConditionがTrueの場合、`{true_block}`が実行されます。Falseの場合、`{false_block}`が実行されます。
      この例では {3 4 +} が実行されます。

- #### 繰り返し
  - do
    - 構文:
      ```bash
      start_value end_value $symbol {body} do
      ```
    - 例:
      ```bash
      stacker:0> 0 10 $i {i echo} do
      0
      1
      2
      3
      4
      5
      6
      7
      8
      9
      10
      ```
  - times
    - 構文:
      ```bash
      {body} n times
      ```
    - 例:
      ```bash
      stacker:0> 1 {dup ++} 10 times
      [1 2 3 4 5 6 7 8 9 10 11]
      ```
      この例では、スタックに1をプッシュした後、{dup (トップの要素を複製)し、++ (トップの要素に1を加算)}を10回繰り返します。

- #### 関数定義:
  - 構文:
    ``` bash
    (arg1 arg2 ... argN) {body} $name defun
    ``` 

  - 例
    ```bash
    stacker:0> (x y) {x y *} $multiply defun
    stacker:1> 10 20 multiply
    [200]
    ```
    2つの引数 `x` と `y` を取り、それらを掛け合わせる関数 `multiply` を定義します。

- #### マクロ作成:
  - 構文:
    ```bash
    {body} $name alias
    ```

  - 例:
    ```bash
    stacker:0> {2 ^ 3 * 5 +} $calculatePowerAndAdd alias
    stacker:1> 5 calculatePowerAndAdd
    [80]
    ```
    マクロ `{2 ^ 3 * 5 +}` を定義し、名前 `calculatePowerAndAdd` を割り当てます。このマクロは、スタック上の数値を2乗し、3倍し、5を加算します。


- #### スクリプトのインクルード
  Stackerスクリプトは、`include`コマンドを使用して他のスクリプトをインクルードできます。
  ``` bash
  stacker:0>  "my_script.stk" include
  ```
  "my_script.stk"で定義されたすべての関数とマクロと変数が現在のスタックに追加されます。



- #### 逆ポーランドなんてクソ喰らえだ
    
    中置記法を文字列として入力し、`evalpy`を使用して評価することができます。 <br>
    `evalpy`は`Python`の`eval`関数を使用しているため、`Python`の構文を使用できます。 <br>
    オペレータの仕様は`Stacker`と`Python`では異なるため、注意してください。 <br>
    ```
    tacker:0> "3+5" evalpy
    [8]
    ```
    やはり中置記法こそ正義なのです。 <br>
    さぁ、`Stacker`をアンインストールしましょう。 <br>
    ~~~ bash
    > pip uninstall pystacker
    ~~~


### スクリプトの実行
Stackerスクリプトは*stkファイルで作成できます。スクリプトを実行するには、次の様に実行ファイルを指定します。

- my_script.stk:
  ```bash
    100000 $n set
    0 $p set
    0 n $k {
        -1 k ^ 2 k * 1 + / p + p set
    } do
    4 p * p set
    p echo
  ```

  これを実行するには、次のコマンドを使用します:

    ```bash
    stacker my_script.stk
    ```

### コマンドライン実行
コマンドラインから、指定したRPN式を直接実行できます。

```bash
stacker -e "3 4 + echo"
```


## 設定

- disable_plugin

  指定のプラグインを無効化します。
  ```bash
  stacker:0> "hoge" disable_plugin
  ```
  このコマンドは、プラグインとして追加されたhoge演算子を無効にします。
  ただし、プラグイン以外の演算子には使えません。

- disable_all_plugins

  すべてのプラグインを一括で無効にします。
  ```bash
  stacker:0> disable_all_plugins
  ```

- enable_disp_stack

  スタックの内容を毎回表示する設定を有効にします。デフォルトでは、この設定が既に有効になっています。
  ```bash
  stacker:0> enable_disp_stack
  ```

- disable_disp_stack

  スタックの内容を表示しない設定にします。この設定を有効にすると、スタックの最新の要素のみが表示されます。
  ```bash
  stacker:0> disable_disp_stack
  ```

- disable_disp_logo

  起動時にロゴの表示を無効にします。
  ```bash
  stacker:0> disable_disp_logo
  ```


## 設定ファイル

  起動時に自動で設定を読み込むことができます。設定ファイルは~/.stackerrcに配置します。
  例えば、~/.stackerrcに以下の内容を記述すると、起動時にdisable_disp_logoとdisable_disp_stackが自動で有効になります。
  ```bash
  disable_disp_logo
  disable_disp_stack
  ```


## プラグインの作成

Pythonを使用してStackerのカスタムプラグインを作成します。

1. `plugins`ディレクトリに新しいPythonファイルを作成します（例：`my_plugin.py`）
    ``` 
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
    ```

    ここにプラグインを追加し、Stackerを再インストールすると、プラグインが恒久的に適用されます。

2. または、Stackerを実行しているディレクトリに`plugins`ディレクトリを作成します。これにより、再インストールせずにプラグインを使用できます。
3. プラグインファイル内に必要な関数やクラスを定義します。
4. これらをStackerに登録するために`setup`関数を追加します。

例：
```python
from stacker.stacker import Stacker

def function(a, b):
    # 何かの処理

def setup(stacker: Stacker):
    stacker.register_plugin("command", function)
```

## プラグインの無効化
特定のプラグインを無効にするには operatorName disable_plugin を使用します。<br>
全てのプラグインを無効にするには disable_all_plugins を使用します。<br>


## ドキュメント
より詳細なドキュメントについては、[`stacker/docs`](https://github.com/remokasu/stacker/blob/main/docs/README.md)を参照してください。


## 使用可能コマンド
`+` `-` `*` `/` `//` `/` `%` `++` `--` `neg` `bin` `oct` `dec` `hex` `band` `bor` `bxor` `~` `>>` `<<` `==` `!=` `<=` `<` `>=` `>` `eq` `noq` `le` `lt` `ge` `gt` `echo` `print` `and` `or` `not` `&&` `||` `^` `log` `log2` `log10` `exp` `sin` `cos` `tan` `asin` `acos` `atan` `sinh` `cosh` `tanh` `asinh` `acosh` `atanh` `sqrt` `gcd` `lcm` `radians` `!` `ceil` `floor` `comb` `perm` `abs` `cbrt` `ncr` `npr` `roundn` `round` `rand` `randint` `uniform` `dice` `int` `float` `str` `bool` `seq` `range` `min` `sum` `max` `len` `drop` `dup` `swap` `pick` `rot` `rotl` `insert` `rev` `clear` `disp` `eval` `asc` `chr` `concat` `time` `if` `ifelse` `times` `do` `set` `defun` `alias` `include`
