# Stacker Examples

This directory contains example programs demonstrating various features of the Stacker language.

## Directory Structure

### basics/
Fundamental language features and control structures:
- **variables.stk** - Variable assignment, scope, and global variables
- **stack_operations.stk** - Stack manipulation (dup, swap, rot, etc.)
- **conditionals.stk** - Conditional statements (if, ifelse) and comparisons
- **types.stk** - Data types and type conversions
- **fizzbuzz.stk** - Classic FizzBuzz problem
- **loops.stk** - Nested loop examples
- **error_handling.stk** - Error handling with `iferror`
- **break.stk** - Breaking out of loops

### functions/
Function and macro definitions:
- **function_basics.stk** - Basic function definition and usage
- **function_and_macro.stk** - Difference between functions and macros
- **lambda.stk** - Lambda functions and closures
- **recursion.stk** - Recursive functions and patterns
- **higher_order.stk** - Higher-order functions (map, filter, reduce)

### algorithms/
Classic algorithms and computational examples:
- **factorial.stk** - Recursive factorial calculation
- **fibonacci.stk** - Iterative Fibonacci calculation
- **gcd.stk** - Euclidean algorithm for GCD
- **square_sum.stk** - Sum of squares calculation
- **pi_calculation.stk** - Pi approximation using Leibniz formula
- **sorting.stk** - Sorting algorithms (bubble, selection, insertion, merge, quick)
- **prime_numbers.stk** - Prime number detection and generation

### advanced/
Advanced features and patterns:
- **global_variables.stk** - Using global variables
- **string_operations.stk** - String manipulation and processing
- **file_io.stk** - File operations (read, write, append)
- **eval_examples.stk** - Dynamic code execution with eval

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
