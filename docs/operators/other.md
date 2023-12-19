| Operator | Description                                           | Example                    |
|----------|-------------------------------------------------------|----------------------------|
| time     | Get Python time time object.                          | `time`                     |
| include  | Include the specified file                            | `"file.stk" include`       |
| eval     | Evaluate the specified RPN expression                 | `'3 5 +' eval`             |
| evalpy   | Evaluate the specified Python expression              | `'3+5' evalpy`             |
| echo     | Print the specified value to stdout without adding it to the stack | `3 4 + echo`  |