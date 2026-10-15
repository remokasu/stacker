# はじめに

## Stacker とは

Stacker は Python 製の RPN（逆ポーランド記法）電卓です。値を先に書き、演算子をあとに書きます。`3 + 4` ではなく `3 4 +` と入力します。括弧は要りません。

同じ記法のまま、変数、関数、マクロ、条件分岐、ループを持つスクリプト言語としても使えます。スクリプトは `.stk` ファイルに書きます。演算子は Python のプラグインで追加できます。

## インストール

Python 3.10 以上が必要です。PyPI から入れる場合は次のとおりです。

```bash
pip install pystacker
```

ソースから入れる場合は、リポジトリを取得してそのディレクトリで `pip install .` を実行します。

```bash
git clone https://github.com/remokasu/stacker.git
cd stacker
pip install .
```

依存ライブラリは `prompt-toolkit` だけで、自動的にインストールされます。

## REPL を起動する

引数なしで実行すると、対話モード（REPL）が始まります。

```bash
stacker
```

`python -m stacker` でも同じです。

```text
Stacker X.Y.Z on linux
Type "help" to get more information.
stacker:0>
```

終了するには `exit` と入力するか、Ctrl+D を押します。

## 最初の計算

値を入力するとスタックに積まれ、演算子は必要な個数の値をスタックから取り出して、結果を積みます。入力のたびに、スタックの中身が下から順に `[ ]` の中に表示されます。

```
stacker:0> 3 4 +
[7]
```

`3` と `4` を積み、`+` が 2 つを取り出して和の `7` を積みました。

式は左から右へ評価されます。`2 3 4 * +` は、先に `3 4 *` が 12 になり、次に `2 12 +` が計算されます。`2 + 3 * 4` に相当する式です。

```
stacker:0> 2 3 4 * +
[14]
```

結果はスタックに残るので、続けて入力するとその値を使えます。

```
stacker:0> 3 4 +
[7]
stacker:1> 2 *
[14]
stacker:1> 10 -
[4]
```

複数の値を積んでおくこともできます。

```
stacker:0> 1 2 3
[1 2 3]
stacker:3> +
[1 5]
stacker:2> clear
[]
```

プロンプトの番号は、入力前のスタックにある値の個数です。`clear` はスタックを空にします。

値の書き方や式の文法は[構文と値](syntax.md)で説明します。

## スクリプトファイルを実行する

`.stk` ファイルを作り、コマンドラインにファイル名を渡して実行します。スクリプトは、スタックの内容を自動では表示しません。結果を出力するには `echo` を使います。

```stk
# hello.stk
3 4 + echo
"hello" echo
```

```bash
stacker hello.stk
```

```text
7
hello
```

`#` から行末まではコメントです。スクリプトの書き方は[スクリプトとファイルの取り込み](scripts.md)を参照してください。

## 1 行だけ実行する

`-e` に式を渡すと、REPL を開かずに実行して終了します。

```bash
stacker -e "3 4 + echo"
```

```text
7
```

`-e` もスタックを表示しないので、結果が必要なら `echo` を付けます。

## VSCode で構文ハイライトを使う

リポジトリの `.vscode-extension` ディレクトリを VSCode の拡張機能ディレクトリにコピーすると、`.stk` ファイルがハイライトされます。リポジトリのルートで実行します。

```bash
# ローカルの VSCode
mkdir -p ~/.vscode/extensions/stacker-language-0.1.0
cp -r .vscode-extension/* ~/.vscode/extensions/stacker-language-0.1.0/

# VSCode Server（Remote SSH）
mkdir -p ~/.vscode-server/extensions/stacker-language-0.1.0
cp -r .vscode-extension/* ~/.vscode-server/extensions/stacker-language-0.1.0/
```

そのあと Ctrl+Shift+P から「Developer: Reload Window」を実行すると有効になります。

## 次に読むページ

- [構文と値](syntax.md): 値の種類と式の書き方
- [名前とシンボル](names-and-symbols.md): 変数と、名前そのものを値として扱う方法
- [制御構文](control.md): 条件分岐とループ
- [関数・ラムダ・マクロ](functions-and-macros.md): `defun` と `defmacro`
- [スクリプトとファイルの取り込み](scripts.md): `.stk` ファイルの書き方
- [演算子リファレンス](operators.md): すべての演算子
- [REPL とコマンドライン](repl-and-cli.md): オプションと REPL の操作
- [プラグインと Python からの利用](plugins-and-python-api.md): 演算子の追加
