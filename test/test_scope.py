import unittest
from pathlib import Path
import tempfile
import os

from stacker.stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode


class TestVariableScope(unittest.TestCase):
    """Test variable scoping behavior."""

    def setUp(self):
        self.stacker = Stacker()

    def test_global_variable_access_from_function(self):
        """Test that functions can $access global variables."""
        self.stacker.stack.clear()
        self.stacker.eval("10 $global_var set")
        self.stacker.eval("{x} {x global_var +} $add_global defun")
        result = self.stacker.eval("5 add_global")
        self.assertEqual(result[-1], 15)

    def test_local_variable_shadows_global(self):
        """Test that local variables $shadow global variables."""
        self.stacker.stack.clear()
        self.stacker.eval("100 $x set")
        self.stacker.eval("{x} {x 2 *} $double defun")
        result = self.stacker.eval("5 double")
        self.assertEqual(result[-1], 10)
        # Global x should still be 100
        result = self.stacker.eval("x")
        self.assertEqual(result[-1], 100)

    def test_function_does_not_modify_global_scope(self):
        """Test that function-local variables don't $affect global scope."""
        self.stacker.stack.clear()
        self.stacker.eval("42 $answer set")
        self.stacker.eval("{n} {n $temp set temp 2 *} $calc defun")
        result = self.stacker.eval("10 calc")
        self.assertEqual(result[-1], 20)
        # Global answer should still be 42
        result = self.stacker.eval("answer")
        self.assertEqual(result[-1], 42)
        # temp should not exist $in global scope - it becomes UndefinedSymbol
        from stacker.engine.data_type import UndefinedSymbol

        result = self.stacker.eval("temp")
        self.assertIsInstance(result[-1], UndefinedSymbol)
        # But using it in an operation should raise an error
        with self.assertRaises(Exception):
            self.stacker.eval("temp 5 +")

    def test_nested_function_calls_independent_scopes(self):
        """Test that nested function calls have independent scopes."""
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 1 +} $inc defun")
        self.stacker.eval("{x} {x inc inc inc} $inc3 defun")
        result = self.stacker.eval("5 inc3")
        self.assertEqual(result[-1], 8)

    def test_recursive_function_independent_scopes(self):
        """Test that recursive calls maintain independent scopes."""
        self.stacker.stack.clear()
        # Fibonacci: fib(n) = fib(n-1) + fib(n-2), base cases: fib(0)=0, fib(1)=1
        self.stacker.eval("""
            {n} {
                n 2 <
                {n}
                {n 1 - fib n 2 - fib +}
                ifelse
            } $fib defun
        """)
        result = self.stacker.eval("6 fib")
        self.assertEqual(result[-1], 8)  # fib(6) = 8

    def test_multiple_parameters_scoping(self):
        """Test that functions with multiple parameters maintain proper scoping."""
        self.stacker.stack.clear()
        self.stacker.eval("{a b c} {a b * c +} $calc defun")
        result = self.stacker.eval("2 3 4 calc")
        self.assertEqual(result[-1], 10)  # 2*3 + 4 = 10


class TestFunctionScope(unittest.TestCase):
    """Test function definition scoping."""

    def setUp(self):
        self.stacker = Stacker()

    def test_function_calls_another_function(self):
        """Test that a function can call another function."""
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x x *} $square defun")
        self.stacker.eval("{x} {x square 2 *} $double_square defun")
        result = self.stacker.eval("5 double_square")
        self.assertEqual(result[-1], 50)  # (5*5)*2 = 50

    def test_recursive_factorial(self):
        """Test recursive factorial function."""
        self.stacker.stack.clear()
        self.stacker.eval("""
            {n} {
                n 1 <=
                {1}
                {n n 1 - fact *}
                ifelse
            } $fact defun
        """)
        result = self.stacker.eval("5 fact")
        self.assertEqual(result[-1], 120)  # 5! = 120

    def test_mutual_recursion(self):
        """Test mutually recursive functions (even/odd checker)."""
        self.stacker.stack.clear()
        self.stacker.eval("""
            {n} {
                n 0 ==
                {1}
                {n 1 - is_odd}
                ifelse
            } $is_even defun
        """)
        self.stacker.eval("""
            {n} {
                n 0 ==
                {0}
                {n 1 - is_even}
                ifelse
            } $is_odd defun
        """)
        result = self.stacker.eval("4 is_even")
        self.assertEqual(result[-1], 1)  # 4 is even
        result = self.stacker.eval("5 is_even")
        self.assertEqual(result[-1], 0)  # 5 is not even
        result = self.stacker.eval("5 is_odd")
        self.assertEqual(result[-1], 1)  # 5 is odd


class TestLambdaScope(unittest.TestCase):
    """Test lambda function scoping."""

    def setUp(self):
        self.stacker = Stacker()

    def test_lambda_access_global_variable(self):
        """Test that lambda can $access global variables."""
        self.stacker.stack.clear()
        self.stacker.eval("10 $offset set")
        result = self.stacker.eval("[1 2 3] {x} {x offset +} lambda map")
        self.assertEqual(result[-1], [11, 12, 13])

    def test_lambda_parameter_shadows_global(self):
        """Test that lambda parameters $shadow global variables."""
        self.stacker.stack.clear()
        self.stacker.eval("100 $x set")
        result = self.stacker.eval("[1 2 3] {x} {x 2 *} lambda map")
        self.assertEqual(result[-1], [2, 4, 6])
        # Global x should still be 100
        result = self.stacker.eval("x")
        self.assertEqual(result[-1], 100)

    def test_lambda_in_function(self):
        """Test lambda used within a function."""
        self.stacker.stack.clear()
        self.stacker.eval("""
            {lst multiplier} {
                lst {x} {x multiplier *} lambda map
            } $multiply_list defun
        """)
        result = self.stacker.eval("[1 2 3 4] 3 multiply_list")
        self.assertEqual(result[-1], [3, 6, 9, 12])

    def test_lambda_recursive(self):
        """Test recursive lambda function."""
        self.stacker.stack.clear()
        # Recursive lambda factorial
        self.stacker.eval("""
            {n} {
                n 1 <=
                {1}
                {n n 1 - fact *}
                ifelse
            } lambda $fact set
        """)
        result = self.stacker.eval("5 fact eval")
        self.assertEqual(result[-1], 120)  # 5! = 120


class TestMacroScope(unittest.TestCase):
    """Test macro scoping behavior."""

    def setUp(self):
        self.stacker = Stacker()

    def test_macro_expansion(self):
        """Test basic macro expansion."""
        self.stacker.stack.clear()
        self.stacker.eval("{5 +} $add5 defmacro")
        result = self.stacker.eval("10 add5")
        self.assertEqual(result[-1], 15)

    def test_macro_with_global_variable(self):
        """Test macro $accessing global variables."""
        self.stacker.stack.clear()
        self.stacker.eval("100 $base set")
        self.stacker.eval("{base +} $add_base defmacro")
        result = self.stacker.eval("25 add_base")
        self.assertEqual(result[-1], 125)

    def test_macro_vs_function_scoping(self):
        """Test that macros and functions have different scoping behavior."""
        self.stacker.stack.clear()
        # Function evaluates in its own scope
        self.stacker.eval("{x} {x 2 *} $f_double defun")
        # Macro expands in caller's scope
        self.stacker.eval("{2 *} $m_double defmacro")

        result = self.stacker.eval("5 f_double")
        self.assertEqual(result[-1], 10)
        result = self.stacker.eval("5 m_double")
        self.assertEqual(result[-1], 10)


class TestComplexScopeScenarios(unittest.TestCase):
    """Test complex scoping scenarios."""

    def setUp(self):
        self.stacker = Stacker()

    def test_deep_recursion_scope_isolation(self):
        """Test that deep recursion maintains scope isolation."""
        self.stacker.stack.clear()
        # Sum from 1 to n
        self.stacker.eval("""
            {n} {
                n 0 <=
                {0}
                {n n 1 - sum_to +}
                ifelse
            } $sum_to defun
        """)
        result = self.stacker.eval("10 sum_to")
        self.assertEqual(result[-1], 55)  # 1+2+3+...+10 = 55

    def test_function_calls_with_different_arguments(self):
        """Test that function calls with different arguments maintain independence."""
        self.stacker.stack.clear()
        self.stacker.eval("""
            {base exp} {
                exp 0 ==
                {1}
                {base base exp 1 - power *}
                ifelse
            } $power defun
        """)
        result = self.stacker.eval("2 3 power")
        self.assertEqual(result[-1], 8)  # 2^3 = 8
        result = self.stacker.eval("3 2 power")
        self.assertEqual(result[-1], 9)  # 3^2 = 9
        result = self.stacker.eval("5 0 power")
        self.assertEqual(result[-1], 1)  # 5^0 = 1

    def test_multiple_functions_same_parameter_names(self):
        """Test multiple functions with same parameter names don't interfere."""
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 10 +} $add10 defun")
        self.stacker.eval("{x} {x 20 +} $add20 defun")
        self.stacker.eval("{x} {x 30 +} $add30 defun")

        result = self.stacker.eval("5 add10")
        self.assertEqual(result[-1], 15)
        result = self.stacker.eval("5 add20")
        self.assertEqual(result[-1], 25)
        result = self.stacker.eval("5 add30")
        self.assertEqual(result[-1], 35)

    def test_scope_with_loops(self):
        """Test scoping behavior with loops."""
        self.stacker.stack.clear()
        self.stacker.eval("0 $total set")
        self.stacker.eval("""
            [1 2 3 4 5] $i {
                total i + $total set
            } dolist
        """)
        result = self.stacker.eval("total")
        self.assertEqual(result[-1], 15)

    def test_constants_accessible_in_functions(self):
        """Test that built-in constants are accessible in functions."""
        self.stacker.stack.clear()
        self.stacker.eval("{r} {r r * pi *} $circle_area defun")
        result = self.stacker.eval("1 circle_area")
        # Should be approximately pi
        self.assertAlmostEqual(result[-1], 3.141592653589793, places=10)


class TestGlobalOperator(unittest.TestCase):
    """Test global operator behavior."""

    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_basic_global_declaration(self):
        """Test $that global operator sets variable $in global scope."""
        script_content = """
0 $counter global
counter 1 + $counter global
counter
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 1)
        finally:
            os.unlink(temp_file)

    def test_global_update_from_function(self):
        """Test $that global variables can be updated from functions."""
        script_content = """
0 $counter global

{x} {
    counter 1 + $counter global
    x counter *
} multiply_with_count defun

10 multiply_with_count
counter
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 1)  # counter should be 1
        finally:
            os.unlink(temp_file)

    def test_global_multiple_function_calls(self):
        """Test global variable persists across multiple function calls."""
        script_content = """
0 $counter global

{} {
    counter 1 + $counter global
    counter
} increment defun

increment drop
increment drop
increment drop
counter
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 3)
        finally:
            os.unlink(temp_file)

    def test_global_from_nested_function(self):
        """Test that nested functions can access and modify globals."""
        script_content = """
0 $value global

{} {
    {x} {
        x $value global
        value
    } set_value defun

    42 set_value drop
    value
} outer defun

outer
value
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 42)
        finally:
            os.unlink(temp_file)


class TestSetVsGlobal(unittest.TestCase):
    """Tests for set operator behavior with existing vs new variables."""

    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_set_updates_existing_global(self):
        """Test that set updates an $existing global variable."""
        script_content = """
10 x set

{} {
    20 x set
    x
} update defun

update
x
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # x should be updated to 20
            self.assertEqual(self.stacker.stack[-1], 20)
        finally:
            os.unlink(temp_file)

    def test_set_creates_local_if_not_exists(self):
        """Test that set creates local variable if it doesn't exist."""
        script_content = """
{} {
    42 newvar set
    newvar
} create_local defun

create_local
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # newvar should not exist $in global scope
            self.assertNotIn('newvar', self.stacker.variables._local)
        finally:
            os.unlink(temp_file)

    def test_set_vs_global_difference(self):
        """Test the difference between set $and global operators."""
        script_content = """
0 a set
0 b set

{} {
    10 a set
    20 $b global
    b
} modify defun

modify
a
b
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # a was updated with set (updates existing)
            self.assertEqual(self.stacker.stack[-2], 10)
            # b was updated $with global
            self.assertEqual(self.stacker.stack[-1], 20)
        finally:
            os.unlink(temp_file)


class TestLoopVariableScope(unittest.TestCase):
    """Tests for loop variable scope behavior."""

    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_do_loop_variable_is_local(self):
        """Test that do loop variables are local to the loop."""
        script_content = """
999 i set

0 5 $i {
    i
} do

i
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # Loop should produce 0,1,2,3,4,5
            # Check a few values
            stack_list = list(self.stacker.stack)
            self.assertIn(0, stack_list[:-1])
            self.assertIn(5, stack_list[:-1])
            # Global i should still be 999
            self.assertEqual(stack_list[-1], 999)
        finally:
            os.unlink(temp_file)

    def test_dolist_loop_variable_is_local(self):
        """Test that dolist loop variables are local to the loop."""
        script_content = """
999 item set

[10 20 30] $item {
    item
} dolist

item
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # Should have 10, 20, 30 from loop
            stack_list = list(self.stacker.stack)
            self.assertIn(10, stack_list[:-1])
            self.assertIn(20, stack_list[:-1])
            self.assertIn(30, stack_list[:-1])
            # Global item should still be 999
            self.assertEqual(stack_list[-1], 999)
        finally:
            os.unlink(temp_file)

    def test_accessing_global_from_loop(self):
        """Test that loops can access and $modify global variables."""
        script_content = """
0 $sum global

1 5 $i {
    sum i + $sum global
} do

sum
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # sum should be 1+2+3+4+5 = 15
            self.assertEqual(self.stacker.stack[-1], 15)
        finally:
            os.unlink(temp_file)

    def test_nested_loops_with_same_variable_name(self):
        """Test nested loops with same variable name."""
        script_content = """
0 1 $i {
    10 11 $i {
        i
    } do
} do
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # Each outer loop iteration should run inner loop twice
            # Inner loop produces 10, 11 for each outer iteration
            # Total: 10, 11, 10, 11
            stack_list = list(self.stacker.stack)
            self.assertEqual(len(stack_list), 4)
            self.assertEqual(stack_list[0], 10)
            self.assertEqual(stack_list[1], 11)
        finally:
            os.unlink(temp_file)

    def test_loop_updating_existing_variable_with_set(self):
        """Test that loop can update existing variables with set operator."""
        script_content = """
0 total set

1 5 $i {
    total i + total set
} do

total
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # total should be 1+2+3+4+5 = 15
            self.assertEqual(self.stacker.stack[-1], 15)
        finally:
            os.unlink(temp_file)


class TestRecursiveWithGlobal(unittest.TestCase):
    """Tests for recursive functions $using global variables."""

    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_recursive_function_with_global_counter(self):
        """Test recursive function that $uses global counter."""
        script_content = """
0 $count global

{n} {
    count 1 + $count global
    n 1 <= {
        1
    } {
        n n 1 - factorial *
    } ifelse
} factorial defun

5 factorial
count
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # 5! = 120
            self.assertEqual(self.stacker.stack[-2], 120)
            # count should be 5 (one increment per recursive call)
            self.assertEqual(self.stacker.stack[-1], 5)
        finally:
            os.unlink(temp_file)

    def test_recursive_with_global_accumulator(self):
        """Test recursive function that accumulates $in global variable."""
        script_content = """
0 $acc global

{n} {
    n 0 <= {
        acc
    } {
        acc n + $acc global
        n 1 - sum_recursive
    } ifelse
} sum_recursive defun

10 sum_recursive
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # 10+9+8+...+1 = 55
            self.assertEqual(self.stacker.stack[-1], 55)
        finally:
            os.unlink(temp_file)


class TestComplexGlobalScenarios(unittest.TestCase):
    """Tests for complex scenarios $mixing global, local, and set."""

    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_mixed_global_local_set(self):
        """Test $mixing global, local, and set in complex scenario."""
        script_content = """
0 $a global
0 b set

{} {
    10 $a global
    20 b set
    30 c set
    0
} modify defun

modify drop
a
b
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # a was $set globally
            self.assertEqual(self.stacker.stack[-2], 10)
            # b was updated (it existed)
            self.assertEqual(self.stacker.stack[-1], 20)
            # c should not $exist globally
            self.assertNotIn('c', self.stacker.variables._local)
        finally:
            os.unlink(temp_file)

    def test_loop_inside_function_with_global(self):
        """Test loop variables inside function scope $with global accumulation."""
        script_content = """
0 $total global

{n} {
    1 n $i {
        total i + $total global
        0
    } do
    total
} accumulate defun

10 accumulate drop
total
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # 1+2+...+10 = 55
            self.assertEqual(self.stacker.stack[-1], 55)
        finally:
            os.unlink(temp_file)

    def test_function_modifying_global_in_loop(self):
        """Test function that $modifies global variable called in a loop."""
        script_content = """
0 $total global

{x} {
    total x + $total global
    total
} add_to_total defun

1 5 $i {
    i add_to_total drop
} do

total
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # total should be 1+2+3+4+5 = 15
            self.assertEqual(self.stacker.stack[-1], 15)
        finally:
            os.unlink(temp_file)

    def test_multiple_functions_sharing_global(self):
        """Test multiple functions sharing $same global variable."""
        script_content = """
0 $shared global

{x} {
    shared x + $shared global
    shared
} add_to_shared defun

{x} {
    shared x * $shared global
    shared
} multiply_shared defun

5 add_to_shared drop
2 multiply_shared drop
shared
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # shared = 0, then 0+5=5, then 5*2=10
            self.assertEqual(self.stacker.stack[-1], 10)
        finally:
            os.unlink(temp_file)


class TestScopeEdgeCases(unittest.TestCase):
    """Tests for edge cases in scope behavior."""

    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_parameter_shadowing_global(self):
        """Test function parameter $shadowing global variable."""
        script_content = """
999 $x global

{x} {
    x 2 *
} double defun

5 double
x
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # Function uses parameter x (5), returns 10
            self.assertEqual(self.stacker.stack[-2], 10)
            # Global x unchanged
            self.assertEqual(self.stacker.stack[-1], 999)
        finally:
            os.unlink(temp_file)

    def test_loop_variable_shadowing_global(self):
        """Test loop variable $shadowing global variable."""
        script_content = """
999 $i global

1 3 $i {
    i
} do

i
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # Loop produces 1, 2, 3
            stack_list = list(self.stacker.stack)
            self.assertIn(1, stack_list[:-1])
            self.assertIn(3, stack_list[:-1])
            # Global i should still be 999
            self.assertEqual(stack_list[-1], 999)
        finally:
            os.unlink(temp_file)

    def test_global_declaration_inside_conditional(self):
        """Test global declaration inside conditional block."""
        script_content = """
1 {
    42 $result global
    result
} {
    0 $result global
    result
} ifelse

result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # result should be 42 since condition is true
            self.assertEqual(self.stacker.stack[-1], 42)
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()
