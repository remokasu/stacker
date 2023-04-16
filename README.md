# 概要

ある晴れた日、学生Aは数学の試験に挑むため、緊張しながら教室へ向かっていました。しかし、彼はある重要なものを忘れてしまっていたのです。それは、関数電卓でした。

`学生A（焦りながら）`
~~~
「先生、電卓を忘れちゃったんですが、お借りできますか？」
~~~

`教授（ニヤリと笑いながら）`
~~~
「もちろんだ。ただし、これは逆ポーランド記法の電卓だぞ」
~~~

`学生A（戸惑いつつ）`
~~~
「逆ポーランドって...？よく分かんないけど、お借りします！」
~~~

`教授（クスクス笑い）`
~~~
「心配するな。普通の電卓のようなモードにも切り替えられるからな。
（ただし切り替え方は初見では分かり難いだろうね）」
~~~

`学生A（安心しながら）`
~~~
「なるほど！ありがとうございます！！」
~~~

<br>

その試験で学生Aは泣いたという。

このプログラムは、A君のトラウマを追体験することができる。

<br>

<hr>

1. ダウンロード
~~~ bash
> git clone git@github.com:remokasu/stacker.git
~~~

2. 依存環境インストール
~~~ bash
> pip install termcolor
~~~
* windowsの場合のみ
~~~ bash
> pip install pyreadline
~~~

3. 起動
~~~ bash
> cd stacker/stacker
> python stacker.py
~~~

4. またはインストール
~~~ bash
cd stacker
> python setup.py install
~~~

* 遊び終わったら削除しましょう
~~~ bash
> python -m pip uninstall stacker
~~~

# 使い方

<hr>

## 四則演算子:
### 加算 (+)
~~~
stacker:0> 3 4 +
(ans) 7.0
~~~

### 減算 (-)
~~~
stacker:0> 5 3 -
(ans) 2.0
~~~

### 乗算 (*)
~~~
stacker:0> 3 4 *
(ans) 12.0
~~~

### 除算 (/)
~~~
stacker:0> 8 4 /
(ans) 2.0
~~~

<hr>

## 比較演算子:
###  等しい (==)
~~~
stacker:0> 3 3 ==
(ans) True
~~~

###  等しくない (!=)
~~~
stacker:0> 3 4 !=
(ans) True
~~~

###  より小さい (<)
~~~
stacker:0> 3 4 <
(ans) True
~~~

###  以下 (<=)
~~~
stacker:0> 4 4 <=
(ans) True
~~~

###  より大きい (>)
~~~
stacker:0> 5 4 >
(ans) True
~~~

###  以上 (>=)
~~~
stacker:0> 5 5 >=
(ans) True
~~~

<hr>

## 論理演算子:
### AND (and)
~~~
stacker:0> True False and
(ans) False
~~~

### OR (or)
~~~
stacker:0> True False or
(ans) True
~~~

<hr>

## べき乗演算子:
### べき乗 (^)
~~~
stacker:0> 2 3 ^
(ans) 8.0
~~~

<hr>

## 三角関数:
### 正弦関数 (sin)
~~~
stacker:0> math.pi 2 / sin
(ans) 1.0
~~~

### 余弦関数 (cos)
~~~
stacker:0> math.pi cos
(ans) -1.0
~~~

### 正接関数 (tan)
~~~
stacker:0> math.pi 4 / tan
(ans) 1.0
~~~

<hr>

## 自作関数:
### 例 1: 平方根を計算する関数 (sqrt)
~~~ bash
stacker:0> x sqrt => x 0.5 ^
stacker:1> 4 sqrt
(ans) 2.0
~~~


### 例 2: 二つの数の平均を計算する関数 (average)
~~~ bash
stacker:0>x y average => x y + 2 /
stacker:1> 2 6 average
(ans) 4.0
~~~



関数定義の構文はRPN構文っぽい独自定義の構文なので突っ込まないでくれ