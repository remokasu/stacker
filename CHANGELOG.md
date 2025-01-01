# CHANGE LOG

## [1.8.1]

### Improvements
- **Increased Maximum Regression Iterations**: The maximum number of regression iterations has been increased.
- **Improved Token Interpretation**: Tokens enclosed in `{}` are now correctly interpreted even when there are no spaces between them.  
  Example: `{x} {x 2 ^} lambda` is now interpreted as `{x}{x 2 ^}lambda`.

### New Features
- **`frac` Command**:  
  Example: `3 4 frac` returns `Fraction(3, 4)` and displays as `3/4`.
- **File Commands**:
  - `write-to-file`: Writes specified content to a file.  
    Example: `"This is a test file." "test.txt" write-to-file`
  - `append-to-file`: Appends specified content to a file.  
    Example: `"This is a test file." "test.txt" append-to-file`
  - `read-from-file`: Reads content from a file.  
    Example: `"test.txt" read-from-file`
  - `file-exists`: Checks if a file exists.  
    Example: `"test.txt" file-exists`

### Documentation Fixes
- Fixed incorrect explanation for the `read` command in `README.md`.


## [1.8.0]

- **Breaking Changes**

  - **Modified ifelse Syntax**:

    Before: <true-expr> <false-expr> condition ifelse
    After: condition <true-expr> <false-expr> ifelse

    Note: This change is not backwards compatible with previous versions.

  - **Modified if Syntax**:

    Before: <true-expr> condition if
    After: condition <true-expr> if

    Note: This change is not backwards compatible with previous versions.

- **Bug Fixes**

  Fixed variable scope handling in recursive function processing


## [1.7.0]

- **Support for Lambda Functions**:
  - Lambda functions are now supported, enabling inline definitions and executions of anonymous functions.
  - **Example**:
    ```
    stacker:0> {x} {x 2 *} lambda
    ```

- **Enforced Symbol Naming Conventions**:
  - Symbols used as arguments in `set`, `defun`, and `defmacro` now require a `$` prefix to improve clarity and prevent naming conflicts.
  - **Example**:
    ```
    stacker:0> 123 $a set
    ```

- **New Stack Manipulation Commands**:
  - **n listn**: Converts the top n elements from the stack into a list.
  - **n tuplen**: Converts the top n elements from the stack into a tuple.
  - **extend**: Expands list and tuple objects onto the stack.

- **Input/Output Enhancements**:
  - **read**: Reads data from standard input.
  - **read-from-string**: Interprets a string as RPN expressions and reads it.

- **Bug Fixes**:
  - Resolved an issue where unnecessary values were being pushed onto the stack during function execution in sub-blocks, causing unexpected errors during recursive operations.

- **Display Command Improvement**:
  - The `disp` command has been updated to omit commas between elements, aligning with RAEL mode display conventions.

- **New Command**:
  - **abort**: Immediately terminates the program with an exit status of 1, equivalent to `exit(1)`.

- **Unified Line Endings**:
  - Line endings across files have been unified; `.gitattributes` has been updated with `* text=auto`.

- **Comment Handling Improvement**:
  - Fixed an oversight where text following a `#` in the middle of a line was not being recognized as a comment.


## [1.6.1]

### Bug Fixes
- Resolved an issue where passing arrays to user-defined functions resulted in errors.

### Breaking Changes
- Changed the macro definition command from `alias` to `defmacro`.
  - Rationale: This change aligns the macro definition syntax with the function definition syntax (`defun`).
  - Note: This modification is not backwards compatible with previous versions.

### Migration
Users will need to update their existing macro definitions:
- Old syntax: `alias`
- New syntax: `defmacro`


## [1.6.0]

### Feature Changes
- Changed debug mode startup option from `--dmode` to `--debug`
- Replaced numpy operations with math and cmath modules to reduce external library dependencies
  - Note: This changes the behavior of applying operators to iterable objects. Use the `map` function to replicate previous behavior

### Bug Fixes
- Fixed an error when inputting tuples in REPL mode. Also improved display
- Improved error detection when using undefined variables within tuples or lists

### New Features
- `sub` command: Converts the top stack element to a code block
- `subn` command: Converts elements from the top of the stack to the nth element into a code block
- Added higher-order functions: `map`, `filter`, `zip` (applicable to lists, tuples, and code blocks)
- Added aggregation functions: `any`, `all`, `sum`, `max`, `min` (applicable to lists, tuples, and code blocks)

### Breaking Changes
1. Changed method of specifying arguments in function definitions
   - New: `{arg1 arg2} { ... } $funcName defun`
   - Old: `(arg1 arg2) { ... } $funcName defun` or `[arg1 arg2] { ... } $funcName defun`

2. Quotation marks are now required for string specifications within tuples and lists
   - Correct: `("hoge" "hoge")`
   - Incorrect: `(hoge hoge)`

### Usage Examples

Higher-order functions:
~~~
stacker:0> [1 2 3] {2 *} map
[[2 4 6]]
stacker:0> (1 2 3) {2 *} map
[(2, 4, 6)]
stacker:0> {1 2 3} {2 *} map
[{2 4 6}]
~~~

Aggregation functions:
~~~
stacker:0> [true false true] any
[true]
stacker:0> [true false true] all
[false]
stacker:0> [1 2 3] sum
[6]
stacker:0> [1 2 3] max
[3]
stacker:0> [1 2 3] min
[1]
~~~


## [1.5.9] - 2024-09-16
- Fixed the `eval` command. Previously used solely for evaluating strings, it can now also evaluate block stacks and literal objects.
  - Examples:
    ```
    stacker:0> {1 2 +} eval
    [3]
    ```
    In this example, the block stack `{1 2 +}` is evaluated, and the result is pushed onto the stack.

    ```
    stacker:0> 3 eval
    [3]
    ```
    In this example, the literal object `3` is evaluated, and the result is pushed onto the stack.

- Removed the feature introduced in 1.5.8 that displayed a specific error message (StackUnderflowError) when the stack depth is less than the number of function arguments. Errors occurring during evaluation will now display as before.


## [1.5.8] - 2024-09-14
- Fixed a bug where empty blocks `{}` were not being evaluated properly.
- Added `iferror` command.
  - The `iferror` command allows users to handle errors in a more structured way. It is used in conjunction with the `try` and `catch` blocks to execute specific commands when an error occurs.
    ~~~
    {try block} {catch block} iferror
    ~~~

- Introduced a dedicated error message when the stack depth is less than the number of arguments required by a function.
  - Example:
    ```
    stacker:0> 1 +
    StackUnderflowError: Operator `+` requires 2 arguments.
    ```

## [1.5.7] - 2024-09-08
- Fixed an issue where stack-related commands were inadvertently removed from input suggestions in version 1.5.6. These commands are now correctly displayed in suggestions.

- Fixed an issue where string inputs identical to reserved keywords for constants, such as "e" for the mathematical constant approximately 2.7183, were mistakenly evaluated as the constants themselves. Now, when strings are explicitly entered, such as through quotes, they are processed as strings rather than numerical values or constants. This correction ensures that user input is handled correctly regardless of resemblance to reserved keywords.

- Add `nip` command.
  - Removes the second element from the top of the stack.
    ~~~
    stacker:0> 1 2 3
    [1 2 3]
    stacker:3> nip
    [1 3]
    ~~~

- Add `rot` command.
  - Move the third element to the top of the stack.
    ~~~
    stacker:0> 1 2 3 4 5
    [1 2 3 4 5]
    stacker:5> rot
    [1 2 4 5 3]
    ~~~

- Add `unrot` command.
  - Move the top element to the third position.
    ~~~
    stacker:0> 1 2 3 4 5
    [1 2 3 4 5]
    stacker:5> unrot
    [1 2 5 3 4]
    ~~~

- Add `over` command.
  - Copies the second element from the top of the stack.
    ~~~
    stacker:0> 1 2 3
    [1 2 3]
    stacker:3> over
    [1 2 3 2]
    ~~~

- Add `roll` command.
  - Moves the nth element to the top of the stack.
    ~~~
    stacker:0> 1 2 3 4 5
    [1 2 3 4 5]
    stacker:5> 3 roll
    [1 2 4 5 3]
    ~~~

- Add `depth` command.
  - Returns the depth of the stack.
    ~~~
    stacker:0> 1 2 3 4 5
    [1 2 3 4 5]
    stacker:5> depth
    [1 2 3 4 5 5]
    ~~~


## [1.5.6] - 2024-08-31
- Add `enable_disp_ans` and `disable_disp_ans` settings.
  - `enable_disp_ans`: This command enables the display of the last result after stack operations. It makes it easier for users to verify the outcomes of their actions.
    ~~~
    stacker:0> enable_disp_ans
    stacker:1> 3 4 +
    7
    [7]
    ~~~
  - `disable_disp_ans`: This command disables the display of the last result after stack operations. When activated, only the stack contents will be shown, providing a cleaner view.
    ~~~
    stacker:0> disable_disp_ans
    stacker:1> 3 4 +
    [7]
    ~~~

- Fixed bug in the examples.

- Fixed a bug where string concatenation using the '+' operator was not functioning correctly.

## [1.5.5] - 2024-02-15
- Added file input and output functionality.
  - Users can now read and write to files using the `read` and `write` commands.
  - Example:
    ~~~
    stacker:0> "test.txt" read
    [This is a test file.]
    stacker:1>  "This is a test file." "test2.txt" write
    ~~~

- Added input command.
  - Users can now input data from the command line using the `input` command.
  - Example:
    ~~~
    stacker:0> "Enter a number: " input
    123
    [123]
    ~~~

- Added Error display.
  - Errors are now displayed in red for better visibility

- Added the `break` command.
  - The `break` command can be used to exit a loop.
  - Example:
    ~~~
    stacker:0> 0 10 $i {i echo {break} {i 5 ==} if} do
    0
    1
    2
    3
    4
    5
    ~~~

## [1.5.4] - 2023-12-24

### Added
- Added a setting command and load at startup setting file "~/.stackerrc".
  - The setting command is as follows:
    - disable_plugin
    - disable_all_plugins
    - enable_disp_stack
    - disable_disp_stack
    - disable_disp_logo


## [1.5.3] - 2023-12-23

### Added
- Added a mode to directly evaluate RPN expressions from the command line. For example, execute as follows:
  ~~~ bash
  stacker -e "3 4 + echo"
  7
  ~~~

### Fixed
- Fixed an issue where the processing of a plugin-added operator was not reflected when it overlapped with an existing operator.



## [1.5.2] - 2023-12-19

### Added
- Added the `evalpy` command, which allows you to evaluate Python syntax.
  - This command uses the `eval` function in Python, so you can use Python syntax.
  - Please note that the specifications of the operators are different between Stacker and Python.
  - Example:
    ~~~ bash
    stacker:0> "3+5" evalpy
    [8]
    ~~~
    In this example, the string `"3+5"` is evaluated as Python syntax and the result is pushed onto the stack.

- Added the `eval` command.
  - This command is intended to evaluate Stacker syntax.
  - Example:
    ~~~ bash
    stacker:0> "3 5 +" eval
    [8]
    ~~~
    In this example, the string `"3 5 +"` is evaluated as Stacker syntax and the result is pushed onto the stack.



### Changed
- Originally, expressions inside blocks were evaluated using a new stack, and the results were passed to the main stack. However, this process has been changed so that expressions within blocks are now passed directly to the main stack for evaluation. As a result of this change, executions like "1 {dup ++} 10 times" have become possible. Previously, using 'dup' inside a block would result in a syntax error because the stack being processed within the block was independent.



## [1.5.1] - 2023-12-15

### Fixed
- Fix times command bug.

## [1.5.0] - 2023-12-12

### Changed

- The `Stack` command modification: `pop` has been changed to `drop`.

- The input format for strings has been changed to `"..."` or `'...'`. Previously, there was no distinction between non-spaced strings and symbols such as variable names, but now they will be distinctly separated.
  ~~~
  stacker:0> "abc"
  [abc]
  stacker:1> 'efg'
  [abc, efg]
  ~~~
  - This change has also changed the usage of the `eval` command.
    - Previous usage:
      ```
      stacker:0> 1+1 eval
      ```
    - New usage:
      ```
      stacker:0> "1+1" eval
      ```
      (Note: `eval` is intended to execute Python syntax, and the example uses infix notation. `eval` cannot be written in Stacker syntax.)

- An error will now be thrown when an undefined symbol is pushed.

- However, when pushing an undefined symbol in the syntax for variable definition or function definition, you can push an undefined symbol by prefixing the symbol name with a dollar sign ($).
  ~~~
  stacker:0> 0 $a set
  stacker:1> (args) {...} $funcName debun
  stacker:2> {...} $macroName alias
  ~~~

- The loop control syntax has been changed from `for` to `do`.
  
    ~~~
    0 10 $i {i echo} do
    ~~~

- When using `include`, the path to the target script file should now be specified as a string (`"..."` or `'...'`).

- The definition of commands has been moved from `stacker.py` to `lib/functions.py`, and the files have been divided into sections. However, the commands for looping and conditional branching remain in `stacker.py`.

- The `slib` directory has been added. If you place a Stacker script file (*.stk) in this directory, it will be automatically loaded at startup and the functions, macros, and variables will be available. Currently, `mean` has been added as an example.

- Functions defined in Stacker are now called `sfunction`. This is to distinguish between Stacker functions and Python functions.

### Added

- Added the ability to convert characters to ASCII codes with `asc`. Only one character can be converted at a time.
- Added the ability to convert ASCII codes to characters with `chr`. This also only converts one character at a time.
- Added test code to the `tests` directory. However, not all features are covered yet.

### Fixed
- REPL mode now displays the length of the stack instead of line numbers.
- REPL mode no longer displays commas between stack elements.

### Removed
- Removed the Japanese description (`description`).
- Removed the ability to specify a Japanese `description` when defining a plugin.
  (It was becoming too difficult to manage.)

<hr>

### (In Japanese)

### Changed

- `Stack` コマンドの変更: `pop` が `drop` に変更されました。

- 文字列の入力フォーマットが `"..."` または `'...'` に変更されました。以前は空白のない文字列と変数名等のシンボルの区別をしていませんでしたが、今後はこれらを明確に区別します。
  ~~~
  stacker:0> "abc"
  [abc]
  stacker:1> 'efg'
  [abc, efg]
  ~~~
  - この変更により、`eval` コマンドの使用方法が変更されました。
    - 以前の使用方法：
      ```
      stacker:0> 1+1 eval
      ```
    - 新しい使用方法：
      ```
      stacker:0> "1+1" eval
      ```
      (注意: `eval` はPython構文を実行することを想定しており、例では中置記法を使用しています。`eval` はStacker構文で書くことはできません。)

- 未定義のシンボルを `push` した際にエラーが発生するように変更されました。

- ただし、変数定義や関数定義の構文で未定義のシンボルを `push` する際は、シンボル名の先頭にドル記号 ($) を付けることで、未定義のシンボルを `push` することが可能です。

  ~~~
  stacker:0> 0 $a set
  stacker:1> (args) {...} $funcName debun
  stacker:2> {...} $macroName alias
  ~~~

- 繰り返し制御構文が変更され、`for` から `do` に変更されました。

  ~~~
  0 10 $i {i echo} do
  ~~~

- `include` する際には、対象のスクリプトファイルのパスを文字列 (`"..."` または `'...'`) で指定するように変更されました。
- コマンドの定義が `stacker.py` から `lib/functions.py` に移動され、項目ごとにファイルが分割されました。ただし、繰り返しと条件分岐のコマンドは `stacker.py` に残されています。
- `slib` ディレクトリが追加されました。このディレクトリに Stacker のスクリプトファイル (*.stk) を置くと、起動時に自動的に読み込まれ、関数、マクロ、変数が利用可能になります。現在は `mean` が例として追加されています。
- Stacker 上で定義した関数は `sfunction` という名称で呼ばれることになりました。これは、Stacker の関数と Python の関数を区別するためです。

### Added
- 文字をASCIIコードに変換する機能 `asc` が追加されました。一文字のみ変換可能です。
- ASCIIコードを文字に変換する機能 `chr` が追加されました。こちらも一文字のみ変換可能です。
- テストコードが `tests` ディレクトリに追加されました。ただし、まだ全ての機能を網羅しているわけではありません。

### Fixed
- REPLモードで行番号の代わりにスタックの長さを表示するように変更されました。
- REPLモードで、スタックの要素間にカンマを表示していた問題を修正し、表示しないように変更しました。

### Removed
- 日本語の説明文 (`description`) を削除しました。
- プラグイン定義時に日本語の `description` を指定する機能を削除しました。
(管理が大変になってきたので...)


## [1.4.6] - 2023-12-05

### Fixed

- Fixed an issue where errors were not being displayed when there was a problem during plugin loading.


## [1.4.5] - 2023-11-27

### Added

- Introduced macro functionality. Macros can be used with `{...} macroName alias`.
- Added the ability to include external scripts with `{path} include`.
- Added new documentation for the latest features.

### Changed
- If a `plugins` directory exists in the stacker execution directory, the application now loads plugin files from this directory at runtime.
- The command for function definition has been changed from `fn` to `defun`. (Apologies for the change. If you have any suitable name suggestions, please propose them in the issues.)



## [1.4.4] - 2023-09-12

### Added

- Added looping capabilities through `times` and `for`.
- Added conditional branching with `if` and `ifelse`.
- Introduced a script file execution mode, which is a basic feature.

  Note: These features are experimental and may cause unexpected behavior. Please refer to the README for more details.

### Changed

- Refactored the source code for better organization. The code is now divided by functionality.



## [1.4.3] - 2023-07-11

### Added

- Resolved an issue where an EOFError was thrown when using Ctrl+D to exit the interactive mode of Stacker. Now, using Ctrl+D will cleanly exit the program just as the "exit" command does.


## [1.4.2] - 2023-06-12

### Added

- `>>`: Right bitwise shift. Shifts a number to the right by the spqecified number of bits. For example, "8 2 >>" means shifting 8 (represented in bits as 1000) two bits to the right. The result would be 10 (2 in decimal).

- `<<`: Left bitwise shift. Shifts a number to the left by the specified number of bits. For example, "2 2 <<" means shifting 2 (represented in bits as 10) two bits to the left. The result would be 1000 (8 in decimal).

- `~`: Bitwise NOT. Inverts each bit (turns 1 into 0 and 0 into 1). For example, "5 ~" means performing a bitwise NOT operation on 5 (represented in bits as 101). The result would be 010 (-6 in decimal). Note: The bitwise NOT operation uses two's complement representation, and the result may be negative.

These operations are only valid for integer values.


## [1.4.1] - 2023-05-24

### Fixed

- Fixed a bug in the parser.

<hr>
## [1.4.0] - 2023-05-22

### Added

- Added the variable definition command (`set`). For instance, `a = 123` can be written as `123 a set`.

### Changed

- Changed the syntax for function definitions. Functions are now defined using the `fn` command, for instance, `(x y) {x y + 2 /} average fn`. Please note that the new syntax is not compatible with the previous one.

<hr>

## [1.3.1] - 2023-05-16

### Changed

- Changed blockstack (the range enclosed by `{...}`) to be lazily evaluated. Blockstack is evaluated when popped, and the results are expanded onto the stack.

<hr>

## [1.3.0] - 2023-05-15

### Added

- Added traceback, which prints detailed error information when an error occurs.
- Added the blockstack feature. This treats the area enclosed by `{...}` as a single block and stacks it.
- Added a debug mode command line option `--dmode` for debugging purposes.

### Changed

- `{...}` previously meant a string, but with this update, it is changed to the blockstack function. Strings can now be expressed by enclosing them in single quotes.

<hr>

## [1.2.10] - 2023-05-07

### Added

- Added new stack operations, such as:
  * `dup`: Duplicates the top element of the stack.
  * `swap`: Swaps the top two elements of the stack.

  Example:
  ~~~
  stacker:0> 1 2 3 4 5
  [1, 2, 3, 4, 5]
  stacker:1> dup
  [1, 2, 3, 4, 5, 5]
  stacker:2>
  ~~~

  ~~~
  stacker:0> 1 2 3 4 5
  [1, 2, 3, 4, 5]
  stacker:1> swap
  [1, 2, 3, 5, 4]
  stacker:2>
  ~~~
<hr>

## [1.2.9] - 2023-05-06

### Added

- Added a new plugin, matrix.py, which adds support for matrix operations.
  - Addition 加算
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> B = [5 6; 7 8]
    stacker:2> A B +
    [[[6, 8], [10, 12]]]
    ~~~

  - Multiplication 乗算
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> B = [5 6; 7 8]
    stacker:2> A B *
    [[[19, 22], [43, 50]]]
    ~~~

  - Element-wise multiplication 要素ごとの乗算
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> B = [5 6; 7 8]
    stacker:2> A B .*
    [[[5, 12], [21, 32]]]
    ~~~

  - Element-wise division 要素ごとの除算
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> B = [5 6; 7 8]
    stacker:2> A B ./
    [[[0.2, 0.3333333333333333], [0.42857142857142855, 0.5]]]
    ~~~

  - Transpose 転置
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> A '
    [[[1, 3], [2, 4]]]
    ~~~

  - Inverse matrix 逆行列
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> A inv
    [[[-2.0, 1.0], [1.5, -0.5]]]
    ~~~

  - Rank ランク
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> A rank
    2
    ~~~

  - Trace トレース
    ~~~
    stacker:0> A = [1 2; 3 4]
    stacker:1> A trace
    5
    ~~~

  - Identity matrix 単位行列
    ~~~
    stacker:0> 2 2 ones
    [[[1.0, 1.0], [1.0, 1.0]]]
    ~~~

  - Zero matrix ゼロ行列
    ~~~
    stacker:0> 2 2 zeros
    [[[0.0, 0.0], [0.0, 0.0]]]
    ~~~

  - Diagonal matrix 対角行列
    ~~~
    stacker:0> A = [[1, 2], [3, 4]]
    stacker:1> A diag
    [[1, 4]]
    ~~~

- Added a new plugin, range.py, which adds support for custom range functionality.
  ~~~
  stacker:0> 10:
  [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]

  stacker:1> (3 10):
  [[3, 4, 5, 6, 7, 8, 9]]

  stacker:2> (0 1 0.2):
  [[0.0, 0.2, 0.4, 0.6000000000000001, 0.8]]
  ~~~

- Added a new plugin, tolist.py, which adds support for converting specified ranges to lists and expanding lists.
  - tolist
    ~~~
    stacker:0> 1 2 3 4 5 6 7 8 9 10
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stacker:1> 4 8 tolist
    [1, 2, 3, 4, [5, 6, 7, 8], 9, 10]
    ~~~
  - unlist
    ~~~
    [1, 2, 3, 4, [5, 6, 7, 8], 9, 10]
    stacker:3> 4 unlist
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ~~~

### Changed

- Added numpy to requirements.txt.
- Made the following changes to stacker/stacker.py:
   * Added insert and ans operators.
   * Added a non_destructive_operator set, which includes operators that do not store their return values on the stack.
   * Updated the get_n_args_for_operator method, allowing it to retrieve the number of arguments for operators.

<hr>

## [1.2.8] - 2023-05-04

### Added

- Added support for inputting multiple arrays on a single line.

- Added a command `rev` to reverse arrays.

- Added a feature to treat the content within {...} as a string.

- Increased the variety of test cases.

### Changed

- Changed the matrix input method.
  Example:
    stacker:0> [1 2 3; 4 5 6; 7 8 9]
    [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]

- Please note that the traditional Python input method is no longer supported.

<hr>

## [1.2.7] - 2023-04-31

### Added

- Added a new matrix input method.
  Example:
    ~~~ bash
    stacker:0> [1 2 3; 4 5 6; 7 8 9]
    [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
    ~~~

- The traditional input method is still available.

  Example:
    ~~~ bash
    stacker:0> [[1,2,3], [4,5,6], [7,8,9]]
    [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
    stacker:1>
    ~~~

### Changed

  - Changed input handling to allow continuing input on a new line while entering a matrix.

  - Changed output to display colors for improved readability.
    - Different colors are used to distinguish between different types of output.

<hr>

## [1.2.5a] - 2023-04-30

### Removed

- Removed unnecessary files from the project.
  - This helps to keep the project clean and organized.

<hr>

## [1.2.5] - 2023-04-30

### Fixed

- Fixed an issue where multi-dimensional arrays could not be entered as input.
  - Users can now input multi-dimensional arrays as expected.

- Changed input evaluation from `eval()` to `ast.literal_eval()`.
  - This improves the safety and reliability of input handling.

- Corrected typos in the README.
  - Improved readability and understanding of the documentation.

<hr>

## [1.2.4] - 2023-04-24

### Added

- Added support for multi-line input within triple quotes.
  - Users can now enter multi-line input by enclosing it within triple quotes.

    Example:

    ~~~
    stacker:0> """
    stacker:0> This is a multi-line
    stacker:0> input example.
    stacker:0> """
    ['\nThis is a multi-line\ninput example.\n']
    ~~~

### Fixed
- Fix Typo in README.md

<hr>

## [1.2.3] - 2023-04-23

### Fixed

- Fixed an issue where lists and tuples could not be entered as input.
  - Users can now input lists and tuples as expected.

### Added

- Added support for binary, octal, and hexadecimal number representations.
  - Users can now input and display numbers in binary, octal, and hexadecimal formats.

<hr>

## [1.2.0] - 2023-04-22

### Added

- Introduced plugin support for extending Stacker's functionality.
  - Users can now create and install custom plugins to add new features.
  - Provided documentation and examples for creating plugins.

<hr>

## [1.0.0] - 2023-04

### Added

- Initial release of the project with core functionalities.
- Basic mathematical operations support.

<hr>