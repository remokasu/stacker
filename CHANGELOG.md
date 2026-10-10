# CHANGE LOG

## [1.16.0] - 2026-10-11

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **Symbols Are A Type Of Their Own**:
  - `$name` always pushes the symbol `name`, whatever a variable `name` holds: `5 x set $x` is the symbol `x`, and a symbol never turns into a value later. The rule is now three lines long: a bare name is a reference (the value of the variable, or the word being run), `$name` and the quoted name `{name}` are the name itself, and a string is text
  - A symbol is not a string: `$x "x" ==` is false, `$x str?` is false (`symbol?` is true), and `$x 1 +` is a type error whose message shows how to write the value (`x`) or the text (`$x str`). `str` turns a symbol into its text and `symbol` turns text back into a symbol
  - `$` must be followed by a name: `$1`, `${x}`, `$"x"`, `$[1 2]` and a lone `$` are syntax errors
- **A String Is Never A Name**:
  - `5 "x" set`, `5 {"x"} set`, `"m" macroexpand`, `[1 4 9] "sqrt" map` and `[3 4] "+" apply` are errors. Write `$x` / `{x}`, or convert text with `symbol` (`"x" symbol`)
- **An Undefined Name Is An Error Where It Is Referenced**:
  - A bare name that is neither a macro, a variable, a function nor an operator used to be pushed as an undefined-symbol value that only failed when consumed. It now raises `UndefinedSymbolError` at its own position, so a typo stops where it is written. This includes a name inside a list literal (`[a b]`) and a macro argument written bare (`foo m`); write `[$a $b]` and `{foo} m` for the names themselves
- **A Lambda Held In A Variable Is A Value**:
  - Writing the name of a variable that holds a lambda pushes the lambda, like any other variable; it no longer calls it. Call it with `eval` (`3 4 multiply eval`) or `apply`, or hand it to `map` / `filter` by name (`[1 2] f map`). Functions defined with `defun` are still called by their bare name. A lambda's arguments bind code blocks raw, like a function's
- **`eval` On A Symbol Runs The Name**:
  - `$x eval` does what writing `x` does: a macro is expanded, a variable's value is pushed, a function or an operator is run. `3 4 $+ eval` is `7`, and `{+} 0 nth eval` runs `+` again (this undoes the 1.15.0 note on names taken out of a block). A block held in `b` is pushed by `$b eval`; `b eval` runs it
- **Blocks Read As Data Hand Out Symbols**:
  - `nth`, `list`, `sorted`, `reversed`, `enumerate`, `zip` and the block argument of `map` / `filter` / `reduce` / `fold` give a symbol for every name written in the block: `{x} 0 nth` is the symbol `x` and `{x y} {} map` is `{x y}`, whatever `x` and `y` hold. Write a list literal `[x y]` when the values are wanted. The aggregates (`sum`, `max`, `all`, ...) still reference the names; `len` counts tokens. `apply` evaluates its argument first, as before, and reads only a block that this evaluation leaves behind as data
  - Conversely, a value spliced into a block by `sub`, `subn`, parameter interpolation or a block-returning word becomes a token of its own kind: a symbol becomes a bare name, a string, literal or computed, becomes a string literal
- **Conditions Are Values**:
  - `if` / `ifelse` no longer look a string or symbol condition up as a variable: a symbol is true, a string is true unless empty. `0 x = $x {1} if` now runs the block; write `x {1} if` to test the variable
- **`true`, `false` And `null` Are Literals**:
  - Like `True` / `False` / `None`, they can no longer be rebound (`5 true set` is an error) and are not listed by `vars`. `pi`, `e` and the other constants are still variables
- **Argument Lists Are Checked**:
  - `defun` and `lambda` take their parameters as a block of distinct bare names, like `defmacro`: `{$a}`, `{"a"}`, a bare `$a` or a list is an error
- **Display**:
  - Every string is shown quoted, computed ones included (`"a" "b" +` shows `'ab'`); a symbol is shown bare. A code block shows its names as written, whether or not they are bound at the time
- **Python API**:
  - A name comes back as a `Symbol` object (`from stacker import Symbol`; `.name` is the text), not as a `str`. `UndefinedSymbol` is removed: catch `UndefinedSymbolError` instead of testing for the value. Plugins receive a `Symbol` for a symbol argument

### Migration

- `$x` used where its value was meant: write `x`. A lambda passed on with `$f`: write `f`
- A string used as a name (`5 "x" set`, `"sqrt" map`, `"+" apply`, `"m" macroexpand`): write `$x` / `{x}`, or `"x" symbol` when the name is built from text
- An undefined name used as data (`foo m`, `[a b]`, `{2 *} double alias`): write `{foo} m` or `$foo m`, `[$a $b]`, `{2 *} {double} alias`
- `$x` or `"x"` written as a condition to test the variable `x`: write `x`
- `$b eval` to run a block held in `b`: write `b eval`
- A lambda called by its bare name (`{x y} {x y *} lambda multiply set 3 4 multiply`): write `3 4 multiply eval`, or define it with `defun`. `[1 2] {f} map` with a lambda in `f`: write `[1 2] f map`
- `$x "x" ==`: write `$x str "x" ==`
- `{$a} {a} lambda` or `$a {a 2 *} f defun`: write `{a}`
- A block whose names were read as values by `map`, `reduce` or `list`: write a list literal `[x y]` instead of `{x y}`
- Python code that tested `isinstance(v, str)` to recognize a name: test `isinstance(v, Symbol)`. Code that looked for `UndefinedSymbol` values: catch `UndefinedSymbolError`
- To find `$name` written where a value was meant, look for `$name` that is not right before `set`, `=`, `global`, `defun`, `defmacro`, `macroexpand` or `alias`, nor the name before a `do` / `dolist` / `reduce` / `fold` block:
  ```bash
  grep -nE '\$[^[:space:]{}"]+' -r . --include='*.stk' \
    | grep -vE '\$[^[:space:]]+[[:space:]]+(set|=|global|defun|defmacro|macroexpand|alias)([[:space:]]|$)' \
    | grep -vE '\$[^[:space:]]+[[:space:]]+\{'
  ```
  (the accumulator name of `reduce` / `fold` still shows up; check those by eye)

### Added

- **`symbol`**: `"x" symbol` makes the symbol `x` from a string; `{x} symbol` from a quoted name; a symbol is returned as it is. Text that could not be written as `$name` (`"1"`, `"a b"`, `""`) is a syntax error
- **`symbol?`**: true for a symbol
- **Symbols in list literals**: `[$a $b]` is a list of two symbols
- **`StackerTypeError`**: raised (it is a `TypeError` too) when a symbol reaches a word that needs a value; the message names the symbol and the two ways to write what was probably meant
- **`Symbol`** is exported from the `stacker` package for embedding code

### Fixed

- `[3 4] 5 apply` silently did nothing; a function argument that is neither a block, a lambda nor a symbol is now a type error
- Calling a lambda with too few arguments raised a Python `IndexError`; it is a `StackUnderflowError`
- A lambda that returned nothing left a `VOID` marker on the stack
- A code block showed an unbound name quoted (`{'foo'}`) and the same name bare once a variable existed
- `5 "$x" set x` bound `x` through the text of the string, and `"$x" y set y list` read the string as `$x`
- `$x 1 +` leaked a Python `TypeError`
- `5 true set` silently replaced the constant `true`
- A bare name inside a nested list literal (`[[x 1]]`) was kept as text instead of being the variable's value
- README: the operator table named a `random` word that never existed (the word is `rand`) and described `all` / `any` with a two-argument form they never had
- The `do` loop benchmark (`0 s set 1 100000 $i {s i + s set} do`) runs about 20% faster: the argument helpers no longer look every value up in the variable scopes

## [1.15.0] - 2026-10-10

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **`defmacro` Defines Real Macros**:
  - `defmacro` now takes three arguments, `{args} {body} name defmacro`, like `defun`. The body runs when the macro is called, on its own stack and in its own scope, and must leave exactly one value: a code block is evaluated on the caller's stack, any other value is pushed. Argument names (and variables assigned inside the body) are substituted into the body's block literals, so control structures can be written in Stacker: `{c b} {{{c eval not {break} if b eval} loop}} {while} defmacro`
  - The old two-argument form `{body} name defmacro` is gone. It was a named code snippet, which is now spelled `{body} {name} alias`
  - Assignments inside a macro body are local to the macro and never change the caller's variables
- **Built-in Names Are Protected From Accidental Rebinding**:
  - A bare built-in operator name written right before `set` / `=` / `global` / `defun` / `defmacro` now runs as that operator instead of being taken as the name to bind. `{} {{2 *}} expand defmacro` used to silently define a macro named `expand`; it now runs `expand`
  - Rebinding a built-in name still works with an explicit quote: `3 $dup set` or `3 {dup} set`. Your own variables, functions and macros can be redefined by their bare name as before
- **`expand` On Code Blocks**:
  - `{1 2 +} expand` now pushes one-token code blocks `{1} {2} {+}` instead of the raw token representation (which left the operator as a string and made `{1 2 +} expand +` fail). `expand` on lists is unchanged
- **Name Positions Are Always Names**:
  - A bare name right before `macroexpand`, and the two names before the block of `reduce` / `fold`, are now read as names, like the name before `set` or the loop variable of `do`. A variable that happened to hold a name can no longer be used there by its bare name (`$m which set which macroexpand` used to expand `m`); write the name itself: `m macroexpand`, `{m} macroexpand`
- **Prelude Is Loaded By `Stacker()`**:
  - The Stacker-written standard words (`alias`, `mean`) are loaded by every new interpreter, not only by the command line, so embedding code and scripts see the same words. `Stacker(prelude=False)` gives a bare interpreter
  - On the command line the prelude is now loaded before plugins (previously after), so the prelude cannot refer to plugin words

### Migration

- Named code snippets: `{2 *} double defmacro` becomes `{2 *} {double} alias`
- Macros that need arguments: write them in the new form, e.g. `{x} {{x x +}} {twice} defmacro`
- Code that rebinds a built-in name with a bare name, e.g. `0 sum set` or `} max defun`, must quote the name: `0 $sum set`, `} {max} defun`
- Code that relied on `expand` turning a block into raw tokens should use `eval` on the pieces, or `concat-block` to build code
- Embedding code that inspected a fresh interpreter's macros or functions and expected them to be empty should create it with `Stacker(prelude=False)`
- Code that passed a macro name to `macroexpand`, or accumulator / element names to `reduce` / `fold`, through a variable should write the names directly (`m macroexpand`, `0 acc x {acc x +} reduce`)
- `eval` on an operator name taken out of a block as data (`{+} 0 nth`), or on a name wrapped with `sub` from a string (`"+" sub`), pushes it back instead of running the operator. Use `expand` or `apply` to run code taken from a block

### Added

- **`loop`**: `{body} loop` repeats a block on the current stack until `break`. It is the primitive all other loops can be written with
- **`alias`** (prelude): `{body} {name} alias` names a code snippet that runs in place on the caller's stack
- **`gensym`**: pushes a fresh unique name (prefixed `__g`) for temporaries in macro-generated code
- **`macroexpand`**: `<args> {name} macroexpand` pushes a macro's expansion without running it
- **`concat-block`**: `{a b} {c} concat-block` joins two code blocks
- **Quoted names**: `{name}` is the documented way to pass a name as a value; every word that takes a name accepts it
- **`Stacker(prelude=...)`**: Python API flag to skip loading the prelude
- Redefining a prelude word logs a warning (`redefining prelude word 'alias'`) through the standard `logging` module

### Fixed

- **Control Flow In `-e` And `Stacker.eval()`**:
  - `if`, `ifelse`, `iferror`, `times`, `while`, `do` and `dolist` evaluated their blocks on the interpreter's own stack instead of the stack they were called on, so `stacker -e "5 {dup ++} 3 times"` failed and `Stacker().eval("true {3} if")` returned an empty result. They now use the calling stack, like `cond` already did
  - `do` and `dolist` restore the enclosing scope even when the body raises
- A defined macro can be redefined by its bare name (`{} {{2}} m defmacro` used to fail with `Expected a symbol, got 1`)
- Macro recursion is stopped by the recursion guard with a `StackerRecursionError` naming the macro, instead of Python's `RecursionError`
- `{} 5 five defmacro` reports a Stacker syntax error instead of leaking an `AttributeError`
- Prelude files load in a fixed order (a manifest in the `slib` package) instead of directory-listing order
- `disp` (and the non-colored stack display) no longer deletes commas inside strings: `"Hello, World!" disp` shows `['Hello, World!']`, and booleans print as `true` / `false` like the colored display
- **String Literals Inside Code Blocks Are Literals**:
  - A string literal inside a block used to be looked up as a name when the block ran: `5 foo set {"foo"} eval` gave `5`, `3 4 {"+"} eval` added the numbers, and a macro named `foo` captured `"foo"` even at top level. A string literal now always evaluates to itself, wherever it is written
  - As a consequence, literals whose text looks like other syntax stay strings inside blocks too: `{"$x"}`, `{"[1 2]"}` and `{"{x}"}` push the strings `$x`, `[1 2]` and `{x}` (they used to be read as a symbol, a list and a block)
  - A block displays its string literals with their quotes: `{"a b" echo}` shows as `{"a b" echo}`
- `"..." eval` no longer substitutes variable values while tokenizing, so `5 x set "6 x set x" eval` rebinds `x` and gives `6`, the same as `read-from-string eval`. A lambda held in a variable is now called when its name appears in the evaluated string, as it is inside a block
- A bare literal (`5 3 set`, `5 True set`) or a quoted literal (`3 {5} set`) is never taken as a name; these report a syntax error instead of binding a variable named `3`, `True` or `5`
- `[1 2] eval` pushes the list back instead of raising a Python `TypeError`
- An undefined name given to the aggregate operators (`len`, `sum`, ...), the transforms (`list`, `sorted`, `reversed`, `enumerate`) or `zip` raises `UndefinedSymbolError` instead of being treated as the text of the name (`foo len` gave 3)
- Inside a block given to an aggregate, a string literal is a string: `5 a set {"a"} max` gives `a`, not 5, and `{"1" "2"} sum` is a type error like `["1" "2"] sum`
- A string given to an aggregate, a transform or `zip` is data even when a variable has the same name: `5 ab set "ab" list` gives `[a b]` (it used to try to list the number 5)

## [1.14.0] - 2026-08-07

### Fixed

- **Fatal Parser Errors Are No Longer Silently Swallowed**:
  - A pathological literal that overflows the Python parser (for example a token of 100,000 chained unary minuses) now raises a visible error instead of silently pushing a bogus `UndefinedSymbol` value onto the stack
  - Benign malformed literals are unaffected and still fall back to symbol resolution: `42 $x set x` returns `42`, and an undefined token like `1st` still resolves to an `UndefinedSymbol`
  - The REPL survives such errors and keeps the current stack intact

## [1.13.0] - 2026-07-10

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **Binding Forms Take Code Blocks Without Evaluating (Code Is Data)**:
  - `=`, `set`, and `global` are binding forms now: a code-block value is stored raw instead of being evaluated at assignment time, matching the README's deferred-evaluation contract (broken since 1.9.0)
  - Example: `{2 *} double_op =` stores the block; `5 double_op eval` returns `10` (previously crashed with a stack underflow)
  - Example: `{5 3 +} x =` stores the block; `x eval` returns `8` (previously `x` held the pre-computed `8`)
  - Function and lambda parameters bind block arguments raw too, so user-defined higher-order functions work: `{op a b} {a b op eval} apply2 defun` then `{+} 5 3 apply2` returns `8` (previously crashed)
  - A bare reference to a block-valued variable pushes the block unevaluated; computing operators still force blocks as before (`{1 2 +} dup +` is still `6`)

### Migration

- Code that relied on assignment-time evaluation should evaluate explicitly:
  - Before: `{5 3 +} x =` (x held `8`)
  - After: `{5 3 +} eval x =` (same result), or keep the block and use `x eval` at the point of use
- Code that passed a block to a function and relied on call-time evaluation should evaluate at the call site:
  - Before: `{[4 5 6]} test_sum` (the argument arrived as `[4 5 6]`)
  - After: `[4 5 6] test_sum`, or `{[4 5 6]} eval test_sum`

### Fixed

- **`examples/advanced/eval_examples.stk`**:
  - The dynamic code-construction example runs to completion again (it exercised exactly the pattern this change restores)

## [1.12.1] - 2026-07-10

### Fixed

- **Stack Operator Boundaries**:
  - `nip` removes the positional element instead of the first equal value (duplicates are safe now)
  - `ins` rejects out-of-range indices instead of silently wrapping around to a bogus position
  - `pick` can reach the bottom element (`4 pick` on a 4-deep stack) and large negative indices raise `PickError` instead of a misleading stack-underflow message
  - `0 roll` is a no-op (Forth ROLL semantics); negative counts raise `RollError`
- **Lambda Local Stack Leak**:
  - A lambda's internal stack no longer accumulates leftover values across calls
- **`global` with Defined Names**:
  - `10 counter global` works when `counter` already holds a value; the name was previously evaluated to its value (`examples/functions/higher_order.stk` runs again)
- **Empty-Stack Display**:
  - `disp` on an empty stack no longer emits a truncated ANSI escape sequence
- **Block Hash Contract**:
  - Equal code blocks (`{1 2 3}` and `(1 2 3)`) now hash equally and are interchangeable as dict keys
- **Comma Array Error Message**:
  - `[1, 2, 3]` raises `StackerSyntaxError` explaining that elements are space-separated, instead of leaking the internal token repr
- **`--debug` in Script Mode**:
  - Failing scripts now print the Python traceback when `--debug` is set, matching the REPL

## [1.12.0] - 2026-07-10

### Added

- **`--recursion-limit N` CLI Flag**:
  - Sets the maximum Stacker function recursion depth for the run (1-1800, default 1500)
  - Out-of-range values are rejected with an explicit error instead of being clamped
- **Include Search Order**:
  - Relative `include` paths now resolve against the including file's directory first, then the current working directory
  - Example: `python -m stacker path/to/main.stk` now finds `"lib.stk" include` next to `main.stk`, regardless of where you run from
  - Nested includes resolve each file relative to its own directory; when nothing matches, the `IncludeError` lists every tried absolute path

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **Default Recursion Limit**:
  - Infinite recursion in user-defined functions now stops with `` StackerRecursionError: Maximum recursion depth (1500) exceeded in function `name` `` instead of crashing the interpreter with a segmentation fault
  - The old `sys.setrecursionlimit(1 << 30)` is replaced by a finite backstop; extremely deep recursion that used to run (at the risk of a crash) now errors — raise the limit with `--recursion-limit` (up to 1800, bounded by the Python interpreter's own C-recursion ceiling)
- **Include Resolution Order**:
  - Scripts that relied on a relative include resolving against the current working directory while a same-named file exists next to the including script will now load the script-side file

## [1.11.0] - 2026-07-08

### Added

- **Block Comments `#| ... |#`**:
  - New nestable block-comment syntax, consumed at the lexical layer in every execution path (script, REPL, `-e`)
  - Example: `1 #| this is ignored |# 2 +` returns `3`
  - Nesting works: `#| outer #| inner |# still outer |#`
  - `#|` inside a string literal is plain content: `"a #| b"` is the string `a #| b`

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **Triple Quotes Are Always Multi-line String Literals**:
  - `"""..."""` and `'''...'''` are string literals everywhere — including at the start of a line in scripts, where they previously formed docstring-style block comments that were silently discarded
  - A triple-quoted string is one token; its newlines are preserved
  - Example: a script line `""" abc """` now pushes the string ` abc ` — and REPL, scripts, and `-e` agree
  - Single- and double-quoted strings may now also span lines (close the quote on a later line); in the REPL an open quote triggers continuation input
- **Unterminated Constructs Are Syntax Errors**:
  - Input ending inside an unclosed string, array `[`, block `{`/`(`, or block comment `#|` now raises `UnterminatedTokenError` (a `StackerSyntaxError`), with the starting line number in scripts
  - Previously the rest of the input was silently fused into one token and pushed as an undefined symbol
  - In the REPL, an unclosed string or block comment triggers continuation input instead (close the delimiter to finish)

### Migration

- Rewrite docstring-style comments to block comments:
  - Before: `"""` / `comment text` / `"""` (each on its own line)
  - After: `#|` / `comment text` / `|#`
  - The bundled `slib/sfunction.stk` has been migrated accordingly
- Scripts that accidentally relied on unterminated tokens being silently swallowed will now fail with `UnterminatedTokenError`; close the offending delimiter

### Changed

- **Evaluation-Loop Performance**:
  - Interpreter core is 2.7x faster on loop-heavy programs (`0 s set 1 100000 $i {s i + s set} do` runs in 0.37s, down from 1.00s) with no language behavior change
  - Operator dispatch now uses a unified lookup table instead of walking up to nine category dicts per operator
  - Code blocks classify their tokens once and reuse the classification across evaluations (loop bodies, function bodies, macros); list literals such as `[i i]` parse once and still re-resolve variables freshly on every evaluation
  - Dynamic semantics are preserved exactly: mid-loop redefinition via `set`/`defun`/`defmacro`, variable shadowing of operators, runtime operator overrides, error messages and error ordering all behave as before (pinned by a new semantics-freeze test suite)

## [1.10.1] - 2026-07-07

### Fixed

- **Code Block Re-evaluation**:
  - Fixed stale results accumulating when the same code block object is evaluated more than once
  - Example: `{1 2 +} dup +` now returns `6` instead of leaving an extra `3` on the stack

- **fold/reduce Exception Safety**:
  - Fixed permanent interpreter state corruption (stack type change and loop-variable leak into the surviving scope) when an exception is raised inside a `fold`/`reduce` body

- **Inline Comments in Multi-line Strings**:
  - Fixed `#` inside a string spanning multiple lines being stripped as a comment in script mode
  - Example: a string opened mid-line as `5 """ part1` and closed on the next line `part2 # more """` now keeps the `#` as string content

- **Circular Include Detection**:
  - `include` now raises `IncludeError` on circular includes instead of recursing until the interpreter crashes
  - Example: two scripts including each other now fail with `Circular include detected`

- **Hex/Octal/Binary Literals in Arrays**:
  - Fixed `0x`/`0o`/`0b` literals being silently mis-tokenized inside array literals
  - Example: `[0x1F 2]` now returns `[31 2]` instead of `[0 x1F 2]` with an undefined symbol

- **roll with Duplicate Values**:
  - Fixed `roll` removing the first equal value from the bottom instead of the element at the given depth when the stack contains duplicates

## [1.10.0] - 2026-07-06

### Added

- **`while` Loop**:
  - Repeats a code block while a condition is true
  - Syntax: `{condition} {body} while`
  - Example: `1 $i set 0 $s set {i 6 <=} {s i + $s set i ++ $i set} while` sums 1 through 6
  - `break` works inside `while` like in other loops

- **`cond` Multi-branch Conditional**:
  - Evaluates condition-result pairs in order and executes the first matching branch
  - Syntax: `{c1} {r1} {c2} {r2} ... n cond` (n = number of pairs)
  - Example: `{x 0 >} {"positive"} {x 0 <} {"negative"} {true} {"zero"} 3 cond`

- **`apply` Operator**:
  - Expands a list onto the stack and applies a function to the elements
  - Example: `[3 4] {+} apply` returns `7`
  - Works with code blocks, lambdas, and operator names

- **List Primitives**:
  - `car`: first element of a list — `[1 2 3] car` returns `1`
  - `cdr`: list without its first element — `[1 2 3] cdr` returns `[2 3]`
  - `cons`: prepend an element — `1 [2 3] cons` returns `[1 2 3]`
  - `null?`: true if the list is empty — `[] null?` returns `true`
  - `pair?`: true if the value is a non-empty list — `[1 2 3] pair?` returns `true`

- **Type Predicate Operators**:
  - `int?`, `float?`, `str?`, `bool?`, `complex?`, `list?`, `number?`
  - Example: `42 int?` returns `true` (`true int?` returns `false` — bools are not ints)

### Changed

- **Type Annotations**:
  - Added comprehensive type annotations across the engine and operators
- **Test Suite**:
  - Expanded with new test files covering `while`, `cond`, `apply`, list primitives, type operators, and advanced `defun`/`defmacro`/HOF behavior
- **Documentation**:
  - Documented `while`, clarified `break` semantics, and added the Type Operators table in README
- **Benchmarks**:
  - Removed benchmark scripts (`benchmarks/*.stk`)

### Fixed

- **`break` in Loops**:
  - Fixed `break` not reliably terminating loops
  - `break` now cleanly exits the innermost loop (`do`, `dolist`, `times`, `while`)
- **Nested Variable Scope in Loops**:
  - Fixed variable references inside nested code blocks within loops
  - Fixed code block detection in the parser
- **Code Block Evaluation in Functions and Lambdas**:
  - Fixed substack handling when evaluating code blocks inside user-defined functions and lambdas
- **Higher-order Functions with Value-less Blocks**:
  - Blocks passed to `map` / `filter` / `reduce` / `fold` must now leave a value on the stack
  - Previously `map`/`filter` crashed with an internal `TypeError`, and `reduce`/`fold` leaked `None` into the accumulator causing a confusing type error on the next step
  - Now a clear `NoValueProducedError` names the operator and suggests `dolist` for side-effect-only iteration
  - Example: `[1 2] {drop} map` reports: ``The block passed to `map` must leave a value on the stack. Use `dolist` for side-effect-only iteration.``
- **`expand` on Tuples**:
  - Fixed `expand` rejecting tuples pushed onto the stack by plugins or the Python API

## [1.9.1] - 2024-12-25

### Fixed

- **Void Function Support**:
  - Fixed critical bug where functions with no return value would crash with `IndexError`
  - Introduced `VOID` sentinel value to distinguish void functions from functions returning `None`
  - Void functions no longer pollute the stack with unnecessary values
  - Recursive void function calls no longer require `drop` operator
  - Example: `{msg} {msg echo} print defun` now works without crashing

### Changed

- **Function Return Value Behavior**:
  - Functions that produce no stack values now return `VOID` instead of crashing
  - `VOID` is not pushed to the stack, keeping stack clean
  - Explicit `None` values can still be used and will be pushed to stack normally

## [1.9.0] - 2024-12-25

### Added

- **Parentheses `()` for Code Blocks**:
  - `()` can now be used in place of `{}` for code blocks
  - Example: `(1 2 +) eval`, `(x y) (x y *) mul defun`

- **Variable Prefix `$` is Optional**:
  - Variables can be used without `$` prefix (old syntax `$x` still works)
  - `=` operator added as an alias for `set`
  - Example: `5 x =` and `x echo`

- **Global Variables**:
  - New `global` keyword for global variable declaration
  - Syntax: `value variable global`
  - Example: `0 counter global`

- **VSCode Syntax Highlighting**:
  - Syntax highlighting extension for `.stk` files
  - Auto-closing pairs, code folding, comment toggling
  - Installation: `cp -r .vscode-extension ~/.vscode/extensions/stacker-language`

### Changed

- **Performance Optimization**:
  - Improved function call performance with scope chain implementation

- **Examples Directory**:
  - Reorganized into categories: `basics/`, `functions/`, `algorithms/`, `advanced/`
  - Updated to use new syntax (no `$` prefix)

### Fixed

- Fixed comment parsing when `#` appears mid-line
- Enhanced error messages
- Fixed multiline `()` code blocks in script files


## [1.8.3]

### Bug Fixes

- **Fixed File Naming Typos**:
  - Renamed `stacker/exec_modes/excution_mode.py` to `execution_mode.py`
  - Fixed method name typo: `disp_all_valiables()` → `disp_all_variables()`
  - Fixed attribute name typo: `self.oprerators` → `self.operators` (affected 16+ locations in core.py)

- **Code Cleanup**:
  - Removed unused file `stacker/valiable.py` (all content was commented out)

### Changed

- **Improved Package Configuration**:
  - Updated `pyproject.toml` to properly specify all subpackages
  - Added explicit Python version requirement: `requires-python = ">=3.10"`
  - Updated dependency specification: `prompt-toolkit>=3.0.0`
  - Corrected `package-data` to only include actual data files


## [1.8.2]

- **Changed**

  Stopped using the deprecated pkg_resources module in favor of standard library alternatives.


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
  - **extend**: Expands list objects onto the stack.

- **Input/Output Enhancements**:
  - **read**: Reads data from standard input.
  - **read-from-string**: Interprets a string as RPN expressions and reads it.

- **Bug Fixes**:
  - Resolved an issue where unnecessary values were being pushed onto the stack during function execution in sub-blocks, causing unexpected errors during recursive operations.

- **Display Command Improvement**:
  - The `disp` command has been updated to omit commas between elements, aligning with REPL mode display conventions.

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
