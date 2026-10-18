"""Equivalence classes, boundaries and error paths for string escapes.

`test_string_escapes.py` holds the behaviour-level cases; this file walks
every escape through every quote form, the code point edges, the places a
string can sit (list, block, macro, `sub`, `parse`) and the error position.
"""

import pytest

from stacker import Stacker
from stacker.engine.data_type import String
from stacker.error import StackerSyntaxError, UndefinedSymbolError
from stacker.syntax.token_rules import decode_string_token, escape_for_display
from stacker.util.disp import plain_text

QUOTES = ['"', "'", '"""', "'''"]
SIMPLE_ESCAPES = [
    (r"\n", "\n"),
    (r"\t", "\t"),
    (r"\r", "\r"),
    (r"\0", "\0"),
    (r"\\", "\\"),
    (r"\"", '"'),
    (r"\'", "'"),
]


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


def top_block_text(program: str) -> str:
    stacker = Stacker()
    stacker.process_expression(program)
    return str(stacker.stack[-1])


class TestEveryEscapeInEveryQuoteForm:
    @pytest.mark.parametrize("quote", QUOTES)
    @pytest.mark.parametrize("source, char", SIMPLE_ESCAPES)
    def test_an_escape_is_read_in_any_quote_form(self, quote, source, char):
        assert run(f"{quote}a{source}b{quote}") == [f"a{char}b"]

    @pytest.mark.parametrize("quote", QUOTES)
    @pytest.mark.parametrize("source, char", SIMPLE_ESCAPES)
    def test_an_escape_alone_is_the_whole_string(self, quote, source, char):
        assert run(f"{quote}{source}{quote}") == [char]

    @pytest.mark.parametrize("quote", QUOTES)
    @pytest.mark.parametrize("source, char", SIMPLE_ESCAPES)
    def test_an_escape_next_to_the_closing_quote(self, quote, source, char):
        assert run(f"{quote}x{source}{quote} len") == [2]

    @pytest.mark.parametrize("quote", QUOTES)
    def test_hex_escapes_in_any_quote_form(self, quote):
        assert run(f"{quote}\\x41\\u0042{quote}") == ["AB"]


class TestHexEscapes:
    @pytest.mark.parametrize(
        "literal, char",
        [
            (r'"\x00"', "\x00"),
            (r'"\x01"', "\x01"),
            (r'"\x1f"', "\x1f"),
            (r'"\x20"', " "),
            (r'"\x7e"', "~"),
            (r'"\x7f"', "\x7f"),
            (r'"\x80"', "\x80"),
            (r'"\xff"', "\xff"),
            (r'"\xFF"', "\xff"),
            (r'"\xfF"', "\xff"),
            (r'"\u0000"', "\x00"),
            (r'"\u00e9"', "é"),
            (r'"\u3042"', "あ"),
            (r'"\ud7ff"', "\ud7ff"),
            (r'"\ue000"', "\ue000"),
            (r'"\uffff"', "\uffff"),
        ],
    )
    def test_a_hex_escape_reads_its_code_point(self, literal, char):
        assert run(literal) == [char]

    @pytest.mark.parametrize("upper, lower", [(r'"\uD7FF"', r'"\ud7ff"'), (r'"\uE000"', r'"\ue000"'), (r'"\uFFFF"', r'"\uffff"')])
    def test_upper_case_hex_digits_read_like_lower_case_ones(self, upper, lower):
        assert run(upper) == run(lower)

    def test_upper_and_lower_case_hex_are_the_same_character(self):
        assert run(r'"\u00E9" "\u00e9" ==') == [True]

    @pytest.mark.parametrize("literal", [r'"\ud800"', r'"\uD800"', r'"\udbff"', r'"\udc00"', r'"\udfff"', r'"\uDFFF"'])
    def test_a_surrogate_code_point_is_an_error(self, literal):
        with pytest.raises(StackerSyntaxError, match="is not a character"):
            run(literal)

    @pytest.mark.parametrize(
        "literal",
        [r'"\x"', r'"\x4"', r'"\x4g"', r'"\xg4"', r'"\u"', r'"\u1"', r'"\u123"', r'"\u12g4"', r'"\u 123"', r'"\x-1"', r'"\x+1"'],
    )
    def test_too_few_or_non_hex_digits_is_an_error(self, literal):
        with pytest.raises(StackerSyntaxError, match="hex digits"):
            run(literal)

    def test_more_digits_than_needed_leave_the_rest_as_text(self):
        assert run(r'"\x414"') == ["A4"]
        assert run(r'"\u00e9e"') == ["ée"]

    def test_the_escape_before_a_hex_escape_does_not_swallow_it(self):
        assert run(r'"\\x41"') == ["\\x41"]
        assert run(r'"\\\x41"') == ["\\A"]


class TestEscapesNextToTheClosingQuote:
    def test_an_escaped_backslash_then_the_closing_quote(self):
        assert run(r'"a\\"') == ["a\\"]

    def test_an_escaped_quote_alone(self):
        assert run(r'"\""') == ['"']

    def test_two_escaped_backslashes_then_the_closing_quote(self):
        assert run(r'"a\\\\" len') == [3]

    def test_an_escaped_backslash_and_an_escaped_quote_together(self):
        assert run(r'"\\\""') == ['\\"']

    def test_the_token_after_an_escaped_backslash_is_a_separate_token(self):
        assert run(r'"a\\" "b"') == ["a\\", "b"]

    def test_a_backslash_before_the_closing_quote_keeps_the_string_open(self):
        from stacker.error import UnterminatedTokenError

        with pytest.raises(UnterminatedTokenError):
            run('"a\\"')

    def test_decoding_a_token_that_ends_in_a_lone_backslash_is_an_error(self):
        with pytest.raises(StackerSyntaxError, match="lone backslash"):
            decode_string_token('"abc\\"')

    @pytest.mark.parametrize("literal", [r'"a\q"', r'"\q"', r'"\ "', r'"\a"', r'"\b"', r'"\v"', r'"\/"', r'"\1"'])
    def test_a_backslash_before_a_non_escape_is_an_error(self, literal):
        with pytest.raises(StackerSyntaxError, match="unknown escape"):
            run(literal)

    def test_a_backslash_before_a_non_escape_at_the_end_is_an_error(self):
        with pytest.raises(StackerSyntaxError, match="unknown escape"):
            run(r'"abc\z"')


class TestEscapesInsideContainers:
    @pytest.mark.parametrize(
        "program, expected",
        [
            (r'[["a\tb"]]', [[["a\tb"]]]),
            (r'[["a\tb"] ["c\nd"]]', [[["a\tb"], ["c\nd"]]]),
            (r'[[["a\\b"]]]', [[[["a\\b"]]]]),
            (r'[["\x41" "\u00e9"]]', [[["A", "é"]]]),
            (r'{["a\tb"]} eval', [["a\tb"]]),
            (r'{[["a\tb"]]} eval', [[["a\tb"]]]),
            (r'{{["a\tb"]} eval} eval', [["a\tb"]]),
            (r'{["a\tb" 1]} eval 0 at', ["a\tb"]),
        ],
    )
    def test_nested_literals_read_escapes_once(self, program, expected):
        assert run(program) == expected

    def test_a_string_in_a_list_in_a_block_is_still_a_string_value(self):
        (inner,) = run(r'{["a\tb"]} eval')
        assert isinstance(inner[0], String)

    @pytest.mark.parametrize("program", [r'[["a\q"]]', r'{["a\q"]} eval', r'[["ok"] ["\u12"]]'])
    def test_a_bad_escape_in_a_nested_literal_is_an_error(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    def test_a_bad_escape_in_a_list_inside_a_block_is_reported_when_the_block_runs(self):
        # observed: only string tokens are checked at build time; the list literal is read on run
        stacker = Stacker()
        stacker.process_expression(r'{["a\q"]}')
        assert len(stacker.stack) == 1
        with pytest.raises(StackerSyntaxError, match="unknown escape"):
            stacker.process_expression("eval")

    def test_a_block_with_a_list_holding_a_string_shows_the_escape(self):
        assert top_block_text(r'{["a\tb"]}') == '{["a\\tb"]}'


class TestParseReadsItsTextAgain:
    def test_the_decoded_text_is_read_a_second_time_by_parse(self):
        # `"\"a\\tb\""` decodes to the 6 characters `"a\tb"` (backslash, t);
        # `parse` reads that source again, so `\t` becomes a TAB (3 characters)
        assert run(r'"\"a\\tb\"" parse eval len') == [3]
        assert run(r'"\"a\\tb\"" parse eval') == ["a\tb"]

    def test_parse_of_a_decoded_tab_text_gives_a_string_with_a_real_tab_too(self):
        # the decoded text holds a real TAB between the quotes: still one string
        assert run(r'"\"a\tb\"" parse eval') == ["a\tb"]

    def test_parse_gives_a_block_that_shows_the_escape(self):
        (block,) = run(r'"\"a\\tb\"" parse')
        assert str(block) == '{"a\\tb"}'

    def test_parse_of_a_bad_escape_in_the_text_is_an_error(self):
        with pytest.raises(StackerSyntaxError):
            run(r'"\"a\\qb\"" parse eval')

    def test_parse_of_an_escaped_backslash_text_reads_it_down_to_one_backslash(self):
        # decoded text: "a\\b" (2 backslashes) -> parse -> one backslash
        assert run(r'"\"a\\\\b\"" parse eval') == ["a\\b"]


class TestDisplayRoundTrip:
    @pytest.mark.parametrize(
        "text, shown",
        [
            ("a\rb", "'a\\rb'"),
            ("a\0b", "'a\\0b'"),
            ("\x01", "'\\x01'"),
            ("\x1f", "'\\x1f'"),
            ("\x7f", "'\\x7f'"),
            ("a\\b", "'a\\\\b'"),
            ("\\", "'\\\\'"),
            ("it's", "'it's'"),
            ('say "hi"', "'say \"hi\"'"),
            ("éあ", "'éあ'"),
            ("", "''"),
        ],
    )
    def test_the_stack_shows_a_string(self, text, shown):
        assert plain_text(String(text)) == shown

    @pytest.mark.parametrize("quote", ['"', "'"])
    def test_a_quote_and_a_backslash_together_are_escaped_in_that_quote_form(self, quote):
        assert escape_for_display("a\\" + quote + "b", quote) == "a\\\\\\" + quote + "b"

    def test_the_other_quote_is_left_alone(self):
        assert escape_for_display("it's", '"') == "it's"
        assert escape_for_display('a"b', "'") == 'a"b'

    @pytest.mark.parametrize(
        "block",
        [
            r'{"a\rb"}',
            r'{"a\0b"}',
            r'{"\x01"}',
            r'{"\x7f"}',
            r'{"\x1f\x80"}',
            r'{"\\\""}',
            r"{'\\\''}",
            r'{"it\'s"}',
            r'{"say \"hi\""}',
            r'{"it\'s \"x\" \\ \r \0"}',
            r'{""}',
            r'{"\u00e9\u3042 \uffff"}',
            r'{["a\tb" "c\\d"] "e\nf"}',
            r'{{"a\tb"}}',
        ],
    )
    def test_a_block_with_such_strings_reads_back_as_the_same_values(self, block):
        text = top_block_text(block)
        assert run(f"{block} eval") == run(f"{text} eval")
        # showing again changes nothing: the text is a fixed point
        assert top_block_text(text) == text

    @pytest.mark.parametrize("quote", ['"', "'"])
    def test_both_quote_kinds_in_a_block_read_back(self, quote):
        block = f"{{{quote}a\\tb\\\\{quote}}}"
        assert run(f"{block} eval") == run(f"{top_block_text(block)} eval") == ["a\tb\\"]


class TestRawOutput:
    def test_echo_writes_the_characters_not_the_escapes(self, capsys):
        run(r'"a\tb\\c\x41" echo')
        assert capsys.readouterr().out == "a\tb\\cA\n"

    def test_str_of_a_string_is_the_raw_text(self):
        assert run(r'"a\tb" str') == ["a\tb"]
        assert run(r'"\x01\0" str len') == [2]

    def test_echo_of_a_string_with_both_quotes(self, capsys):
        run(r'"it\'s \"q\"" echo')
        assert capsys.readouterr().out == 'it\'s "q"\n'


class TestMultibyteFromUnicodeEscapes:
    def test_len_counts_characters(self):
        assert run(r'"\u00e9\u3042x" len') == [3]

    def test_at_picks_a_character(self):
        assert run(r'"\u00e9\u3042x" 1 at') == ["あ"]

    def test_at_the_first_and_last_character(self):
        assert run(r'"\u00e9\u3042x" 0 at') == ["é"]
        assert run(r'"\u00e9\u3042x" 2 at') == ["x"]

    def test_slice_cuts_between_characters(self):
        assert run(r'"\u00e9\u3042x" 1 2 slice') == ["あ"]

    def test_slice_of_everything(self):
        assert run(r'"\u00e9\u3042x" 0 3 slice') == ["éあx"]

    def test_nth_picks_a_character_and_keeps_the_string(self):
        assert run(r'"\u3042\u3044" 1 nth') == ["あい", "い"]

    def test_a_multibyte_escape_equals_the_literal_character(self):
        assert run('"\\u3042" "あ" ==') == [True]


class TestStringsSplicedIntoBlocks:
    @pytest.mark.parametrize(
        "value",
        [r'"a\tb"', r'"it\'s \"q\" \\ \r"', r'"\x01\0"', r'"\u3042"', r'""'],
    )
    def test_sub_wraps_a_string_and_the_block_shows_it_so_that_it_reads_back(self, value):
        text = top_block_text(f"{value} sub")
        assert run(f"{value} sub eval") == run(f"{text} eval") == run(value)

    def test_sub_of_a_string_shows_the_escape(self):
        assert top_block_text(r'"a\tb" sub') == '{"a\\tb"}'

    def test_a_spliced_string_is_still_a_string_when_run(self):
        (value,) = run(r'"a\tb" sub eval')
        assert isinstance(value, String)

    def test_subn_of_strings_with_escapes_reads_back(self):
        text = top_block_text(r'"a\tb" "c\nd" 2 subn')
        assert run(f"{text} eval") == ["a\tb", "c\nd"]


class TestMacroInterpolation:
    @pytest.mark.parametrize(
        "value",
        [r'"a\tb"', r'"it\'s \"q\" \\ \r \0"', r'"\u3042\x01"'],
    )
    def test_a_macro_hands_the_string_through_unchanged(self, value):
        assert run("{x} {{x}} :m defmacro " + f"{value} m") == run(value)

    def test_a_macro_using_the_string_twice_gets_two_copies(self):
        assert run(r'{x} {{x x +}} :m defmacro "a\tb" m') == ["a\tba\tb"]

    def test_a_string_in_a_nested_block_of_a_macro_expansion_reads_back(self):
        assert run(r'{x} {{{x}}} :m defmacro "a\tb" m eval') == ["a\tb"]

    def test_a_macro_expansion_block_shows_the_escape(self):
        assert top_block_text(r'{x} {{{x}}} :m defmacro "a\tb" m') == '{"a\\tb"}'

    def test_a_macro_with_a_string_holding_both_quotes_and_a_backslash(self):
        assert run(r'{x} {{x len}} :m defmacro "it\'s \"q\"\\" m') == [9]


class TestWhereABadEscapeIsReported:
    def test_a_side_effect_before_the_bad_literal_still_happens(self, capsys):
        with pytest.raises(StackerSyntaxError, match="unknown escape"):
            run(r'"ok" echo "a\q"')
        assert capsys.readouterr().out == "ok\n"

    def test_values_pushed_before_the_bad_literal_stay_on_the_stack(self):
        stacker = Stacker()
        with pytest.raises(StackerSyntaxError):
            stacker.process_expression(r'1 2 "a\q" 3')
        assert list(stacker.stack) == [1, 2]

    def test_words_after_the_bad_literal_do_not_run(self, capsys):
        with pytest.raises(StackerSyntaxError):
            run(r'"a\q" "late" echo')
        assert capsys.readouterr().out == ""

    def test_a_bad_escape_inside_a_block_fails_when_the_block_is_built(self, capsys):
        with pytest.raises(StackerSyntaxError, match="unknown escape"):
            run(r'"first" echo {"a\q" "inside" echo}')
        assert capsys.readouterr().out == "first\n"

    def test_a_bad_block_is_not_pushed(self):
        stacker = Stacker()
        with pytest.raises(StackerSyntaxError):
            stacker.process_expression(r'{"a\q"}')
        assert list(stacker.stack) == []

    def test_a_bad_escape_in_a_block_body_is_not_run_by_a_defun(self):
        with pytest.raises(StackerSyntaxError):
            run(r'{} {"a\q"} :f defun')

    def test_the_next_line_still_works_after_a_bad_escape(self):
        stacker = Stacker()
        with pytest.raises(StackerSyntaxError):
            stacker.process_expression(r'"a\q"')
        stacker.process_expression(r'"a\tb" len')
        assert list(stacker.stack) == [3]

    def test_a_name_is_not_taken_for_a_string_with_a_backslash(self):
        with pytest.raises(UndefinedSymbolError):
            run(r"a\tb")
