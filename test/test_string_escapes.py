"""A string literal reads escapes; the display writes them back so a block's text reads as the same block."""

import pytest

from stacker import Stacker
from stacker.engine.data_type import String
from stacker.error import StackerSyntaxError
from stacker.syntax.token_rules import decode_string_token, escape_for_display
from stacker.util.disp import plain_text


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestReadingEscapes:
    @pytest.mark.parametrize(
        "literal, text",
        [
            (r'"a\nb"', "a\nb"),
            (r'"a\tb"', "a\tb"),
            (r'"a\rb"', "a\rb"),
            (r'"a\0b"', "a\0b"),
            (r'"a\\b"', "a\\b"),
            (r'"\"42\""', '"42"'),
            (r'"it\'s"', "it's"),
            (r"'it\'s'", "it's"),
            (r"'say \"hi\"'", 'say "hi"'),
            (r'"\x41\u00e9"', "A\u00e9"),
            (r'"C:\\new"', "C:\\new"),
            (r'"""a\tb"""', "a\tb"),
            (r"'''a\nb'''", "a\nb"),
            ('"no escapes"', "no escapes"),
        ],
    )
    def test_a_literal_reads_its_escapes(self, literal, text):
        assert run(literal) == [text]
        assert run(f"{{{literal}}} eval") == [text]
        assert run(f"[{literal}]") == [[text]]

    def test_the_value_is_a_string_literal(self):
        assert isinstance(run(r'"a\nb"')[0], String)

    @pytest.mark.parametrize(
        "literal, message",
        [
            (r'"a\qb"', "unknown escape `\\q`"),
            (r'"\x4"', "`\\x` in a string takes 2 hex digits"),
            (r'"\u12"', "`\\u` in a string takes 4 hex digits"),
            (r'"\uD800"', "is not a character"),
            (r'"\xzz"', "`\\x` in a string takes 2 hex digits"),
        ],
    )
    def test_an_escape_that_is_not_one_is_an_error(self, literal, message):
        with pytest.raises(StackerSyntaxError, match=message.replace("\\", "\\\\").replace("`", "`")):
            run(literal)
        with pytest.raises(StackerSyntaxError):
            run(f"[{literal}]")
        with pytest.raises(StackerSyntaxError):
            run(f"{{{literal}}} eval")

    def test_a_lone_backslash_at_the_end_of_a_token(self):
        with pytest.raises(StackerSyntaxError, match="lone backslash"):
            decode_string_token('"abc\\"')

    def test_a_list_literal_string_is_read_once(self):
        # read twice, `\\b` would become a backspace and `\t` a tab inside the tab
        assert run(r'["a\\tb"] 0 at') == ["a\\tb"]
        assert run(r'["a\\b"] 0 at len') == [3]


class TestWritingEscapes:
    @pytest.mark.parametrize(
        "text, shown",
        [
            ("a\tb", "'a\\tb'"),
            ("a\nb", "'a\\nb'"),
            ("a\\b", "'a\\\\b'"),
            ("\x01", "'\\x01'"),
            ("it's", "'it's'"),
            ('say "hi"', "'say \"hi\"'"),
        ],
    )
    def test_the_stack_shows_control_characters_as_escapes(self, text, shown):
        assert plain_text(run("x")[0] if False else String(text)) == shown

    def test_a_quote_is_escaped_only_when_asked(self):
        assert escape_for_display("it's") == "it's"
        assert escape_for_display("it's", "'") == "it\\'s"
        assert escape_for_display('a"b', '"') == 'a\\"b'

    @pytest.mark.parametrize(
        "block, shown",
        [
            (r'{"a\tb"}', '{"a\\tb"}'),
            (r'{"it\'s"}', '{"it\'s"}'),
            (r'{"say \"hi\""}', "{'say \"hi\"'}"),
            (r'{"it\'s \"x\""}', '{"it\'s \\"x\\""}'),
            (r'{"a\\b"}', '{"a\\\\b"}'),
        ],
    )
    def test_a_block_shows_its_strings_so_that_they_read_back(self, block, shown):
        stacker = Stacker()
        stacker.process_expression(block)
        text = str(stacker.stack[-1])
        assert text == shown
        again = Stacker()
        again.process_expression(f"{block} eval")
        reparsed = Stacker()
        reparsed.process_expression(f"{text} eval")
        assert list(reparsed.stack) == list(again.stack)

    def test_echo_and_str_give_the_raw_text(self, capsys):
        run(r'"a\tb" echo')
        assert capsys.readouterr().out == "a\tb\n"
        assert run(r'"a\tb" str len') == [3]
