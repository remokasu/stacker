# 演算子リファレンス

Stacker が標準で持つ語（演算子・prelude・定数・リテラル）の一覧です。表の「例」は、スタックに `1 2 3 4 5` を積んだ状態から実行できる式です。

読み方:

- `a b -` のような記述は、スタックから `b`（一番上）、`a`（その下）の順に取り出すことを表します。結果は特に断らない限りスタックに積まれます。
- 同じ動作の別名は 1 行にまとめています（例: `reduce`, `fold`）。
- 数値リテラルや文字列などの書き方は [構文と値](syntax.md)、名前とシンボルは [名前とシンボル](names-and-symbols.md) を参照してください。

## 目次

- [算術](#算術)
- [比較](#比較)
- [論理](#論理)
- [ビット演算と基数変換](#ビット演算と基数変換)
- [数学](#数学)
- [乱数](#乱数)
- [型と変換](#型と変換)
- [文字列](#文字列)
- [リスト](#リスト)
- [配列と辞書](#配列と辞書)
- [高階関数](#高階関数)
- [集約と変換](#集約と変換)
- [スタック操作](#スタック操作)
- [制御構文](#制御構文)
- [定義と束縛](#定義と束縛)
- [評価とコード操作](#評価とコード操作)
- [入出力](#入出力)
- [ファイル](#ファイル)
- [OS](#os)
- [時間](#時間)
- [終了](#終了)
- [プラグインと設定](#プラグインと設定)
- [システム](#システム)
- [prelude](#prelude)
- [定数とリテラル](#定数とリテラル)

## 算術

| 演算子 | 説明 | 例 |
|---|---|---|
| `+` | 加算。`a b +` は a + b | `3 5 +` |
| `-` | 減算。`a b -` は a - b | `10 3 -` |
| `*` | 乗算。`a b *` は a × b | `4 6 *` |
| `/` | 除算。`a b /` は a ÷ b。結果は float | `12 4 /` |
| `//` | 切り捨て除算。`a b //` は a ÷ b を負の無限大方向に丸めた整数 | `7 2 //` |
| `%` | 剰余。`a b %` は a を b で割った余り（符号は b に従う） | `9 2 %` |
| `^` | べき乗。`a b ^` は a の b 乗 | `3 2 ^` |
| `neg` | 符号を反転 | `5 neg` |
| `++` | 1 を加える | `5 ++` |
| `--` | 1 を引く | `5 --` |

`++` と `--` は値を 1 つ取って結果を積みます。変数そのものは更新しません（変数への代入は `set` を使います）。

## 比較

結果は `true` / `false` です。`a b <` のように、下の値を左辺として比べます。

| 演算子 | 説明 | 例 |
|---|---|---|
| `==`, `eq` | 等しい | `1 1 ==`, `1 1 eq` |
| `!=`, `neq` | 等しくない | `1 0 !=`, `1 0 neq` |
| `<`, `lt` | `a b <` は a < b | `1 2 <`, `1 2 lt` |
| `<=`, `le` | `a b <=` は a ≤ b | `3 3 <=`, `3 3 le` |
| `>`, `gt` | `a b >` は a > b | `2 1 >`, `2 1 gt` |
| `>=`, `ge` | `a b >=` は a ≥ b | `3 3 >=`, `3 3 ge` |

## 論理

| 演算子 | 説明 | 例 |
|---|---|---|
| `and`, `&&` | 論理積。両方が真ならば後の値、そうでなければ偽の側の値を返す | `true false and`, `true false &&` |
| `or`, `\|\|` | 論理和。前の値が真ならばそれ、そうでなければ後の値を返す | `true false or`, `true false \|\|` |
| `not` | 論理否定 | `true not` |

`and` と `or` は真偽値だけでなく任意の値を受け取り、`1 2 and` は `2`、`0 5 or` は `5` になります。2 つの引数は両方とも評価済みの値で、短絡評価はしません。

## ビット演算と基数変換

| 演算子 | 説明 | 例 |
|---|---|---|
| `band` | ビット積 | `3 2 band` |
| `bor` | ビット和 | `3 2 bor` |
| `bxor` | ビット排他的論理和 | `3 2 bxor` |
| `~` | ビット反転（`n` に対して `-n-1`） | `5 ~` |
| `>>` | 右シフト。`a n >>` は a を n ビット右へ | `8 2 >>` |
| `<<` | 左シフト。`a n <<` は a を n ビット左へ | `2 2 <<` |
| `bit-length` | 整数を書くのに要るビット数（0 は 0。負の数は絶対値） | `255 bit-length` |
| `popcount` | 整数の 1 のビットの数（負の数は絶対値） | `255 popcount` |
| `trailing-zeros` | 最下位の 1 のビットより下の 0 の数。0 はエラー | `40 trailing-zeros` |
| `bin` | 2 進表記の文字列（`"0b101"`） | `5 bin` |
| `oct` | 8 進表記の文字列（`"0o12"`） | `10 oct` |
| `hex` | 16 進表記の文字列（`"0xff"`） | `255 hex` |
| `dec` | 10 進の整数に変換。`"0b101"` のような接頭辞付きの文字列も受け付ける | `0b101010 dec`, `"0b101" dec` |

## 数学

三角関数・逆三角関数の角度はラジアンです。

| 演算子 | 説明 | 例 |
|---|---|---|
| `abs` | 絶対値 | `-3 abs` |
| `sqrt` | 平方根。負の数はエラー | `9 sqrt` |
| `cbrt` | 立方根 | `27 cbrt` |
| `exp` | e の累乗 | `3 exp` |
| `real` | 実部。実数はそのまま | `3+4j real` |
| `imag` | 虚部。実数は 0 | `3+4j imag` |
| `conj` | 共役複素数。実数はそのまま | `3+4j conj` |
| `arg` | 偏角（-π から π）。正の実数は 0、負の実数は π | `1j arg` |
| `polar` | `r t polar` は長さ r、偏角 t の複素数 | `1 pi 2 / polar` |
| `log` | 自然対数（引数 1 つ） | `2 log` |
| `log2` | 2 を底とする対数 | `4 log2` |
| `log10` | 10 を底とする対数 | `4 log10` |
| `sin` | 正弦 | `pi 2 / sin` |
| `cos` | 余弦 | `pi cos` |
| `tan` | 正接 | `pi 4 / tan` |
| `asin` | 逆正弦（結果はラジアン） | `0.5 asin` |
| `acos` | 逆余弦（結果はラジアン） | `0.5 acos` |
| `atan` | 逆正接（結果はラジアン） | `1 atan` |
| `sinh` | 双曲線正弦 | `1 sinh` |
| `cosh` | 双曲線余弦 | `1 cosh` |
| `tanh` | 双曲線正接 | `1 tanh` |
| `asinh` | 逆双曲線正弦 | `1 asinh` |
| `acosh` | 逆双曲線余弦 | `2 acosh` |
| `atanh` | 逆双曲線正接 | `0.5 atanh` |
| `radians` | 度をラジアンに変換 | `180 radians` |
| `ceil` | 切り上げ（整数） | `3.2 ceil` |
| `floor` | 切り捨て（整数） | `3.8 floor` |
| `round` | 最も近い整数へ丸める。ちょうど半分は偶数側（`2.5` は `2`） | `3.5 round` |
| `roundn` | 小数 n 桁に丸める。`x n roundn` | `3.51 1 roundn` |
| `gcd` | 最大公約数 | `12 18 gcd` |
| `lcm` | 最小公倍数 | `4 6 lcm` |
| `!` | 階乗。後置: `4 !` | `4 !` |
| `comb`, `ncr` | 組み合わせの数。`n k comb` は nCk | `5 2 comb`, `5 2 ncr` |
| `perm`, `npr` | 順列の数。`n k perm` は nPk | `5 2 perm`, `5 2 npr` |
| `frac` | 分数（約分された有理数）。`a b frac` は a/b | `3 6 frac` |

## 乱数

| 演算子 | 説明 | 例 |
|---|---|---|
| `rand` | 0 以上 1 未満の乱数（float） | `rand` |
| `randint` | `a b randint` は a 以上 b 以下の整数の乱数 | `1 6 randint` |
| `uniform` | `a b uniform` は a と b の間の float の乱数 | `1 2 uniform` |
| `dice` | `n m dice` は m 面のサイコロを n 個振った目の合計 | `3 6 dice` |

## 型と変換

型判定の語は `true` / `false` を返し、判定した値は消費されます。

| 演算子 | 説明 | 例 |
|---|---|---|
| `int` | 整数に変換（小数は切り捨て、文字列は解析） | `3.7 int` |
| `float` | 浮動小数点数に変換 | `3 float` |
| `str` | 文字列に変換 | `42 str` |
| `bool` | 真偽値に変換（`0`, 空文字列, 空リストは `false`） | `1 bool` |
| `complex` | 複素数に変換 | `3 complex` |
| `type` | 値の種類をシンボルで積む: `:int` `:float` `:complex` `:fraction` `:bool` `:str` `:list` `:array` `:dict` `:symbol` `:lambda` `:null`（ブロックは引数として評価されるので、その結果の種類になる。プラグインが積んだ値はそのクラス名）。`x type :array ==` のように比べる | `42 type` |
| `int?` | 整数か。`bool` は整数ではない | `42 int?` |
| `float?` | float か | `3.14 float?` |
| `str?` | 文字列か | `"hello" str?` |
| `bool?` | 真偽値か | `true bool?` |
| `complex?` | 複素数か | `1+2j complex?` |
| `list?` | リストか。配列は `false` | `[1 2 3] list?` |
| `array?` | 配列か | `[1 2 3] array array?` |
| `dict?` | 辞書か | `dict dict?` |
| `same?` | `a b same?` は、配列・辞書なら同じ実体か。それ以外の値は `==` と同じ | `dict dup same?` |
| `number?` | 数値（整数・float・複素数）か | `42 number?` |
| `symbol?` | シンボルか。`:x` はシンボル | `:x symbol?` |
| `null?` | `null` か（空のリストは `null` ではない） | `null null?` |

## 文字列

文字列の語は新しい文字列を積み、元の文字列は残しません。

| 演算子 | 説明 | 例 |
|---|---|---|
| `concat` | 2 つの文字列を連結。`a b concat` は a の後ろに b | `"ab" "cd" concat` |
| `search` | `s sub search` は s の中で sub が最初に現れる位置（0 始まり）。無ければ `-1` | `"hello" "ll" search` |
| `contains` | `s sub contains` は s が sub を含むか。リストなら要素として含むか（`[1 2 3] 2 contains`） | `"hello" "ell" contains` |
| `replace` | `s old new replace` は s の中の old をすべて new に置換 | `"a-b-c" "-" "+" replace` |
| `split` | `s sep split` は s を sep で分割したリスト | `"a,b,c" "," split` |
| `join` | `list sep join` は文字列のリストを sep でつなぐ | `["a" "b"] "," join` |
| `lower` | 小文字にする | `"Hello" lower` |
| `upper` | 大文字にする | `"Hello" upper` |
| `title` | 各単語の先頭を大文字にする | `"hello world" title` |
| `strip` | 前後の空白を除く | `"  hi  " strip` |
| `lstrip` | 先頭の空白を除く | `"  hi  " lstrip` |
| `rstrip` | 末尾の空白を除く | `"  hi  " rstrip` |
| `asc` | 1 文字の文字コード | `"A" asc` |
| `chr` | 文字コードに対応する 1 文字 | `65 chr` |
| `format` | `template value format` は `template` の `{}` に value を埋め込む（Python の `str.format`） | `"x={}" 3 format`, `"{:.2f}" 3.14159 format` |
| `subseq` | `s a b subseq` は s の a 番目から b 番目の手前までの部分文字列（文字列専用の `slice`） | `"hello" 1 3 subseq` |
| `words` | 空白（スペース・タブ・改行）で区切った語のリスト。空の文字列は入らない | `"  a b  c " words` |
| `starts-with?` | `s p starts-with?` は s が p で始まるか | `"hello" "he" starts-with?` |
| `ends-with?` | `s p ends-with?` は s が p で終わるか | `"hello" "lo" ends-with?` |
| `encode` | `s encoding encode` は文字列をその符号化（`"utf-8"`、`"latin-1"` など）のバイトのリストに。符号化できない文字はエラー（置き換えはしない）。`"utf-16"` は BOM 付きになるので、固定したいときは `"utf-16-le"` | `"hi" "utf-8" encode` |
| `decode` | `bytes encoding decode` はバイトのリスト（配列でも）を文字列に | `[104 105] "utf-8" decode` |

`format` が埋め込める値は 1 つだけです。`join` に数値のリストは渡せません（先に `map` と `str` で文字列にします）。

## リスト

リストの書き方は [構文と値](syntax.md) を参照してください。

| 演算子 | 説明 | 例 |
|---|---|---|
| `car` | 先頭の要素。空リストはエラー | `[1 2 3] car` |
| `cdr` | 先頭を除いたリスト | `[1 2 3] cdr` |
| `cons` | `x xs cons` は xs の先頭に x を加えたリスト | `1 [2 3] cons` |
| `pair?` | 空でないリストか | `[1 2 3] pair?` |
| `seq` | `a b seq` は a から b まで（両端を含む）の整数のリスト。a が b より大きいと空 | `1 5 seq` |
| `listn` | スタックの上から n 個を 1 つのリストにまとめる。`1 2 3 3 listn` は `[1 2 3]` | `3 listn` |
| `nth` | `container i nth` は 0 始まりの i 番目の要素を積む。対象はリスト・配列・文字列・コードブロックで、`container` はスタックに残る。負の添字は末尾から | `[10 20 30] 1 nth` |
| `at` | `container i at` は i 番目の要素を積み、`container` は取り去る。対象は `nth` と同じ | `[10 20 30] 1 at` |
| `slice` | `xs a b slice` は a 番目から b 番目の手前までを、同じ種類の新しい値で積む。リスト・配列・文字列。負の添字は末尾から、範囲外は切り詰める | `[10 20 30 40] 1 3 slice` |
| `expand` | リストの要素をスタックに展開する。コードブロックはトークンごとに 1 トークンのブロックに分ける | `[1 2 3] expand`, `{a b} expand` |

## 高階関数

`map`・`filter`・`reduce` に渡すブロックは、値を 1 つ残すものにします。結果を使わず副作用だけが目的なら `dolist` を使います。ブロックと関数の詳細は [関数・ラムダ・マクロ](functions-and-macros.md) を参照してください。

| 演算子 | 説明 | 例 |
|---|---|---|
| `map` | `list f map` は各要素に f（ブロック・ラムダ・シンボル）を適用した結果のリスト。f は要素ごとに値を 1 つ残す | `[1 2 3] {2 *} map`, `[1 2 3] :sqrt map` |
| `filter` | `list f filter` は f の結果（要素ごとに値 1 つ）が真になる要素だけのリスト | `[1 2 3 4] {2 >} filter` |
| `reduce`, `fold` | `list init :acc :x {body} reduce` は init から始め、各要素を名前 x、累積値を名前 acc に束縛して body を実行し、1 つの値にまとめる | `[1 2 3] 0 :acc :x {acc x +} reduce`, `[1 2 3] 0 :acc :x {acc x +} fold` |
| `zip` | 2 つのリストを要素ごとに組にする。`[1 2] [3 4] zip` は `[[1 3] [2 4]]`。長さが違うときは短いほうに合わせる | `[1 2] [3 4] zip` |
| `apply` | `list f apply` はリストの要素をスタックに展開してから f を実行 | `[3 4] {+} apply`, `[3 4] :+ apply` |

## 配列と辞書

書き換えられる配列と辞書の語。詳しくは[配列と辞書](arrays-and-dicts.md)を参照してください。書き換える語は `!` で終わり、値を積みません（`pop!` は取り出した要素を積む）。

| 演算子 | 説明 | 例 |
|---|---|---|
| `array` | `xs array` はリスト・文字列・ブロックから配列を作る（1 段だけ） | `[1 2 3] array` |
| `array-of` | `n x array-of` は長さ n、中身 x の配列 | `5 0 array-of` |
| `at!` | `v a i at!` は a の i 番目を v にする。範囲外はエラー | `9 [1 2 3] array 0 at!` |
| `append!` | `v a append!` は a の末尾に v を足す | `4 [1 2 3] array append!` |
| `pop!` | `a pop!` は a の末尾の要素を取り除いて積む。空ならエラー | `[1 2 3] array pop!` |
| `dict` | 空の辞書 | `dict` |
| `get` | `d k get` は k の値。なければ `null` | `dict "k" get` |
| `put!` | `v d k put!` は k の値を v にする | `1 dict "k" put!` |
| `has?` | `d k has?` は k があるか | `dict "k" has?` |
| `del!` | `d k del!` は k を取り除く。なければエラー | `dict :d set 1 d "k" put! d "k" del!` |
| `keys` | キーのリスト（入れた順） | `dict keys` |
| `values` | 値のリスト（キーを入れた順） | `dict values` |

## 集約と変換

`sum`, `len`, `min`, `max`, `any`, `all` はリスト（または文字列などの反復可能な値）を 1 つ取ります。スタックの数を合計したいときは `listn` で先にリストにします。

| 演算子 | 説明 | 例 |
|---|---|---|
| `sum` | 合計 | `[1 2 3] sum` |
| `len` | 要素数・文字数。辞書はキーの数 | `[1 2 3] len` |
| `empty?` | リスト・配列・文字列・辞書が空か。`null` には使えない（`null?` を先に見る） | `[] empty?` |
| `min` | 最小値 | `[3 1 2] min` |
| `max` | 最大値 | `[3 1 2] max` |
| `any` | 真の要素が 1 つでもあるか | `[true false] any` |
| `all` | すべての要素が真か | `[true true false] all` |
| `list` | 反復可能な値（文字列・配列など）をリストにする | `"abc" list` |
| `enumerate` | 各要素を `[添字 要素]` の組にする。`[10 20] enumerate` は `[[0 10] [1 20]]` | `[3 1 2] enumerate` |
| `sorted` | 昇順に並べた新しいリスト | `[3 1 2] sorted` |
| `reversed` | 逆順にした新しいリスト | `[3 1 2] reversed` |

## スタック操作

スタックの考え方は [はじめに](getting-started.md) を参照してください。`n` を取る語は、先に `n` を取り出してから残りのスタックに作用します。位置は上から数え、1 が一番上です。

| 演算子 | 説明 | 例 |
|---|---|---|
| `drop` | 一番上を捨てる | `drop` |
| `drop2` | 上から 2 つを捨てる | `drop2` |
| `dropn` | 上から n 個を捨てる。`n dropn` | `2 dropn` |
| `dup` | 一番上を複製 | `dup` |
| `dup2` | 上から 2 つをそのまま複製（`a b` が `a b a b` になる） | `dup2` |
| `dupn` | 上から n 個をそのまま複製。`n dupn` | `2 dupn` |
| `over` | 上から 2 番目をもう一度一番上に積む（配列・辞書なら同じ実体） | `over` |
| `swap` | 上から 2 つを入れ替える | `swap` |
| `pick` | 上から n 番目をもう一度一番上に積む。`n pick`（`1 pick` は `dup` と同じ） | `3 pick` |
| `roll` | 上から n 番目を一番上へ移動（コピーではない）。`n roll` | `3 roll` |
| `rot` | 上から 3 番目を一番上へ移動（`a b c` が `b c a` になる） | `rot` |
| `unrot` | 一番上を 3 番目の位置へ移動（`a b c` が `c a b` になる） | `unrot` |
| `nip` | 上から 2 番目を取り除く | `nip` |
| `depth` | スタックの深さを積む | `depth` |
| `ins` | `index value ins` は value を、上に index 個の要素が残る位置へ挿入。`0 99 ins` は一番上に積むのと同じ | `3 99 ins` |
| `rev` | スタック全体を逆順にする | `rev` |
| `count` | 値を 1 つ取り、残りのスタックにその値がいくつあるかを積む（スタックは残る） | `2 count` |
| `clear` | スタックを空にする | `clear` |
| `disp` | スタックの内容を出力する（スタックは変わらない） | `disp` |

## 制御構文

条件分岐とループの詳細は [制御構文](control.md) を参照してください。条件にはブロックも値も渡せます。

| 演算子 | 説明 | 例 |
|---|---|---|
| `if` | `cond {body} if` は cond が真なら body を実行 | `true {"yes" echo} if` |
| `ifelse` | `cond {then} {else} ifelse` は cond に応じて then か else を実行 | `true {"yes"} {"no"} ifelse` |
| `iferror` | `{try} {handler} iferror` は try がエラーを起こしたら handler を実行 | `{1 0 /} {"caught"} iferror` |
| `try` | `{try} {handler} try` は try がエラーを起こしたら、エラーの辞書（`"kind"` と `"message"`）を積んでから handler を実行 | `{1 0 /} {"kind" get} try` |
| `throw` | `kind message throw` は自分のエラーを起こす。kind は文字列かシンボル、message は文字列 | `{"E" "boom" throw} {"message" get} try` |
| `cond` | `{c1} {r1} {c2} {r2} ... n cond` は n 組の条件と結果を順に調べ、最初に条件が真になった組の結果を実行 | `5 :x set {x 0 >} {"pos"} {true} {"other"} 2 cond` |
| `do` | `start end :name {body} do` は start から end まで（両端を含む）の整数を name に束縛して body を実行 | `1 5 :i {i echo} do` |
| `dolist` | `list :name {body} dolist` は各要素を name に束縛して body を実行 | `[1 2 3] :x {x echo} dolist` |
| `times` | `{body} n times` は body を n 回実行 | `{dup ++} 3 times` |
| `while` | `{cond} {body} while` は cond が真の間 body を繰り返す | `0 :i set {i 3 <} {i ++ :i set} while` |
| `loop` | `{body} loop` は `break` が実行されるまで body を繰り返す | `0 {1 + dup 10 > {break} if} loop` |
| `break` | 最も内側のループを抜ける。ループの外ではエラー | `0 {1 + dup 3 > {break} if} loop` |

## 定義と束縛

名前とスコープは [名前とシンボル](names-and-symbols.md)、関数・マクロ・ラムダは [関数・ラムダ・マクロ](functions-and-macros.md) を参照してください。

| 演算子 | 説明 | 例 |
|---|---|---|
| `set`, `=` | `value :name set` は value を name に束縛する。ブロックは評価されずに保存される | `3 :x set`, `3 :x =` |
| `global` | `value :name global` はグローバルスコープに束縛 | `42 :answer global` |
| `defun` | `{args} {body} :name defun` は関数を定義。呼ぶと本体が残した値を全部積む | `{x y} {x y *} :multiply defun` |
| `defmacro` | `{args} {body} :name defmacro` はマクロを定義。body は展開時に実行され、展開結果のコードを 1 つ残す | `{c b} {{c eval not {b eval} if}} {unless} defmacro` |
| `lambda` | `{args} {body} lambda` は無名関数の値を作る。`eval` で呼ぶと本体が残した値を全部積む | `{x y} {x y *} lambda` |

## 評価とコード操作

| 演算子 | 説明 | 例 |
|---|---|---|
| `eval` | コードブロック・シンボル・ラムダを実行する。文字列は先に `parse` でブロックにする | `{3 5 +} eval`, `"3 5 +" parse eval` |
| `collect` | ブロック（シンボル・ラムダも）を空のスタックで実行し、残った値をすべて 1 つのリストにして積む。変数は呼び出し側のもの | `{1 2 3} collect`, `{0 3 :i {i i *} do} collect` |
| `parse` | 文字列をコードブロックに変換 | `"3 4 +" parse` |
| `sub` | 一番上の値を、1 トークンのコードブロックで包む | `:x sub` |
| `subn` | 上から n 個の値を 1 つのコードブロックで包む | `1 2 2 subn` |
| `concat-block` | 2 つのコードブロックを連結 | `{a b} {c} concat-block` |
| `symbol` | 文字列または引用された名前からシンボルを作る | `"x" symbol` |
| `gensym` | 重複しない新しいシンボルを積む（マクロが生成するコードの一時変数用） | `gensym` |
| `macroexpand` | マクロを実行せず、展開結果を積む。`args... {name} macroexpand` | `{0 >} {"neg" echo} {unless} macroexpand` |
| `include` | 別の Stacker スクリプトを、その場のスコープで実行する（毎回。[スクリプトとファイルの取り込み](scripts.md)） | `"file.stk" include` |
| `require` | 同じファイルをインタプリタごとに 1 回だけ実行する。2 回目以降は何もしない | `"file.stk" require` |

## 入出力

| 演算子 | 説明 | 例 |
|---|---|---|
| `echo`, `print` | 値を出力して改行する（スタックには積まない） | `3 4 + echo`, `"hello" print` |
| `printc` | 値を改行なしで出力 | `"hello" printc` |
| `newline` | 改行を出力 | `newline` |
| `read` | 標準入力から 1 行読み、コードブロックとして積む（`parse` と同じ解析）。文字列として読むには `read-line` | `read` |
| `read-line` | 標準入力から 1 行を文字列で積む（末尾の改行は除く）。入力の終わりなら `null` | `read-line` |
| `read-stdin` | 標準入力の残り全部を 1 つの文字列で積む。入力の終わりなら `""` | `read-stdin` |
| `read-stdin-bytes` | 標準入力の残り全部を、バイト（0〜255 の整数）のリストで積む。`read-line` / `read-stdin` と同じ位置から続けて読める | `read-stdin-bytes` |
| `write-stdout-bytes` | `bytes write-stdout-bytes` はバイトのリスト（配列でも）を標準出力にそのまま書く | `[72 105 10] write-stdout-bytes` |

## ファイル

| 演算子 | 説明 | 例 |
|---|---|---|
| `write-to-file` | `data path write-to-file` はファイルに書き込む（既存の内容は置き換わる） | `3 "output.txt" write-to-file` |
| `append-to-file` | `data path append-to-file` はファイルの末尾に追記 | `3 "output.txt" append-to-file` |
| `read-from-file` | ファイルの内容全体を 1 つの文字列として積む | `"input.txt" read-from-file` |
| `read-bytes` | ファイル全体をバイト（0〜255 の整数）のリストで積む | `"image.png" read-bytes` |
| `write-bytes` | `bytes path write-bytes` はバイトのリスト（配列でも）をファイルに書く（置き換え）。0〜255 の整数以外の要素はエラー | `[72 105] "out.bin" write-bytes` |
| `read-lines` | ファイルの全行を、文字列のリストとして積む | `"input.txt" read-lines` |
| `file-exists` | ファイルが存在するか | `"file.txt" file-exists` |

## OS

| 演算子 | 説明 | 例 |
|---|---|---|
| `ls` | カレントディレクトリのファイル名のリストを積む | `ls` |
| `cd` | `path cd` はカレントディレクトリを変更 | `".." cd` |
| `pwd` | カレントディレクトリのパスを積む | `pwd` |
| `cat` | `path cat` はファイルの内容を出力（スタックには積まない） | `"file.txt" cat` |
| `path-join` | `a b path-join` は区切りを補ってつなぐ。右がリストなら順につなぐ（`script-dir ["data" "in.txt"] path-join`） | `"data" ["in" "x.txt"] path-join` |
| `list-dir` | ディレクトリの中の名前のリスト（名前順） | `"." list-dir` |
| `path-base` | パスの最後の要素（ファイル名） | `"a/b/c.txt" path-base` |
| `path-dir` | パスのディレクトリ部分。ディレクトリのないファイル名なら `""` | `"a/b/c.txt" path-dir` |

## 時間

| 演算子 | 説明 | 例 |
|---|---|---|
| `time` | 現在時刻をエポック秒（float）で積む | `time` |

## 終了

| 演算子 | 説明 | 例 |
|---|---|---|
| `exit` | 終了コード 0 でプログラムを終了 | `exit` |
| `abort` | 終了コード 1 でプログラムを終了 | `abort` |
| `exit-code` | `n exit-code` は終了コード n でプログラムを終了 | `1 exit-code` |

## プラグインと設定

プラグインの作り方は [プラグインと Python からの利用](plugins-and-python-api.md)、REPL の設定は [REPL とコマンドライン](repl-and-cli.md) を参照してください。

| 演算子 | 説明 | 例 |
|---|---|---|
| `disable_plugin` | `name disable_plugin` は名前の付いたプラグイン 1 つを無効にする。登録されていなければメッセージを出す | `"hoge" disable_plugin` |
| `disable_all_plugins` | すべてのプラグインを無効にする | `disable_all_plugins` |

## システム

| 演算子 | 説明 | 例 |
|---|---|---|
| `vars` | 定義済みの変数（定数を含む）を出力 | `vars` |
| `funcs` | 定義済みの関数を出力 | `funcs` |
| `macros` | 定義済みのマクロを出力 | `macros` |
| `operators` | 使える演算子の説明を一覧で出力 | `operators` |
| `version` | この Stacker の版を文字列で積む | `version` |
| `args` | コマンドラインでスクリプト名の後ろに書いた引数を、文字列のリストで積む（`stacker s.stk 200 100` なら `['200' '100']`）。REPL では `[]` | `args` |
| `script-path` | 実行中のファイルの絶対パス。取り込まれたファイルの中ではそのファイル。REPL と `-e` では `null` | `script-path` |
| `script-dir` | 実行中のファイルのディレクトリ。REPL と `-e` では `null` | `script-dir` |
| `main-script-path` | コマンドラインで実行したスクリプトの絶対パス。REPL と `-e` では `null` | `main-script-path` |
| `main?` | 実行中のコードが、コマンドラインで実行したスクリプトか。取り込まれたファイルの中では偽、REPL と `-e` では真。モジュールの末尾に `main? {args 0 at int run} if` と書くと、取り込まれたときは動かない | `main?` |
| `ans` | 値を残した最後の入力（REPL の 1 行、スクリプトの 1 式）の結果を、もう一度積む。値を残さない入力（`clear` など）では変わらない。1 つの入力の中では、その入力より前の結果を指す。まだ結果がなければエラー。`include` / `require` したファイルの中では使えない | `ans` |

REPL の `enable_disp_ans` / `disable_disp_ans` は、スタックの一番上を毎回表示するかどうかの設定です（[REPL とコマンドライン](repl-and-cli.md)）。

## prelude

prelude は Stacker 自身で書かれた標準の定義で、起動時に読み込まれます。`funcs` と `macros` の出力には `(prelude)` と付いて現れます。

| 演算子 | 説明 | 例 |
|---|---|---|
| `alias` | `{body} :name alias` は body に name という名前を付け、name を書くとその場に body を書いたのと同じに動く | `{2 ^ 3 * 5 +} {calc} alias` |
| `mean` | `list mean` はリストの平均 | `[1 2 3] mean` |

## 定数とリテラル

定数は名前で値を積む語です。`true`, `false`, `null` はリテラルで、名前ではないため再定義できません（[構文と値](syntax.md)）。

| 演算子 | 説明 | 例 |
|---|---|---|
| `e` | ネイピア数 | `e` |
| `pi` | 円周率 | `pi` |
| `phi` | 黄金比 | `phi` |
| `tau` | 2π | `tau` |
| `nan` | 非数 | `nan` |
| `inf` | 正の無限大 | `inf` |
| `true` | 真 | `true` |
| `false` | 偽 | `false` |
| `null` | 値がないことを表す値 | `null` |
