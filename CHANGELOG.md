# CHANGE LOG

## [1.36.0] - 2026-11-07

### Changed

- **A loop written with its body runs inside the activation that runs it.** `do`, `dolist`, `times` and `loop` whose body is a block literal, once the body has run often enough to be compiled, make no activation for the loop or for the body: the activation's own instruction stream is swapped for the body's and back, as an arm of `if` already was. The depth they count (two levels), `break`, the errors' wording and the trace are unchanged. The loops inside a loop that 1.30.0 made a third slower run as fast as in 1.29.1 again
- **A string or an array given to a regular word takes the direct path of a compiled block.** Such a word on plain values ran directly in a compiled block since 1.29.0, but a string literal is a `String` and an array an `Array`, which went through the word runner every time. The string reaches the word as the plain `str` it holds, as the runner handed it
- **A name defined nowhere compiles as a variable read.** It was a step that raised, and the unit dropped itself as soon as the block bound that name: a function that sets a local and reads it back ran by the generic stream from its fourth call on. The name is now read as a variable, found once bound and looked up the general way, raising as before, when none is found

## [1.35.0] - 2026-11-07

### Changed

- **A macro whose body is one block literal expands once per set of arguments.** Such a body runs nothing at expansion time, so the expansion depends on the arguments alone: the machine keeps it (by the arguments' identity, up to 16 per macro) and runs the kept code where the macro is called, in the caller's scope, with the words the caller sees. `alias` and the words it makes are such macros: `{over drop} :over2 alias` runs `over2` in about a third of the time (19 → 6 µs). A macro given a new object every time stops keeping expansions after 32 misses in a row. `macroexpand` always expands anew; a redefinition and `copy()` start with nothing kept

## [1.34.0] - 2026-11-06

### Changed

- **A control word reached from Python runs by the machine.** A wrapper registered over `if`, `ifelse`, `cond`, `iferror`, `try`, `loop`, `times`, `do`, `while` or `dolist`, a subclass handler that calls the built-in, and `eval`, `collect`, `apply` and `macroexpand` reached the same way hand the word to the machine, which holds the one implementation. Such a word now leaves what the built-in leaves: the trace after a `break` is the innermost block's, and a recursion through a wrapped `if` or `ifelse` counts a level per call where it was a tail call before, since the activation that called the Python function stays under it. A value such a word read for its call already (the bounds of `do`, the count of `times`) is not read again. From Stacker code nothing changes
- **How a value is written is the language's; colors are the runtime's.** `stacker.lang.text.pieces` writes a value as `(kind, text)` pieces, one rule for `echo`, `str`, the error messages and the stack display, and `stacker.runtime.display` colors the pieces for the REPL. The language layer knows nothing of terminals
- **A script is read where it is split**: `stacker.syntax.script.read_script` reads the file whose expressions `iter_expressions` splits; the engine's own reader is gone
- Each layer's docstring says what the layer knows, and none names a layer above it

### Breaking Changes

- **Internal paths moved; the public names did not.** No alias is kept. Old → new:
  - `stacker.lang.color` → `stacker.runtime.color`
  - `stacker.lang.display` → `stacker.lang.text`, and `disp_default` → `stack_text`; `disp_colored` and `disp_stack` → `stacker.runtime.display`. The printer classes, `custom_print` and `color_map` are gone: a value's text comes from `plain_text`, `display_text` or `pieces`
  - `stacker.engine.stk_file_read.readtxt` → `stacker.syntax.script.read_script` (with `SCRIPT_ENCODING`)
- **A control word called from Python counts depth as the built-in does**: a program that recursed through a wrapped `if` or `ifelse` close to `--recursion-limit` may now reach the limit

## [1.33.0] - 2026-11-06

### Changed

- **The engine is made with its own words, and the face hands it the value words.** `stacker.operators.STANDARD` lists the tables of value words by category, in the order `operators` shows them; `Stacker.WORD_TABLES` is that set, and the root core makes its tables from it. The words, their order and their groups are unchanged
- **A block and a lambda carry their kind on the class** (`stacker_kind`, read by `stacker.lang.protocols.kind_of`), so the display, `type` and the collection words tell them without importing the engine. `stacker.lang.protocols` also holds what the lower layers read of a block and of the running core, for type checking
- **The rule of `include` and `require` is written once** (`stacker.engine.include.start_include`): the word on the machine and `Stacker.include()` / `require()` both resolve the path, catch a circular include, record the including line and make the child core by it
- No import in the package goes up the layers any more: the layer test's table of known crossings is empty
- What the words do when reached from Python (a control word wrapped and registered again, a subclass handler, a function or lambda value called from Python, a script included by the methods, a wrapped higher-order word) is pinned by tests, unchanged

### Breaking Changes

- **Internal paths moved again; the public names did not.** No alias is kept. Old → new:
  - `stacker.engine.include.SCRIPT_EXTENSION` → `stacker.syntax.script.SCRIPT_EXTENSION` (`stacker.runtime.config.script_extension_name` still re-exports it)
  - `stacker.engine.include.include_stacker_script` → `stacker.stacker.include_stacker_script`
  - `stacker.engine.manager.OperatorManager()` takes the tables of value words (`stacker.operators.STANDARD`); made with none, it holds the engine's words only
- **A `StackerCore` made directly has no value words** (its `WORD_TABLES` is empty): use `Stacker`, or a subclass that sets `WORD_TABLES`. The display shows such a core as a block, as it shows a `Stacker`; before, only a `Stacker` was shown so

## [1.32.0] - 2026-11-06

### Added

- **`from stacker import console`** gives a plugin the console module under a public name: a word that prints writes to `console.stdout()` and its output follows the interpreter's

### Changed

- **The package is in layers, and a module imports only from its own layer and the ones below.** From the bottom: the values and the errors (`stacker.data_type`, `stacker.error`), the syntax (`stacker.syntax`), the language's surroundings (`stacker.lang`: how a value is shown, a scope, the console, the recursion limit, a word's arguments), the engine (`stacker.engine`, with the words it runs itself in `stacker.engine.primitives`, `include` and the operator table), the words on values (`stacker.operators`), the face (`stacker`, `stacker.stacker`) and the runtime (`stacker.runtime`). A test reads every import in the package and refuses one against that order. The language, its output, its errors and its speed are unchanged
- The parser's own test file no longer ships in the wheel; it moved to the test suite

### Breaking Changes

- **The internal import paths moved; the public names did not.** `from stacker import Stacker, Array, Symbol, Console, StreamConsole`, `stacker.stacker.Stacker`, `stacker.error` and the command line are as before. No alias of an old path is kept. Old → new:
  - `stacker.engine.data_type` → `stacker.data_type`
  - `stacker.engine.display`, and its former name `stacker.util.disp` → `stacker.lang.display`
  - `stacker.engine.recursion`, `console`, `scope`, `generation`, `boundary`, `smacro` → the same names under `stacker.lang`
  - `stacker.operators.arguments` → `stacker.lang.arguments`; `stacker.util.color` → `stacker.lang.color`
  - `stacker.include.include` → `stacker.engine.include`; `stacker.include.stk_file_read` → `stacker.engine.stk_file_read`
  - `stacker.operators.manager` and `stacker.manager` → `stacker.engine.manager`
  - `stacker.operators.loop`, `if_else`, `hof`, `include`, `defun`, `defmacro`, `lmd`, `exit` → the same names under `stacker.engine.primitives`
  - `stacker.lib.config` → `stacker.runtime.config`; `stacker.lib.ui_tools` → `stacker.runtime.ui_tools`; `stacker.error_formatter` → `stacker.runtime.error_formatter`
  - `stacker.operators.eval`, an empty table, is gone
- **`include` is no longer in `stacker.__all__`**: it named the subpackage, not a word, and `from stacker import *` no longer brings it in

## [1.31.0] - 2026-11-06

### Changed

- **Every block that runs often is compiled**, not only one with a word that gained from it before: on the machine a compiled block's steps run with less around them than the interpreter's walk of the tokens, so a small body (`{i drop}`, an arm `{1}`) runs faster than before. `--no-compile` is unchanged
- **A block that `eval` runs in the scope it was written in runs in place**, as an arm of `if` does, instead of in an activation of its own
- **A loop enters the same activation again for the next iteration**, and `map`, `filter`, `reduce` and `fold` do the same for the next element, instead of making one each time
- **The words of a compiled block are dispatched by a kind decided once**, when the block is compiled, instead of being sorted out at every run. With the above, programs run faster than in 1.30.0 throughout, and on CPython most run in the time they took in 1.29.1 or less

### Breaking Changes

- **The body of `try` and `iferror` catches for itself** when it is a block: the word and its body are one activation where they were two, so `--recursion-limit` counts one for such a `try` (a body that is a lambda or a value still runs under the word's own activation)

## [1.30.0] - 2026-11-05

### Changed

- **Stacker runs on a machine of its own.** A function call, an arm of `if`, a loop's body, a `try`, a `map` body, a macro's expansion and an included file run as activations on a return stack the interpreter keeps itself, so the host's call stack no longer grows with a recursion written in Stacker. What a program leaves behind is unchanged: the stack, the output, the errors and their messages, the trace. A Python word that runs a block is the one place the host's depth is still used
- **Recursion goes as deep as memory allows.** The default `--recursion-limit` is 100000 (it was 1500), there is no ceiling any more, and `--recursion-limit 0` asks for no limit at all. The limit counts activations now, not calls (see Breaking Changes). The example programs run in the time they took in 1.29.1 on CPython; programs made of calls, lambdas or `map` take a fifth to a third longer there, and on PyPy most run a quarter to two fifths faster
- **A call made by the last word of a function's body is a tail call**: the body that ends with it is replaced instead of kept, so a recursion that only ever calls last runs until it is done, however deep, using no depth. An `if` arm, an `ifelse` arm, a `cond` result, an `eval` or an `apply` standing last pass the position on. The values the body had left before the call come out under the call's result, in order: `{n} {n n 0 > {n 1 - h} {} ifelse} :h defun 3 h` leaves `3 2 1 0`

### Breaking Changes

- **`--recursion-limit N` counts activations.** N is the depth of the return stack: a call, the arm of an `if` or `ifelse` it runs, a loop and its body, a `try` and its body, a macro's expansion and the run of the expansion, a block in a value's place each count one, so the same program stops at a different N than in 1.29.1 (a function whose body is one `ifelse` takes two per level). The error is named after the nearest function or macro, or after the word that ran the block when no function is on the way (`` in word `eval` ``), where the host's `RecursionError` used to leak. A macro that expands into itself says `while expanding macro` where it said `in code generated by macro`
- **An infinite tail recursion runs for ever.** `{n} {n 1 + rec} :rec defun 0 rec` used to stop with `StackerRecursionError`; the call is a tail call now and the program runs until it is interrupted (Ctrl-C at the REPL). A recursion that does something after the call still stops at the limit
- **`--recursion-limit` takes 0 or more**: 0 means no limit, and there is no upper bound (1 to 1800 before); `recursion.set_limit` does the same and refuses a negative value. `MAX_RECURSION_LIMIT`, `RECURSION_FRAMES_PER_LEVEL` and `RECURSION_BACKSTOP_MARGIN` are gone from `stacker.engine.recursion` and `stacker.lib.config`; `HOST_RECURSION_LIMIT` (46000, the depth the command line gives the host) is there instead
- The `StackerRecursionError` that says `at N calls, before the limit` (the host ran out of depth first) is raised only for a recursion that goes through a Python word called from a function; code written in Stacker alone stops at the limit

## [1.29.1] - 2026-11-04

### Fixed

- Ctrl-C ended the REPL with the host's traceback, and the stack, the variables and the definitions were lost with it. It now cancels what is being typed or run and the prompt comes back, with everything kept, including what the interrupted line had already left on the stack. Ctrl-D and `exit` end the REPL as before
- Ctrl-C printed the host's traceback when it stopped a script or `-e`. It now prints nothing; with `--debug` the traceback is still printed. The process ends the same way as before: a shell sees status 130, and a shell loop around the program stops

## [1.29.0] - 2026-11-02

### Added

- **`--no-compile` and `Stacker(compile=False)`**: run every block in the interpreter instead of compiling the ones that run often (below). The result is the same either way; the switch is for comparing the two and for narrowing a problem down

### Changed

- **A block that runs often runs compiled.** On its eighth run, a block (a loop body, the body of a function or a lambda, a block literal before a control word) is translated once into instructions in which every name is already resolved, and runs from them from then on. What a program leaves behind is unchanged: the stack, what it printed, the errors and their messages, the trace, `vars`, `break` and the recursion limit. A compiled block notices a word defined, redefined, aliased or disabled, and a variable created with a word's name, and goes back to the interpreter for that run. Measured against 1.28.1 with the same programs on one machine (min of 7 runs): on CPython 3.13, loops take 30 to 36% less time (`0 :acc set 1 100000 :i {acc i + :acc set} do acc` 343 → 221 ms), recursion 43% less (`20 fib` 254 → 144 ms), a function or lambda called in a loop 33 to 38% less, `map` and `reduce` 17% less, and the examples run one after another 42% less; on CPython 3.10, 13 to 39% less across the same programs; on PyPy 3.11, loops, recursion and calls run 11 to 21 times faster (881 → 56 ms, 531 → 35 ms, 748 → 66 ms), `while` takes 45% less time and the examples run 5 times faster. A loop whose body is one aliased word is 6 to 10% slower on CPython, and `append!` in a loop 4 to 9% slower; startup time is unchanged
  - Writing into the dictionaries that `get_macros_ref()`, `get_sfuntions_ref()` and `get_plugins_ref()` return, or into the `macros`, `sfunctions` and `plugins` attributes, does not reach a compiled block. Use `register_sfunction`, `register_macro`, `register_plugin` and `register_operator`, or pass `compile=False`
  - With `--no-compile` or `compile=False`, a recursion through `if` or `ifelse` reaches the host's own depth limit about a quarter earlier than in 1.28.1 (the `StackerRecursionError` raised `at N calls, before the limit` says 124 instead of 163 under a host limit of 1000); compiled, it stops where it did. The command line raises the host's depth, so there Stacker's own limit (`--recursion-limit`, 1500 by default) stops the recursion first, as before
- **Faster blocks, function calls and lambda calls.** Running a block in another scope, calling a function and calling a lambda each copy the block's interpreter state, and the copy is now made the way the host runs it fastest. Startup time is unchanged

### Breaking Changes

- **`Stacker.sfunc_args` is removed.** The attribute was a dictionary that nothing ever filled; reading it now raises `AttributeError`. A function's argument names are `stacker.sfunctions[name]["func"].args`

### Removed

- **The manual under `docs/` is withdrawn**: it is not ready to be read. The README is the reference

### Fixed

- A block nested inside a block literal kept plugin descriptions of its own, so `{ { "twice" disable_plugin } eval } eval` removed the plugin but `help` still listed its description. Nested blocks share the interpreter's descriptions now, at any depth
- `defun` and `lambda` accepted a body that is not a code block (`{x} 5 :f defun`), and calling the function leaked the host's error (`'int' object has no attribute 'variables'`). They refuse such a body when it is defined, as `defmacro` does: `` `defun` expects a code block as the function body, got 5. Write {args} {body} :name defun `` and `` `lambda` expects a code block as the body, got 5. Write {args} {body} lambda ``, each a `StackerSyntaxError`. `defun` warns of a redefinition only once its name, argument list and body are valid

## [1.28.1] - 2026-10-30

### Fixed

- `register_sfunction`, `register_macro`, `register_parameter` and `register_plugin` accepted `true`, `false`, `null`, `True`, `False` and `None` as names, and what they registered could never be read: a program always reads these as values. They raise the `StackerSyntaxError` that `set` raises now, naming the registration (`` `register_parameter` cannot bind `true`: it is a literal, not a variable ``)

### Changed

- Removed the module `stacker.reserved`, which held one constant that nothing read

## [1.28.0] - 2026-10-30

### Breaking Changes

- **The REPL's commands are reserved words.** `help`, `about`, `delete_history`, `enable_disp_stack`, `disable_disp_stack`, `enable_disp_logo`, `disable_disp_logo`, `enable_disp_ans` and `disable_disp_ans` were names a program could define, while the REPL took a line holding one of them as its own command first: after `{x} {x 100 +} :help defun`, `1 help` ran the function and a lone `help` showed the REPL's help. Naming anything after one is now a `ReservedWordError`, through every word that names something (`set`, `=`, `global`, `defun`, `defmacro`, `alias`, `do`, `dolist`, `reduce`, `fold`, and the argument names of functions, macros and lambdas) and through `register_sfunction`, `register_macro`, `register_parameter` and `register_plugin`. One written in a program, or after a value on the REPL's line, is a `ReservedWordError` saying it is a REPL command, where it was an undefined name
- **A REPL command is its lowercase name.** The REPL and `~/.stackerrc` took the commands in any case (`HELP` showed the help); only the lowercase names are commands and reserved now, and `HELP` is an ordinary name. The REPL takes a command with spaces around it, as `~/.stackerrc` does

### Migration

- Rename a function, variable, macro, argument, loop variable or plugin word named after a REPL command, in scripts and in plugins alike (`register_plugin("help", ...)` fails to load now): `{} {...} :help defun` becomes `{} {...} :show-help defun`
- Type the REPL's commands in lowercase: `HELP` becomes `help`
- Write the commands in `~/.stackerrc` in lowercase too: a line such as `Disable_Disp_Logo` is now an ordinary name, an error when nothing is bound to it, and an error in the rc file stops Stacker before it starts

### Added

- **`ReservedWordError`**: raised for a reserved word as above; a `StackerSyntaxError`. `try` gives `ReservedWordError` as the kind

### Fixed

- The README listed the REPL's display settings among the words of the language, left out `enable_disp_logo` and said `disable_disp_stack` shows the latest value. It describes the REPL's commands as they are now

## [1.27.2] - 2026-10-29

### Fixed

- Errors were colored when standard output was a terminal, whatever standard error was: `stacker script.stk 2> errors.txt` typed at a terminal wrote color codes into the file, and an error shown on a terminal while the output went to a file had none. Colors now follow standard error, where the errors are written
- `write-to-file` emptied the file, and `append-to-file` created a missing one, when the value could not be turned into text: they opened the file first. The text is now made before the file is opened, so the file is left as it was
- `disable_plugin` and `disable_all_plugins` left the plugins' descriptions behind, so the REPL's `help` still listed the plugins they had turned off. They remove the descriptions too now, also when they run inside a block, a function body or an included file
- The REPL completed only the names it knew when it started: a function, a variable or a macro defined at the prompt was not offered. It now offers every name it knows when it completes

## [1.27.1] - 2026-10-29

### Fixed

- A script given by a relative path that changed directory with `cd` and then failed was reported by a path that does not exist, the new directory joined with the script's name (`sub/main.stk:3: error: ...`). The path is now resolved before the script runs, so the report names the script itself

## [1.27.0] - 2026-10-29

### Added

- **`Stacker.location`**: the file, the line and that line's text the interpreter is on, so a host can tell where `run_file` stopped: the line of the expression that failed, or the line an unterminated construct started on. Example: `file, line, text = s.location`. The command line reads a failing script's line through it, and reports it as before
- **`Stacker.get_operator_groups()`**: the built-in words with their descriptions, in the groups and the order `operators` lists them, as `(key, heading, words)`; a word replaced with `register_operator` is listed with its new description. `operators` and the REPL's `help` are built from it and print what they printed before

## [1.26.2] - 2026-10-29

### Fixed

- A limit on the digits of an integer's text that a host put back after making an interpreter, as a host that reads untrusted input is advised to do, did not stay: every block, function call, `map`, branch, macro or included file the interpreter ran lifted it again. An interpreter now lifts the limit once, when it is made. With the limit put back, showing or converting an integer longer than the limit raises the host's error
- `register_operator` replacing a stack, higher-order, aggregate, transform, array and dictionary, settings or system word replaced it in the other interpreters of the same process too, not only in the one it was called on: in every one made afterwards, and in one made before as soon as it replaced a word itself. Each interpreter now has its own copy of those words, as it already had of the others

## [1.26.1] - 2026-10-29

### Fixed

- `disable_all_plugins` turned no plugin off when it ran inside a block, a function body, a branch of `ifelse` or an included file, and a function or a block made before it ran could still call the plugins. It replaced the plugin table of the part of the program it ran in with a new empty one instead of emptying the table the whole program shares. It now empties the shared table, as `disable_plugin` already did for one plugin, so `{} {disable_all_plugins} :plugins-off defun plugins-off` turns every plugin off

## [1.26.0] - 2026-10-29

### Added

- **`Stacker.run_file(path, *, main=True, restore_location=False, intercept=None)`**: runs a script file from Python as `stacker script.stk` does. Each expression is evaluated on the interpreter's own stack, so what the file leaves stays there and `ans` sees it; while the file runs it is the current file (`script-path`, relative includes, and where a function it defines says it was defined), and with `main` it is the main script (`main?`, `main-script-path`). `restore_location` puts the current file and line back once the file ends, and `intercept` skips the expressions it claims. The command line runs scripts and `~/.stackerrc` through it
- **`Stacker(console=...)`, `Console`, `StreamConsole`**: where the words that print and read go (`echo`, `print`, `disp`, `vars`, `read`, `read-line`, `read-stdin` and their kin), per interpreter. The default is the standard streams as they are when a word runs, as before, so a redirect made after the interpreter was created still applies. `exit`, `abort` and `exit-code` still raise `SystemExit`

### Changed

- The language engine no longer depends on the command line's code. `stacker.util.disp` is now `stacker.engine.display` (the old name still imports the same module), the recursion limits live in `stacker.engine.recursion` and the script extension in `stacker.include.include`; both are still importable from `stacker.lib.config`. The language itself, its output and its error messages are unchanged

## [1.25.1] - 2026-10-24

### Fixed

- An integer of more than 4300 digits could be computed (`2000 !`) but not shown, written to a file, formatted, turned to another base or read from source: the host limits the digits it converts between an integer and text, and the limit got out as the host's error; a script that only left such a number on its stack ended in error. An interpreter lifts the limit when it is made, so an integer of any size reads and shows, and `bin`, `oct` and `hex` convert an integer directly instead of through its decimal text
- The package did not ship the prelude (`stacker/slib/*.stk`), so `stacker` installed from the wheel stopped at start with `Failed to load prelude file`; the files are package data now, and a test checks that every file the interpreter reads at run time ships
- `code=` told a value that a macro or `subn` had put into a block apart from the literal that reads as it, so `[1 2 3] {mlen} macroexpand {[1 2 3] len} code=` was false while `code-text` gave the same text for both. A token and a value that are shown as the same text are the same code (a literal holding a name, `[x]`, is not compared with a value: `code=` looks nothing up)

## [1.25.0] - 2026-10-24

### Breaking Changes

- **A list typed over several lines in the REPL is one list, as it is in a script.** `[1 2` and `3 4]` on two lines gave `[[1 2] [3 4]]`: the REPL put a row separator at every line break, so a table copied from a script into the REPL silently changed shape. The line break is a space there too now, and rows are written with `;` (`[1 2; 3 4]`), the same in both. `end` on a line of its own still gives up an open list

### Added

- **`echo-err`, `print-err`, `printc-err`, `write-stderr-bytes`**: what `echo`, `print`, `printc` and `write-stdout-bytes` write to standard output, written to standard error, so a program's warnings, progress and error reports stay out of its output (a test that compares the two streams, an interpreter that must report its errors on standard error) without appending to `/dev/stderr`, which only some hosts have
- **`code-text`, `code=`, `code?`**: a block as a value, without running it. Most words run a block handed to them, so `{1 2 +} {3} ==` was true and `{"hi" echo} echo` printed `hi` and then complained. `code-text` gives the text the stack shows (`"{1 2 +}"`; `parse eval` reads it back), `code=` tells whether two blocks are the same code, token by token (a string literal and a bare name of the same text differ; `{1 2}` and `(1 2)` do not), and `code?` whether a value is a block (a lambda is not). A test of a macro can compare what `macroexpand` leaves with the code it expects
- `defun` and `defmacro` log it when they redefine a word of the program's own that another file defined (`redefining word '__call' (defined at parser.stk:62) at interp.stk:84`): a program split over files has no name spaces, so two helpers of one name silently became one, and the error showed far from either definition. A word defined again in its own file, or twice in the REPL, is left alone; a definition made in the REPL or with `-e` is reported as made outside any file
- A macro whose body sets a variable named like a built-in or prelude word logs it once (`macro 'm5' replaces the built-in word 'len' in the code it generates (its body binds a variable 'len')`): a working variable `len` in the body turned the `len` of the generated code into its value, and nothing said so where the macro was called. A parameter of such a name is left alone, since replacing it is what the template is for

## [1.24.3] - 2026-10-24

### Fixed

- `read-from-file`, `read-lines` and `cat` kept the byte order mark a file may start with (a spreadsheet's "CSV UTF-8" does), so the first heading carried an invisible character and `row "id" has?` was silently false. The mark is skipped, as it is for scripts; the stack display shows a character that shows as nothing (the byte order mark, a zero-width space, a bidirectional control) as its escape (`'\ufeffid'`) so such a difference is visible
- Standard output and input used the host's locale while scripts and files were UTF-8, so a non-ASCII value could not be printed where the locale was not UTF-8, and the error blamed the value (`` `echo` cannot use '...' ``). Both streams are UTF-8 from the command line; through the Python API, a character the output cannot carry is reported as the output's fault, naming its encoding. `read-stdin` gives line ends as a file read does (`\r\n` as `\n`)
- A `format` field could reach into the value (`"{0.__class__}" 5 format` showed the host's class). A field is `{}` or `{0}` with a format spec; a path into the value is refused by name

## [1.24.2] - 2026-10-24

### Fixed

- About fifty words that run no code of the program's own (`<`, `sin`, `asin`, `exp`, `round`, `comb`, `gcd`, `randint`, `nth`, `contains`, `parse`, `car` and the like) still leaked the host's error for a value of the wrong type or outside their range (`math domain error`, `'<' not supported between instances of 'int' and 'str'`, a bare `IndexError` from `nth`). The words that call a host function without running a block now report every host error as their own, in one place: a type error as `StackerTypeError`, a value out of range as `ValidationError`, an index past the end as `StackerIndexError`, each naming the word and showing its arguments (`` `asin` cannot use 5: math domain error ``). A lambda handed to a sequence word is refused by name like any other non-sequence. A test feeds every word every kind of value and fails if a host error ever gets out
- `cbrt` gave a complex number for a negative number (`-8 cbrt`) and an inexact root for a perfect cube (`64 cbrt` was `3.9999999999999996`); it gives the real root, exact for perfect cubes. `lcm` divided by zero for `0 0 lcm` and kept the sign of the product (`-4 6 lcm` was `-12`); it is 0 or more, `0 0 lcm` being 0
- `dupn`, `dropn`, `listn` and `subn` silently did nothing for a negative count; a count must be 0 or more. `comb`, `perm`, `ncr`, `npr`, `randint` and `dice` truncated a fraction to an integer (`5 2.9 comb` was 10); they take integers only. `roundn` with a digit count in the millions never finished; the count is limited to 1000 places either side
- A block handed to an operator as an argument that left two or more values spread them over the stack, so `10 {1 2} -` computed `1 - 2` and left the 10, while `{1 2} 10 -` left a 1 behind. An argument must be one value; a block that leaves more is an error that shows them
- Scripts and the file words were read and written in the encoding of the host's locale, so a script with a Japanese comment could not be read where that was not UTF-8, and a UTF-8 file starting with a byte order mark had the mark glued to its first word. Scripts are read as UTF-8 with the mark skipped (a file that is not UTF-8 is refused with its line), and the file words read and write UTF-8
- A value nested about 1500 levels deep (a linked list of pairs) could not be shown by `echo`, `str` or the stack display and stopped with the host's recursion error; it is reported as a value too deep to show, by name
- `-inf` and `+inf` (and `-nan`) are read as numbers, as `inf` and `nan` are, at the top level, inside a block and inside a list literal (`[inf -inf]`)

## [1.24.1] - 2026-10-23

### Fixed

- The string `";"` inside a list literal was taken for the row separator: `["x" ";" "y"]` became `[['x'] ['y']]` and `[";"]` an empty list, with no error. A string is text; only a bare `;` splits rows
- A `{` or `}` (or `(` / `)`) inside a string literal inside a block was counted as structure, so `{"{" echo}` was not a block (a function with such a body could not be defined, `{"a{b"} eval` pushed a value only the host has, a set). Brackets inside strings do not count, and a token that reads only as a host-only value (a set, a tuple) is a name, never that value
- `dolist`, `map`, `filter`, `reduce`, `fold`, `zip`, `sum`, `len`, `any`, `all`, `enumerate`, `list`, `reversed`, `car`, `cdr`, `contains`, `split` and `concat` leaked the host's message when given a number, a boolean or null in a sequence's place (`'int' object is not iterable`); each names itself and shows the value
- A function whose body nests blocks deeply (`ifelse` inside `ifelse` five or more levels) hit the host's own call-depth limit before the recursion guard, reported as a bare host error that `try` could not tell from any other. The innermost call reports it as the usual recursion error, naming the function and the depth reached, and says why it came before the limit
- `null type` gave the symbol `:null`, which could not be written in source or made with `symbol`; `:null`, `:true` and `:false` are symbols now (the bare word stays the value), so `x type :null ==` works. They still cannot be bound: `5 :null set` is refused
- A function short of arguments was reported as "Operator `g` requires 2 arguments."; it is "Function `g` ...", and one argument is "1 argument"

## [1.24.0] - 2026-10-23

### Breaking Changes

- **`try` and `iferror` put the stack back as it was when an error is caught.** What the failing block pushed is dropped and what it took is back, so the handler, or the dictionary `try` pushes, sits on exactly the stack the word began with. Until now the block's partial work stayed: `{d "price" get int d "qty" get int *} {e} {0} lambda try` left the price under the handler's 0 when the quantity could not be read, and a sum that meant to count the order as 0 was silently wrong. What was left also depended on where the block failed and whether the failing word had taken its arguments, and a function failing in the same way left nothing, so a block and a function behaved differently. What a block changed in place (an array, a dictionary, a variable) stays changed. `break` is not an error and leaves the stack as the block left it

### Migration

- A handler that read the values the failing block had pushed so far reads them from the error dictionary instead: `try` gives them under the key `"stack"` (`e "stack" get`), a copy of the stack as it was at the failure

### Added

- The error dictionary of `try` has a third key, `"stack"`: what the stack held when the error was raised. Entering `try` or `iferror` copies the stack, which costs in proportion to its depth

## [1.23.0] - 2026-10-23

### Added

- **`bit-length`, `popcount`, `trailing-zeros`**: the bits an integer needs, its one bits, and the zero bits below its lowest one bit, so a program no longer counts bits through the binary text of a number
- **`path-join` takes a list on the right**: `script-dir ["data" "x.csv"] path-join` joins every part in turn, so a path of several parts no longer needs one `path-join` per part (and cannot be short of one)
- A script, or a file read by `include` or `require`, that ends with values on its stack logs them (`1 value left on the stack at the end of main.stk: '/home/.../ps3'`): a value left behind is usually an argument too many or a result never used, which the file's own output does not show (a long value is cut short; a file included several times is logged each time). The REPL and `-e` show the stack and log nothing
- A `set` or `global` that makes a new global variable with a built-in word's name logs `redefining built-in word 'all'`, as `defun` does since 1.22.0: a global variable hides the word everywhere, a required library's functions included. A local variable (inside a function or a loop) hides it only there and is not logged

## [1.22.0] - 2026-10-22

### Added

- **`read-bytes`, `write-bytes`, `read-stdin-bytes`, `write-stdout-bytes`, `encode`, `decode`**: a file or standard input read as a list of its bytes (integers 0 to 255), bytes written back as they are, and a string turned into its bytes in an encoding (`"hi" "utf-8" encode`) or back (`[104 105] "utf-8" decode`), so a program that reads a picture or writes a compressed file no longer needs a helper outside Stacker. A byte that is not an integer 0 to 255 is refused by name and position
- **`path-join`, `list-dir`, `path-base`, `path-dir`**: two parts of a path joined with the separator (`script-dir "data.txt" path-join`), the names inside a directory in name order, and the last part or the directory part of a path. `ls` is unchanged
- **`main-script-path`, `main?`**: the script the command line ran, and whether the running code is it, so a module can end with `main? {args 0 at int run} if` and stay quiet when another script requires it. `main?` is true in the REPL and with `-e`, where `main-script-path` is null
- A `defun` or `defmacro` that gives a built-in or plugin word's name to a new word logs `redefining built-in word 'slice'`, as it already did for a prelude word. The new word still wins, so a program keeps working when a later version adds a word of the same name; the warning is what tells its author that the built-in is now hidden

### Changed

- An empty dictionary is shown as `{:}`, on the stack and in error messages, so it is told apart from an empty block `{}`. `{:}` is not a way to write one; `dict` makes it

## [1.21.0] - 2026-10-22

### Breaking Changes

- **`type` pushes a symbol.** `42 type` is `:int`, `"a" type` is `:str`, `[1] array type` is `:array`, `null type` is `:null`; the kinds are `int` `float` `complex` `fraction` `bool` `str` `list` `array` `dict` `symbol` `lambda` `null` (a block is evaluated as an argument, so `{1} type` is `:int`; a value a plugin pushed gives its class name). Shown with `echo` or `str`, the kind is its bare name: `42 type echo` prints `int` where it printed `<class 'int'>`. It used to push the host's class object, shown as `<class 'int'>` or `<class 'stacker.engine.data_type.Array'>`, which no word but `str` could use

### Migration

- A comparison of two types (`a type b type ==`) still works. Code that showed the type as text compares with a symbol instead: `x type :int ==`, or `x type str` for the name as text (`int`)

## [1.20.1] - 2026-10-22

### Fixed

- `cat` and `cd` handed their argument to the host, which reads an integer as a file descriptor: `1 cat` closed the standard output and silenced everything after it. A path must be a string, as for the file words since 1.19.1; a path that cannot be opened or changed to is reported by the word with the path and the reason (`` `cd` cannot change to `nope_dir`: No such file or directory ``)
- A lambda or a symbol handed to `if`, `ifelse`, `iferror`, `times`, `cond` or `try` in a block's place was pushed as a value, so `true f if` left the lambda on the stack and a `try` handler written as `{e} {...} lambda` swallowed the error and did nothing, while `eval`, `collect` and `apply` ran the same values. Every word that runs code now runs a lambda (with its arguments from the stack, so a `try` handler takes the error dictionary) and a symbol (as its name) the way `eval` does. Any other value is still pushed: `true 1 2 ifelse` chooses a value as before. What changes is choosing between two lambdas (`true f g ifelse` now runs the chosen one) or between two symbols (`true :a :b ifelse` now runs the chosen name; to choose the symbol itself, write `true {:a} {:b} ifelse`)
- `cond` reported too few pairs as "requires 0 arguments" and leaked the host's message for a count that is not an integer; it says how many values the pairs need (`` `cond` needs 6 values below the count (3 pairs of a condition and a result), but the stack has 2 ``) and leaves the stack as it was
- `bin`, `oct`, `hex` and `dec` raised "Invalid number format.(convert_to_base)" for every value they cannot read; each names itself and shows the value (`` `bin` expects an integer or a string such as "0b101", got 7.5 ``)

## [1.20.0] - 2026-10-19

### Breaking Changes

- **A string literal reads escapes.** `"a\tb"` is three characters, `"\"42\""` is `"42"` with its quotes, and `\\` is one backslash; the escapes are `\n` `\t` `\r` `\0` `\\` `\"` `\'` `\xNN` `\uNNNN`, in single, double and triple quotes alike. Any other escape (`\q`) is a syntax error, never left in the text. Until now a backslash stayed in the text (though it already kept `\"` from ending the string)
- **A block runs in the scope it is bound to, whichever word runs it.** `eval`, `if`, `ifelse`, `cond`, `iferror`, `times`, `loop`, `while`, `do`, `dolist`, `collect`, `apply` and `reduce` ran a block in the scope of the word's caller; `map`, `filter`, `lambda` and `defun` ran it in the scope it was written in. Every word now does the latter. A block written where it runs behaves exactly as before; a block carried somewhere else is a closure: `{x} {{x 100 +}} :mk defun 5 mk eval` is 105, `1 3 :i {{i}} do 3 listn {eval} map` is `[1 2 3]`, and a function that takes a block sees the caller's variables through it with every word. What changes is the other direction: a block made at the top level and `eval`ed inside a function no longer sees the function's variables
- **`null?` is true for null alone.** It was also true for an empty list and an empty array, so a check written for null refused an empty list handed in as a value. Whether a list, an array, a string or a dictionary has nothing in it is `empty?`
- **A plugin registered with `pass_core` reads the interpreter's own scope.** It used to see the loop variable while a `do` / `dolist` body ran, since the interpreter's scope was swapped for the iteration's; the iteration's scope now belongs to the running body alone
- **`stacker -e expr file.stk` no longer ignores `file.stk`**: with `-e`, every positional is an argument for `args`
- **`subseq` takes a start and an end.** `"hello" 1 3 subseq` is `el`; it is the string-only form of `slice`. It used to push the first whitespace-separated word of a string

### Migration

- A backslash that was meant literally is written `\\` (`"C:\\new"`); a `\"` that was meant as a backslash and a quote is `\\"`
- A block that must see a function's variables is written inside the function, or the values are passed on the stack. A block that `eval`s another block kept in a variable and expects the loop variable (`{i} :b set 1 3 :i {b eval} do`) hands the block to `do` as its body instead (`1 3 :i b do`)
- `[] null?` as an emptiness test becomes `[] empty?`; `null?` keeps its name for the null test
- `s subseq` for the first word becomes `s words 0 at`

### Added

- **`args`, `script-path`, `script-dir`**: `stacker script.stk 200 100` hands what follows the script name to the program, and `args` pushes those arguments as a list of strings (`['200' '100']`; with `-e`, every positional is one, and `--` lets an option-like argument through). `script-path` is the absolute path of the file that is running (inside an included file, that file; null in the REPL and with `-e`) and `script-dir` its directory, so a script finds the data next to it wherever it is run from
- **`read-line`, `read-stdin`**: one line of standard input as a string without its line break (null at the end), and the rest of standard input as one string. `read` keeps parsing a line as code
- **`throw`, `try`**: `kind message throw` raises an error of the program's own kind, shown where a built-in error shows its class name (`  [IllegalArgumentException]`). `{try} {handler} try` catches what `iferror` catches and runs the handler with the error on the stack as a dictionary with the keys `"kind"` and `"message"`, so a handler can tell a wrong argument from a typo and throw the error again with `e "kind" get e "message" get throw`. `break` and an exit pass through both
- **`slice`**: `xs a b slice` cuts a list, an array or a string from index a up to b into a new value of the same kind; negative indexes count from the end and an index past either end is cut off
- **`words`, `starts-with?`, `ends-with?`**: the whitespace-separated words of a string (no empty strings), and whether a string begins or ends with another
- **`empty?`**: whether a list, an array, a string or a dictionary has no elements; any other value (null included) is refused by name
- The stack shows control characters and backslashes in a string as escapes (`9 chr` is `'\t'`), and a block shows its string literals so that the text reads back as the same block; `echo` and `str` give the raw text

### Fixed

- A string inside a list literal was read by the host, twice: `["a\\b"]` held a backspace, `["a\tb"]` a tab while `"a\tb"` did not, and `["it's"]` leaked the host's syntax error. The list parser reads strings by the same rule as the rest
- `split` with an empty separator leaked the host's message; it is refused by name, pointing at `array` for the characters and `words` for the words
- Running `~/.stackerrc` left it as the current file, so the REPL and `-e` searched its directory for a relative include; the position is put back once it has run
- A host operand type error inside nested words was attributed to every enclosing word in turn (`` Operator `if` received… Operator `if` received… ``); it is attributed once

### Performance

- Every Stacker nesting level costs fewer host frames: `if` 9 to 5, `do` 8 to 5, `times` 9 to 5, `eval` 6 to 4, a function call 5 to 3, a lambda through `map` 8 to 6. The host keeps its frames in 16 KiB chunks and frees a chunk the moment it empties, so a hot loop whose call depth crossed a chunk boundary paid for a chunk on every iteration (up to 7 times slower, depending on nothing visible in the program); with narrower levels the boundary is crossed less often: in a sweep of a loop wrapped in 0 to 33 function calls, the depths that paid for a chunk went from four (11, 12, 29, 30) to two (17, 18); a depth that does pay is as slow as before. Loops themselves run at the same speed as in 1.19.1 (a loop body with a variable is bound to its iteration's scope, which costs what the fewer frames save)
- A function or lambda call no longer re-enters the host's call machinery twice, which is what bounded the recursion depth at about 2000 calls whatever the limit asked for

## [1.19.1] - 2026-10-18

### Fixed

- A list literal written inside a code block (`{["A" "B"]} eval`, a function body, a `do` body) was read by the host when the block was made, so `["A" "B"]` became a list of the one string `"AB"`, and every run of the block pushed the same list. The literal is read when the block runs, exactly as at the top level: the strings stay separate, what the top level refuses (commas, a block inside a list) is refused here too, and each run makes a fresh list
- `write-to-file`, `append-to-file`, `read-from-file`, `read-lines` and `file-exists` handed whatever they got to the host, which reads an integer as a file descriptor: `"x" 1 write-to-file` wrote to the standard output and closed it (`true` is 1 as well). A file name must be a string; anything else is refused with the word's name. A file that cannot be opened is reported by the word with the file's name and the reason (`` `read-lines` cannot open `nope.txt`: No such file or directory ``)
- `write-to-file` and `append-to-file` wrote the host's text of a value (`True`, `None`, `['a', 'b']`); they write what `str` gives (`true`, `null`, `['a' 'b']`, `{'k' 1}`), so a file written by Stacker reads as Stacker shows the value
- `do`, `seq`, `listn`, `subn`, `dropn`, `dupn`, `pick`, `roll`, `roundn`, `band`, `bor`, `bxor`, `~`, `<<` and `>>` leaked the host's message when given a float where an integer is needed (`'float' object cannot be interpreted as an integer`, `unsupported operand type(s) for &`), which is what `/` leaves. Each names itself and shows the value: `` `dropn` expects an integer, got 2.0; `int` makes an integer of a number ``
- The hint for a word written inside a list literal (`[1 dup]`) also mentions `{... dup ...} collect`, the way to build a list from words without counting them

## [1.19.0] - 2026-10-18

### Added

- **`real`, `imag`, `conj`, `arg`, `polar`**: the parts of a complex number, its conjugate and its angle, and a complex number from a length and an angle (`r t polar`). `real`, `imag` and `conj` take every number: `3 imag` is 0 and `3 real` is 3, so code need not ask whether it holds a complex number
- **`collect`**: `{...} collect` runs a block on an empty stack, in the caller's scope, and pushes everything it left as one list: `{8 5 frac 3 5 frac 0} collect`, `{0 3 :i {i i *} do} collect` is `[0 1 4 9]`. A list literal holds values only; `collect` is the way to make a list from expressions without counting them for `listn`. A symbol or a lambda without parameters is run the same way
- **`--version`**: `stacker --version` prints `Stacker 1.19.0`; the word `version` pushes the version as a string

## [1.18.1] - 2026-10-18

### Fixed

- A `do` or `dolist` body holding a code block copied that block on every iteration since 1.17.0 (each iteration has a scope of its own, and a block is bound to the scope it is pushed from), which made such loops up to twice as slow as in 1.16.0. The copy made for one iteration is bound again for the next when nothing holds it any more, which the reference count tells on the interpreters where it is exact (the count is calibrated when Stacker starts, so it is right on every version; where it cannot be known a copy is made as before). A loop body with blocks in it is now about a third slower than in 1.16.0 (it was up to twice as slow), and a lambda kept from an iteration still sees that iteration's variable
- `asc`, `chr`, `int`, `float`, `sqrt`, `log`, `log2`, `log10`, `sorted`, `min`, `max`, `format` and the arithmetic words (`+` `-` `*` `/` `//` `%` `^` `++` `--`) leaked the host's message when given a value they cannot use (`ord() expected a character`, `invalid literal for int()`, `math domain error`, `can only concatenate str`, `'<' not supported between instances of 'String' and 'int'`). Each names itself and shows the value as the stack does: `` `asc` expects a string of one character, got 'abc' ``, `` `int` cannot read 'x' as an integer ``, `` `sqrt` expects a number of 0 or more, got -1 ``, `` `sorted` cannot compare 1 with 'a' ``, `` `+` cannot use 'a' and 1 together; to join text, make both values strings with `str` ``. A value outside a word's domain (`-1 sqrt`, `0 log`, `-1 chr`, `[] min`) is a `ValidationError`; a template given to `format` that asks for more than its one value is a `StackerIndexError`
- A symbolic word written inside a list literal (`[1 2 +]`, `[1 2 ^]`) was reported as "Unexpected token"; it gets the same explanation as a named word (`[1 dup]`): a list literal holds values only, build the list on the stack and collect it with `listn`

## [1.18.0] - 2026-10-17

### Added

- **Arrays And Dictionaries You Can Change In Place**:
  - `[1 2 3] array` makes an array: like a list, but its elements can be changed where it stands. `5 0 array-of` makes one of five zeros. A list stays a value that never changes; `a list` turns an array back into a list
  - Words that change an array or a dictionary end in `!`: `v a i at!` stores v at index i, `v a append!` adds v at the end, `a pop!` takes the last element off and pushes it
  - `c i at` pushes element i and takes the container off the stack (`nth` leaves it there); it reads lists, strings and blocks too
  - `dict` makes an empty dictionary. `v d k put!` stores v under key k, `d k get` pushes its value (`null` when k is not there), `d k has?` tells whether k is there, `d k del!` removes it, and `d keys` / `d values` give lists in the order the keys were added. A key is a string, a number or a symbol
  - An array or a dictionary is one thing however it is passed around: `dup`, a variable, a function argument or a list element refers to the same one, and a change made through any of them is seen through all. `a b same?` tells whether two are the same one; `==` compares contents (two different ones that contain themselves cannot be compared that way)
  - An array is shown like a list, `[1 2 3]`, in a color of its own in the REPL (`array?` tells for sure); a dictionary as `{'a' 1 'b' 2}`. One inside itself, or nested too deep, shows as `[...]` / `{...}`
  - Words that only read (`len`, `nth`, `dolist`, `map`, `sorted`, ...) take arrays as they take lists; the ones that make a new sequence make a list. `dolist`, `map` and the like go through the elements an array had when they started. A dictionary is not a sequence: those words say to go through its keys
  - `array?`, `dict?`; `list?` is false for an array
  - From Python, an array is an `Array` (a `list` subclass, `from stacker import Array`) and a dictionary a `dict`, the same objects the interpreter holds
  - New errors `StackerIndexError` (an index out of range, `pop!` on an empty array) and `KeyNotFoundError` (`del!` of a missing key)
- Messages that called a list an array now call it a list (`Unterminated list starting at line 3`, `Commas are not used in Stacker lists`)

## [1.17.0] - 2026-10-17

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **`include` Runs The File In Place**:
  - An included file runs in the interpreter that includes it, in the scope where `include` is written, as if its text stood there. Nothing is copied: the variables, functions and macros it defines are the ones the includer sees afterwards. Until now the file ran in an interpreter of its own and copies of its definitions were added, so a variable read after `include` was a snapshot that the file's own functions no longer updated, and a second `include` of the same file split its state in two
  - The file sees what is already defined: its functions can call the includer's functions and those of other included files, and it uses the includer's plugins and the prelude words the includer redefined
  - The file runs every time it is included. A file that sets up state (`0 :counter set`) sets it up again on a second `include`; read such a file with `require`
  - Names are shared: a variable the file sets, at its top level or inside its functions, is the includer's variable of that name when there is one
  - Inside a function, the variables an included file makes are local to that call; its functions and macros are global, as always
  - When the file fails part way, what it defined before the error stays defined
  - Each expression of an included file is read as a script reads it, so the file means the same whether it is run or included
  - A script that includes itself fails at once, before running a second time. `ans` cannot be used inside an included file
- **`;` Wraps Every Row**:
  - In a list literal, `;` ends a row and every row becomes a list, whatever it holds: `[a b; c]` is `[[a b] [c]]`. A row that held one list used to be that list itself, so `[[1 2] [3 4]; [5 6]]` was `[[[1 2] [3 4]] [5 6]]`; it is `[[[1 2] [3 4]] [[5 6]]]`. Write `[[1 2; 3 4] [5 6; 7 8]]`, without the outer `;`, for a list of matrices
  - A `;` before the closing bracket is no longer dropped by the REPL and the script reader: `[1 2 3;]` is the one-row matrix `[[1 2 3]]` wherever it is written (it was `[1 2 3]` at the end of a REPL or script line and `[[1 2 3]]` elsewhere). A trailing `;` after the last row still adds nothing: `[1 2 3; 4 5 6;]` is two rows
- **Each Iteration Of `do` And `dolist` Has A Scope Of Its Own**:
  - A lambda or block made in the body and kept past the iteration sees that iteration's loop variable: `1 3 :i {{} {i} lambda} do 3 listn {eval} map` is `[1 2 3]` (every lambda used to see the last value, 3). A variable first set in the body still outlives the loop
- **A Function Returns Every Value Its Body Leaves**:
  - A function defined with `defun`, and a lambda called with `eval` or `apply`, push every value their body leaves, in order; a body that leaves nothing pushes nothing. Until now only the top value was pushed and the others were dropped without a word
  - Example: `{a b} {b a} :swap2 defun 1 2 swap2` leaves `2 1` (was `1`); `{n} {n 0 > {n 1 - h n} if} :h defun 3 h` leaves `1 2 3` (was `3`)
  - `map` and `filter` need the function, block or lambda to leave exactly one value for each element, and the block of `reduce` / `fold` exactly one value per step. Leaving none is a `NoValueProducedError` as before; leaving several is a `ResultCountError` (a block given to `map` used to collect them into a list, and `reduce` kept the bottom one)
  - Called from Python, a function or a lambda returns the list of the values its body leaves; the `stack` attribute of `StackerFunction` and `StackerLambda` (their former working stack) is gone

### Added

- **`require`**: `"lib.stk" require` runs a file like `include` the first time, and does nothing when the same file is required again in the same interpreter, however its path is written. A file already run by `include` is not run again by `require`; a file that failed part way is not recorded and runs again next time. `require` binds at the top level wherever it is written. `Stacker.require(path)` does the same from Python
- **Errors Inside Included Files Say Where**: an error inside an included file is reported at the line of that file, followed by the lines that included it:
  ```text
  /home/user/project/lib/helpers.stk:2: error: `total` is not defined.
    [UndefinedSymbolError]
    | 
  2 | 10 total +
    included from /home/user/project/lib/geometry.stk:1
    included from /home/user/project/main.stk:1
  hint: To use the name itself, write `:total` or `{total}`
  ```
  The REPL and `-e` show the same without the line of the entry. From Python, the exception carries `include_location` (file, line, source line) and `include_frames`; its message is unchanged
- **`ResultCountError`**: raised when a function, lambda or block leaves more than one value where one is read

### Migration

- A library that keeps state and is read from more than one file: read it with `require` in every file that reads it
- An included file that used a temporary name at its top level (`0 :i set`) changes the includer's variable of that name: rename it, or move the code into a function
- A file that called a prelude word the includer redefines: the file now gets the redefinition
- A function whose body leaves something below its result (a value it did not use up) now hands that to the caller too: drop it in the body. It shows up as an extra value on the stack, or as an argument error further on
- To return several values as one, collect them in the body (`2 listn`) and spread them with `expand`, as before
- A block given to `map` that left several values per element to get a list of them: collect them in the block (`{dup 2 listn} map`)
- Python code that called a `StackerFunction` or a `StackerLambda` and used its return value: the value is now a list of the results (`[0]` for a one-value function)
- `[1 2 3;]` at the end of a REPL or script line to get `[1 2 3]`: drop the `;`. A matrix of matrices written as `[[1 2; 3 4]; [5 6; 7 8]]`: drop the `;` between them, `[[1 2; 3 4] [5 6; 7 8]]`

## [1.16.1] - 2026-10-17

Some fixes change what existing code does; they are bugs, not new behavior, and are listed under Breaking Changes as well.

### Breaking Changes

- **Behavior Fixed Under Bug Reports** (each is a bug, listed again under Fixed; here because code written around the old behavior changes meaning):
  - `split` pushes one list, not the parts one by one: `"a,b,c" "," split` leaves `['a' 'b' 'c']`. Code that counted the parts with `depth` or collected them with `listn` gets a list inside a list
  - `echo`, `print`, `printc`, `str` and `format` write `true` / `false` / `null`, a symbol and a list in Stacker's notation (`true`, `null`, `a`, `[1 'a']`), not the host's (`True`, `None`, `Symbol('a')`, `[1, 'a']`). Text that compared against the old spelling (`true str "True" ==`) changes
  - A variable first `set` in the body of `do`, `dolist`, `reduce` or `fold` stays after the loop, as in `while`, `times` and `loop`
  - A list literal keeps its nesting: `[[1 2]]` is a list holding one list, `[[]]` a list holding an empty list, and `[1 2 3;]` written inside an expression (not at the end of a REPL or script line, where the `;` before `]` is dropped) is one row, `[[1 2 3]]`
  - A code block that leaves nothing, handed to a word as an argument (`{} echo`, `{"x" echo} 1 +`), is an error, not a value
  - `-e` reports an error on stderr, like a script does, not on stdout
  - `abort` and `exit-code` end the program, as documented; code that ran past them does not run any more

### Migration

- `split` followed by code that gathered the parts (`depth :d set ... split depth d - listn`): drop the gathering, the result is already a list. For the parts on the stack, write `split expand`
- Output compared against `True` / `None` / `[1, 2]`: compare against `true` / `null` / `[1 2]`
- A loop body that reused a temporary name and relied on it being dropped: the name now stays in the enclosing scope (inside a function it is still local to the function)
- `[[1 2]]` written to get `[1 2]`: write `[1 2]`

### Fixed

- A lambda made inside a function call saw the variables of the latest call of that function, not of the call that made it: after `{n} {{x} {x n +} lambda} :adder defun 10 adder :add10 set 20 adder :add20 set`, `5 add10 eval` gave 25. A block is bound to the scope it is written in when it is pushed, so `5 add10 eval` is 15 and a lambda or a `map` body made in a recursive call keeps that call's variables
- A block handed to `map` or `filter` was deep-copied, interpreter and all, once per element: `[1 2 3] {1 +} map` took 100 times longer than the same with a lambda, and grew with the number of variables; an assignment inside the block was lost with the copy. The block runs as it is, in the caller's scope: `0 :c set [1 2 3] {drop c 1 + :c set 0} map drop c` is 3
- A variable first `set` in the body of `do`, `dolist`, `reduce` or `fold` was gone after the loop (`1 3 :i {i :last set} do last` was "`last` is not defined"), unlike in `while`, `times` and `loop`. It stays, as the docs describe; only the loop variable is dropped
- `[[1 2]]` was read as `[1 2]`: a list literal whose only element is a list lost its outer brackets, however deep (`[[[1 2]]]` too, and `[[]]` was `[]`). The nesting is kept as written
- `abort` and `exit-code` did nothing: `3 exit-code` went on with the next word and exited 0, and left the 3 on the stack. They exit with their status (`exit-code` needs an integer)
- `split` pushed the parts one by one (`"a,b,c" "," split` left `'a' 'b' 'c'`); it pushes one list, as described (`['a' 'b' 'c']`). Write `split expand` for the parts
- `echo`, `print`, `printc`, `str` and `format` wrote `true`, `null`, a symbol and a list as the host writes them (`True`, `None`, `Symbol('a')`, `[1, 'a']`); they write them as the stack display does (`true`, `null`, `a`, `[1 'a']`). A string is still written bare, and a number keeps its type in `format` (`"{:.2f}" 3.14159 format`)
- A code block that left nothing, handed to a word as an argument, leaked the interpreter's own "no value" marker: `{} echo` printed `VOID`, `{} str` made the string `'VOID'`, `{"x" echo} 1 +` failed on `'VoidType'`. It is a `NoValueProducedError` ("The block passed to `echo` left nothing on the stack"). `apply` with an empty argument block applies the function to nothing
- `-e` printed its error on stdout, with a caret that always pointed at the last word of the expression. It reports like the REPL does, on stderr, with the error type and a hint, and no caret
- `listn` / `subn` with fewer values than the count asked for said "`listn` requires 1 arguments" and dropped the values it had taken. The message says how many values it needs and how many the stack has, and the stack is left as it was
- A string word given the wrong type leaked the host's message (`5 upper` → "'int' object has no attribute 'upper'", `[1 2 3] 2 search` → "'list' object has no attribute 'find'"); the error names the word and shows the value (`` `search` expects a string to search in, got [1 2 3] ``). `join` on a list of numbers says to make them strings first (`{str} map`); `nth` on a value that is not a list, a string or a block, or with a non-integer index, names itself; the hint for an index error no longer suggests `[]`
- A word written inside a list literal (`[1 dup]`) was reported as "`dup` is not defined" with a hint to write `:dup`; it is a syntax error that says a list literal holds values only and how to build the list on the stack (`listn`)

## [1.16.0] - 2026-10-15

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **Names Are Written `:name`**:
  - Tokens are read one at a time, left to right, and nothing looks ahead: a bare name is always a reference, wherever it stands. The name a word binds is written `:name` (or `{name}`)
  - Until now the name right before `set` / `=` / `global` / `defun` / `defmacro` / `macroexpand`, the loop variable of `do` / `dolist` and the two names before a `reduce` / `fold` block could be written bare
  - Example: `4 :x set`, `{a b} {a b +} :add defun`, `1 10 :i {i echo} do`, `[1 2 3] 0 :acc :x {acc x +} reduce`
  - Example: `4 x set` now fails with `` `x` is not defined `` (and a hint to write `:x`); if `x` is defined, `set` is handed its value and fails with `` `set` expects a name, got 5 ``
  - Every word that takes a name takes it this way, built in or not: `{2 *} :double alias` and `{2 *} :dup alias` both work
  - Code means the same however it is split: `{4 :x} {set} concat-block eval` and `{4 :x} eval {set} eval` both bind `x`
  - The 1.15.0 protection of built-in names is gone. A bare `dup` runs, so `3 dup set` runs `dup` and `set` then fails; `3 :dup set` makes `dup` a variable holding 3 that shadows the built-in word, as before
  - A bare name that holds a name binds that name: after `:y :x set` (or `{y} :x set`), `7 x set` binds `y`. A computed name works too: `1 10 "i" symbol {i echo} do`
  - In a macro body, `:t` is replaced by the name `t` holds, so a generated name is bound as `:t set`: `{x} { gensym :t = { x eval :t set t t + } } {double!} defmacro`
- **Symbol Prefix `:`**:
  - `:x` is the name `x` as a value. `$` is gone: a token starting with `$` is a syntax error that points at the new spelling. Strings are unaffected (`"$100"` is still a string)
- **Symbols Are A Type**:
  - `:name` always pushes the symbol `name`, whatever a variable `name` holds, and a symbol never turns into a value later
  - Example: `5 :x set :x` is the symbol `x`
  - A symbol is not a string: `:x "x" ==` is false, `:x str?` is false, `symbol?` is true, and `:x 1 +` is a type error whose message shows how to write the value (`x`) or the text (`:x str`). `str` gives a symbol's text; `symbol` turns text into a symbol
  - `:` must be followed by a name: `:1`, `:{x}`, `:"x"`, `:[1 2]`, `::x` and a lone `:` are syntax errors. A name holds no `:`, `$`, quote, bracket, `#` or `;`, so every symbol can be written back as `:name`
- **Strings Are Not Names**:
  - `5 "x" set`, `5 {"x"} set`, `"m" macroexpand`, `[1 4 9] "sqrt" map` and `[3 4] "+" apply` are errors
  - Write `:x` / `{x}`, or convert text with `symbol` (`"x" symbol`)
- **Undefined Names Fail Where They Are Written**:
  - A bare name that is neither a macro, a variable, a function nor an operator raises `UndefinedSymbolError` at its own position; it used to be pushed as an undefined-symbol value that failed only when consumed
  - This includes a name inside a list literal (`[a b]`) and a macro argument written bare (`foo m`); write `[:a :b]` and `{foo} m` for the names themselves
- **A Lambda In A Variable Is A Value**:
  - Writing the variable's name pushes the lambda; it no longer calls it. Call it with `eval` (`3 4 multiply eval`) or `apply`, or hand it to `map` / `filter` by name (`[1 2] f map`)
  - Functions defined with `defun` are still called by their bare name
  - A lambda's arguments bind code blocks raw, like a function's
- **`eval` On A Symbol Runs The Name**:
  - `:x eval` does what writing `x` does: a macro is expanded, a variable's value is pushed, a function or an operator is run
  - Example: `3 4 :+ eval` is `7`; `{+} 0 nth eval` runs `+` (this undoes the 1.15.0 note on names taken out of a block)
  - A block held in `b` is pushed by `:b eval` and run by `b eval`
- **`eval` Takes Code, Not Text**:
  - `eval` runs a block, a symbol or a lambda. `"3 4 +" eval` is a type error; turn text into code with `parse` first: `"3 4 +" parse eval`
- **`read-from-string` Is Now `parse`**:
  - The word that turns text into a code block is `parse`: `"3 4 +" parse` is `{3 4 +}`. `read-from-string` is gone
- **Blocks Read As Data Give Symbols**:
  - `nth`, `list`, `sorted`, `reversed`, `enumerate`, `zip` and the block argument of `map` / `filter` / `reduce` / `fold` give a symbol for every name written in the block, whatever the name holds
  - Example: `{x} 0 nth` is the symbol `x`; `{x y} {} map` is `{x y}`. Write a list literal `[x y]` when the values are wanted
  - The aggregates (`sum`, `max`, `all`, ...) still reference the names; `len` counts tokens; `apply` evaluates its argument first, as before, and reads only a block left behind as data
  - A value spliced into a block by `sub`, `subn`, parameter interpolation or a block-returning word becomes a token of its own kind: a symbol becomes a bare name; a string, literal or computed, becomes a string literal
- **Conditions Are Values**:
  - `if` / `ifelse` no longer look a string or symbol condition up as a variable: a symbol is true, a string is true unless empty
  - Example: `0 :x = :x {1} if` runs the block; write `x {1} if` to test the variable
- **`true`, `false` And `null` Are Literals**:
  - Like `True` / `False` / `None`, they cannot be rebound (`5 true set` is an error) and are not listed by `vars`. `pi`, `e` and the other constants are still variables
- **Argument Lists Are Checked**:
  - `defun` and `lambda` take their parameters as a block of distinct bare names, like `defmacro`: `{:a}`, `{"a"}`, a bare `:a` or a list is an error
- **Display**:
  - Every string is shown quoted, computed ones included (`"a" "b" +` shows `'ab'`); a symbol is shown bare
  - `null` is shown as `null`, like `true` and `false` (it used to show as `None`)
  - A code block shows its names as written, whether or not they are bound
- **Python API**:
  - A name comes back as a `Symbol` object (`from stacker import Symbol`; `.name` is the text), not as a `str`
  - `UndefinedSymbol` is removed; catch `UndefinedSymbolError` instead of testing for the value
  - Plugins receive a `Symbol` for a symbol argument

### Migration

- Put `:` before every name that is bound, defined or looped over: `4 x set` → `4 :x set`, `5 y =` → `5 :y =`, `42 answer global` → `42 :answer global`, `{...} {...} f defun` → `{...} {...} :f defun`, `{...} {...} m defmacro` → `{...} {...} :m defmacro`, `m macroexpand` → `:m macroexpand`, `1 10 i {...} do` → `1 10 :i {...} do`, `[...] x {...} dolist` → `[...] :x {...} dolist`, `[...] 0 acc x {...} reduce` → `[...] 0 :acc :x {...} reduce`. Your own variables, functions and macros are redefined the same way (`6 :x set`), and a `gensym` name bound in a macro body with `t set` is written `:t set`
- Old code stops right where such a name is written (`` `x` is not defined ``, with a hint to write `:x`), or at the binding word when the name was already defined (`` `set` expects a name, got 5 ``). The one silent change: rebinding by its bare name a variable that holds a symbol or a one-name block now binds that name instead
- On `.stk` files, the names before `set`, `=`, `global`, `defun`, `defmacro` and `macroexpand` can be rewritten with (run it on code lines only; it skips what follows `#` on a line but not the inside of strings, so check lines holding strings by hand):
  ```bash
  sed -E -i 's/^([^#]*)(^|[[:space:]{(])([A-Za-z_][^][:space:]{}()":$#;]*)([[:space:]]+)(set|=|global|defun|defmacro|macroexpand)([[:space:]})]|$)/\1\2:\3\4\5\6/' file.stk
  ```
  (one pass rewrites one name per line; run it again until nothing changes). Loop variables are not caught by it: find the remaining names with
  ```bash
  grep -nE '(^|[[:space:]])[A-Za-z_][^[:space:]{}]*[[:space:]]+[{(]' -r . --include='*.stk'
  ```
  and add `:` to those followed by `do` or `dolist`, and to both names before the block of `reduce` / `fold`
- `$name` everywhere, operator names included (`$+`, `$>=`): write `:name`. On `.stk` files: `sed -E 's/(^|[[:space:][{(])\$([^][:space:]{}()]+)/\1:\2/g'`, then check by hand the strings that contained `$` after a space (`"cost $5"` would become `"cost :5"`)
- `:x` used where its value was meant: write `x`. A lambda passed on with `:f`: write `f`
- A string used as a name (`5 "x" set`, `"sqrt" map`, `"+" apply`, `"m" macroexpand`): write `:x` / `{x}`, or `"x" symbol` when the name is built from text
- An undefined name used as data (`foo m`, `[a b]`, `{2 *} double alias`): write `{foo} m` or `:foo m`, `[:a :b]`, `{2 *} :double alias`
- `:x` or `"x"` written as a condition to test the variable `x`: write `x`
- `:b eval` to run a block held in `b`: write `b eval`
- `"..." eval` to run text: write `"..." parse eval`
- `read-from-string`: write `parse`
- A lambda called by its bare name (`{x y} {x y *} lambda :multiply set 3 4 multiply`): write `3 4 multiply eval`, or define it with `defun`. `[1 2] {f} map` with a lambda in `f`: write `[1 2] f map`
- `:x "x" ==`: write `:x str "x" ==`
- `{:a} {a} lambda` or `:a {a 2 *} :f defun`: write `{a}`
- A block whose names were read as values by `map`, `reduce` or `list`: write a list literal `[x y]` instead of `{x y}`
- Python code that tested `isinstance(v, str)` to recognize a name: test `isinstance(v, Symbol)`. Code that looked for `UndefinedSymbol` values: catch `UndefinedSymbolError`
- To find `:name` written where a value was meant, look for `:name` that is not right before `set`, `=`, `global`, `defun`, `defmacro`, `macroexpand` or `alias`, nor the name before a `do` / `dolist` / `reduce` / `fold` block:
  ```bash
  grep -nE '(^|[[:space:]\[{(]):[^[:space:]{}"]+' -r . --include='*.stk' \
    | grep -vE ':[^[:space:]]+[[:space:]]+(set|=|global|defun|defmacro|macroexpand|alias)([[:space:]]|$)' \
    | grep -vE ':[^[:space:]]+[[:space:]]+\{'
  ```
  (the accumulator name of `reduce` / `fold` still shows up; check those by eye)

### Added

- **`symbol`**: `"x" symbol` makes the symbol `x` from a string; `{x} symbol` from a quoted name; a symbol is returned as it is. Text that cannot be written as `:name` (`"1"`, `"a b"`, `""`) is a syntax error
- **`symbol?`**: true for a symbol
- **Symbols in list literals**: `[:a :b]` is a list of two symbols
- **`StackerTypeError`**: raised (it is a `TypeError` too) when a symbol reaches a word that needs a value; the message names the symbol and the two ways to write what was probably meant
- **`Symbol`** is exported from the `stacker` package for embedding code

### Fixed

- A loop on the last line of a script was silently dropped: `1 3 :i` on one line and `{i echo} do` on the next, or a body held in a variable (`1 3 :i body do`), ran nothing and exited 0 when it ended the file (and the same in `~/.stackerrc`): the script reader held such a line back, guessing that its arguments would follow. Each expression now runs once its brackets and strings are closed, and an error on the line after a loop is reported at its own line
- `~/.stackerrc` could not hold the display settings the README shows (`disable_disp_logo`, `disable_disp_stack`, `enable_disp_ans`): since 1.9.0 every mode stopped at start-up with "`disable_disp_logo` is not defined". The REPL applies them again; the command line and scripts skip them. `help`, `about` and `delete_history` are skipped everywhere rather than run on every start
- `break` outside a loop took the REPL down with a traceback and leaked a `BaseException` to Python callers; it is a `StackerSyntaxError` ("`break` can only be used inside a loop") and the REPL carries on. A `break` in an included file still leaves the loop that runs the `include`
- `ans` was registered but did nothing since 1.5.0. It pushes again the result of the last input that left a value (a REPL line, an expression of a script, `-e`), stays available after the stack is used up, and is an error when there is no result yet
- `zip` and `enumerate` handed back Python tuples, shown as `[(1, 4) (2, 5) (3, 6)]`; each pair is a list now (`[[1 4] [2 5] [3 6]]`, `[10 20] enumerate` → `[[0 10] [1 20]]`)
- An index out of range inside an operator (`[1 2] 5 nth`, `"{} {}" 3 format`) was reported as "`nth` requires 2 arguments"; only an empty stack is a missing argument now, and the index error is reported as it is
- A value put into a block by `sub`, `subn` or `enumerate` was shown as Python shows it: `[1 2] sub` displayed `{[1, 2]}` and `true sub` displayed `{True}`. Such a value is shown as the stack display shows it (`{[1 2]}`, `{true}`)
- `times` with anything but a number as the count, such as the block and the count the wrong way round (`0 {"x" echo} times`) or a string (`{1} "3" times`), leaked a Python `TypeError`; it is a `StackerSyntaxError` that says to write `{body} n times`
- A condition block of `if`, `ifelse`, `cond` or `while` that left nothing on the stack was reported as the word lacking arguments ("`if` requires 2 arguments"); it now says that the condition block left nothing to test. The condition block itself is unchanged: it runs on the current stack, may use what is below it, and an empty block leaves the top as the condition
- With `enable_disp_ans` on, the REPL printed the top of the stack with Python's `str()` (`[[1, 2], [3, 4]]`, `hello`, `True`); the line is formatted like the stack display (`[[1 2] [3 4]]`, `'hello'`, `true`)
- `DropError`, `DupError`, `SwapError` and the other stack-word errors did not derive from `StackerError`, so `except StackerError` missed them
- README: the operator table listed an `input` word that does not exist, described `sub` / `subn` and the arguments of `ins` and `count` wrongly, omitted that `sin` / `cos` / `tan` take radians and that `phi` exists, and listed `true` / `false` as constants
- `[3 4] 5 apply` silently did nothing; a function argument that is neither a block, a lambda nor a symbol is now a type error
- Calling a lambda with too few arguments raised a Python `IndexError`; it is a `StackUnderflowError`
- A lambda that returned nothing left a `VOID` marker on the stack
- A code block showed an unbound name quoted (`{'foo'}`) and the same name bare once a variable existed
- `5 "$x" set x` bound `x` through the text of the string, and `"$x" :y set y list` read the string as a symbol
- `:x 1 +` leaked a Python `TypeError`
- `5 true set` silently replaced the constant `true`
- A bare name inside a nested list literal (`[[x 1]]`) was kept as text instead of being the variable's value
- README: the operator table named a `random` word that never existed (the word is `rand`) and described `all` / `any` with a two-argument form they never had
- `help` and `operators` did not list `map`, `filter`, `reduce`, `fold`, `zip`, the aggregates or the transforms. The help text still described tuples, `$` on loop variables and the two-argument `defmacro`; it and the descriptions of `do`, `dolist`, `times`, `while`, `lambda`, `defun`, `set`, `sub`, `subn`, `listn`, `nth`, `parse`, `read` (it reads a line and pushes it as a code block) and the higher-order words now match the language
- The `do` loop benchmark (`0 :s set 1 100000 :i {s i + :s set} do`) runs about 20% faster: the argument helpers no longer look every value up in the variable scopes

## [1.15.0] - 2026-10-10

### Breaking Changes

Note: This change is not backwards compatible with previous versions.

- **`defmacro` Takes Arguments And Generates Code**:
  - `defmacro` takes three arguments, `{args} {body} name defmacro`, like `defun`
  - The body runs when the macro is called, on its own stack and in its own scope, and must leave exactly one value: a code block is evaluated on the caller's stack, any other value is pushed
  - Argument names, and variables assigned inside the body, are substituted into the body's block literals
  - Assignments inside the body are local to the macro
  - Example: `{c b} {{{c eval not {break} if b eval} loop}} {while} defmacro`
  - The two-argument form `{body} name defmacro` is gone; a named code snippet is now `{body} {name} alias`
- **Built-in Names Are Protected Before A Binding Word** (superseded in 1.16.0, where no bare name is read as a name by position):
  - A bare built-in operator name right before `set` / `=` / `global` / `defun` / `defmacro` runs as that operator instead of being taken as the name to bind
  - Example: `{} {{2 *}} expand defmacro` used to define a macro named `expand`; it now runs `expand`
  - To rebind a built-in name, quote it: `3 $dup set` or `3 {dup} set`. Your own variables, functions and macros can still be redefined by their bare name
- **`expand` On Code Blocks**:
  - `{1 2 +} expand` pushes the one-token blocks `{1} {2} {+}`; it used to push the raw tokens, which left `+` as a string and made `{1 2 +} expand +` fail
  - `expand` on lists is unchanged
- **The Names Before `macroexpand`, `reduce` And `fold` Are Names** (superseded in 1.16.0: every name is written `:name`):
  - A bare name right before `macroexpand`, and the two names before the block of `reduce` / `fold`, are read as names, like the name before `set` or the loop variable of `do`
  - A variable holding a name can no longer be used there by its bare name: `$m which set which macroexpand` used to expand `m`; write `m macroexpand` or `{m} macroexpand`
- **The Prelude Is Loaded By `Stacker()`**:
  - The standard words written in Stacker (`alias`, `mean`) are loaded by every new interpreter, not only by the command line, so embedding code and scripts see the same words; `Stacker(prelude=False)` gives a bare interpreter
  - On the command line the prelude is loaded before plugins (previously after), so the prelude cannot refer to plugin words

### Migration

- Named code snippets: `{2 *} double defmacro` becomes `{2 *} {double} alias`
- Macros that need arguments: write them in the new form, e.g. `{x} {{x x +}} {twice} defmacro`
- Code that rebinds a built-in name with a bare name, e.g. `0 sum set` or `} max defun`, must quote the name: `0 $sum set`, `} {max} defun`
- Code that relied on `expand` turning a block into raw tokens should use `eval` on the pieces, or `concat-block` to build code
- Embedding code that inspected a fresh interpreter's macros or functions and expected them to be empty should create it with `Stacker(prelude=False)`
- Code that passed a macro name to `macroexpand`, or accumulator / element names to `reduce` / `fold`, through a variable should write the names directly (`m macroexpand`, `0 acc x {acc x +} reduce`)
- `eval` on an operator name taken out of a block as data (`{+} 0 nth`), or on a name wrapped with `sub` from a string (`"+" sub`), pushes it back instead of running the operator. Use `expand` or `apply` to run code taken from a block

### Added

- **`loop`**: `{body} loop` repeats a block on the current stack until `break`; every other loop can be written with it
- **`alias`** (prelude): `{body} {name} alias` names a code snippet that runs in place on the caller's stack
- **`gensym`**: pushes a fresh unique name (prefixed `__g`) for temporaries in macro-generated code
- **`macroexpand`**: `<args> {name} macroexpand` pushes a macro's expansion without running it
- **`concat-block`**: `{a b} {c} concat-block` joins two code blocks
- **Quoted names**: `{name}` passes a name as a value; every word that takes a name accepts it
- **`Stacker(prelude=...)`**: Python API flag to skip loading the prelude
- Redefining a prelude word logs a warning (`redefining prelude word 'alias'`) through the standard `logging` module

### Fixed

- **Control Flow In `-e` And `Stacker.eval()`**:
  - `if`, `ifelse`, `iferror`, `times`, `while`, `do` and `dolist` evaluated their blocks on the interpreter's own stack instead of the stack they were called on: `stacker -e "5 {dup ++} 3 times"` failed and `Stacker().eval("true {3} if")` returned an empty result. They now use the calling stack, like `cond` already did
  - `do` and `dolist` restore the enclosing scope even when the body raises
- A defined macro can be redefined by its bare name (`{} {{2}} m defmacro` used to fail with `Expected a symbol, got 1`)
- Macro recursion is stopped by the recursion guard with a `StackerRecursionError` naming the macro, instead of Python's `RecursionError`
- `{} 5 five defmacro` reports a Stacker syntax error instead of leaking an `AttributeError`
- Prelude files load in a fixed order (a manifest in the `slib` package) instead of directory-listing order
- `disp` (and the non-colored stack display) no longer deletes commas inside strings: `"Hello, World!" disp` shows `['Hello, World!']`, and booleans print as `true` / `false` like the colored display
- **String Literals Inside Code Blocks Are Literals**:
  - A string literal inside a block used to be looked up as a name when the block ran: `5 foo set {"foo"} eval` gave `5`, `3 4 {"+"} eval` added the numbers, and a macro named `foo` captured `"foo"` even at top level. A string literal now always evaluates to itself
  - Literals whose text looks like other syntax stay strings inside blocks too: `{"$x"}`, `{"[1 2]"}` and `{"{x}"}` push the strings `$x`, `[1 2]` and `{x}` (they used to be read as a symbol, a list and a block)
  - A block displays its string literals with their quotes: `{"a b" echo}` shows as `{"a b" echo}`
- `"..." eval` no longer substitutes variable values while tokenizing: `5 x set "6 x set x" eval` rebinds `x` and gives `6`, the same as `read-from-string eval`. A lambda held in a variable is called when its name appears in the evaluated string, as it is inside a block
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
  - `0 roll` is a no-op; negative counts raise `RollError`
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
