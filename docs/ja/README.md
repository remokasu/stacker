# Stacker マニュアル

Stacker は、逆ポーランド記法（RPN）で計算する電卓であり、プラグインで拡張できるスクリプト言語です。
このマニュアルは [VERSION](../VERSION) に書かれた版の Stacker に対応しています。

## 目次

1. [はじめに](getting-started.md) — インストール、REPL、最初の計算、スクリプトの実行
2. [構文と値](syntax.md) — 数値・文字列・リスト・ブロック・リテラル・コメント
3. [名前とシンボル](names-and-symbols.md) — 名前の 3 つの書き方、シンボル、変数の束縛
4. [制御構文](control.md) — 条件分岐とループ
5. [関数・ラムダ・マクロ](functions-and-macros.md) — defun、lambda、alias、defmacro
6. [スクリプトとファイルの取り込み](scripts.md) — .stk ファイル、include、prelude、エラー表示
7. [演算子リファレンス](operators.md) — すべての組み込み語の一覧
8. [REPL とコマンドライン](repl-and-cli.md) — REPL のコマンド、コマンドラインのオプション、~/.stackerrc
9. [プラグインと Python からの利用](plugins-and-python-api.md) — プラグインの作り方、Python への埋め込み

## そのほかの資料

- [サンプルスクリプト](../../examples/)
- [変更履歴](../../CHANGELOG.md)
- 不具合の報告や要望: [GitHub Issues](https://github.com/remokasu/stacker/issues)
