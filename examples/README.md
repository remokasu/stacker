# Stacker Examples

This directory contains example programs demonstrating various features of the Stacker language.

## Directory Structure

### basics/
Fundamental language features and control structures:
- **fizzbuzz.stk** - Classic FizzBuzz problem
- **loops.stk** - Nested loop examples
- **error_handling.stk** - Error handling with `iferror`
- **break.stk** - Breaking out of loops

### functions/
Function and macro definitions:
- **function_basics.stk** - Basic function definition and usage
- **function_and_macro.stk** - Difference between functions and macros

### algorithms/
Classic algorithms and computational examples:
- **factorial.stk** - Recursive factorial calculation
- **fibonacci.stk** - Iterative Fibonacci calculation
- **gcd.stk** - Euclidean algorithm for GCD
- **square_sum.stk** - Sum of squares calculation
- **pi_calculation.stk** - Pi approximation using Leibniz formula

### advanced/
Advanced features and patterns:
- **global_variables.stk** - Using global variables

## Running Examples

Run any example with:
```bash
stacker examples/basics/fizzbuzz.stk
```

Or explore them interactively:
```bash
stacker
stacker:0> "examples/basics/fizzbuzz.stk" include
```

## Syntax Notes

All examples use the modern Stacker syntax:
- Variable assignment: `value variable =` (not `value $variable =`)
- Variable reference: `variable` (not `$variable`)
- The `$` prefix is supported for backward compatibility but not recommended
