"""
Error formatter for Stacker with Clang-style output.

Provides rich, visual error messages with:
- File location and line number
- Source code context
- Visual indicators (arrows, highlighting)
- Color-coded severity levels
"""

from __future__ import annotations
from typing import Optional
import sys


class ErrorFormatter:
    """Formats error messages in a Clang-like style with visual indicators."""

    # ANSI color codes
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    @staticmethod
    def _supports_color() -> bool:
        """Check if the terminal supports color output."""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    @classmethod
    def format_error(
        cls,
        filename: Optional[str],
        line_number: Optional[int],
        column: Optional[int],
        error_type: str,
        message: str,
        source_line: Optional[str] = None,
        hint: Optional[str] = None
    ) -> str:
        """
        Format an error message in Clang style.

        Args:
            filename: Source file name (None for REPL)
            line_number: Line number where error occurred
            column: Column number where error occurred
            error_type: Type of error (e.g., "SyntaxError", "RuntimeError")
            message: Error message
            source_line: The source code line that caused the error
            hint: Optional hint for fixing the error

        Returns:
            Formatted error message string
        """
        use_color = cls._supports_color()
        lines = []

        # Location line: "filename:line:column: error: message"
        location_parts = []
        if filename:
            location_parts.append(f"{filename}")
        if line_number is not None:
            location_parts.append(f"{line_number}")
        if column is not None:
            location_parts.append(f"{column}")

        location = ":".join(location_parts) if location_parts else "stacker"

        if use_color:
            error_label = f"{cls.BOLD}{cls.RED}error:{cls.RESET}"
            location = f"{cls.BOLD}{location}{cls.RESET}"
        else:
            error_label = "error:"

        lines.append(f"{location}: {error_label} {message}")

        # Add error type if different from "error"
        if error_type and error_type.lower() != "error":
            if use_color:
                lines.append(f"  {cls.GRAY}[{error_type}]{cls.RESET}")
            else:
                lines.append(f"  [{error_type}]")

        # Source code context with visual indicator
        if source_line is not None and line_number is not None:
            # Line number padding
            line_num_str = str(line_number)
            padding = len(line_num_str) + 1

            if use_color:
                line_prefix = f"{cls.BLUE}{line_num_str} |{cls.RESET} "
                blank_prefix = f"{cls.BLUE}{' ' * len(line_num_str)} |{cls.RESET} "
            else:
                line_prefix = f"{line_num_str} | "
                blank_prefix = f"{' ' * len(line_num_str)} | "

            lines.append(blank_prefix)
            lines.append(f"{line_prefix}{source_line}")

            # Visual indicator (caret ^ or arrow)
            if column is not None and column > 0:
                # Adjust for line number prefix
                indicator_pos = column - 1
                spaces = ' ' * indicator_pos

                if use_color:
                    indicator = f"{blank_prefix}{spaces}{cls.BOLD}{cls.GREEN}^{cls.RESET}"
                else:
                    indicator = f"{blank_prefix}{spaces}^"

                lines.append(indicator)

        # Optional hint
        if hint:
            if use_color:
                lines.append(f"{cls.BOLD}{cls.CYAN}hint:{cls.RESET} {hint}")
            else:
                lines.append(f"hint: {hint}")

        return "\n".join(lines)

    @classmethod
    def format_warning(
        cls,
        filename: Optional[str],
        line_number: Optional[int],
        column: Optional[int],
        message: str,
        source_line: Optional[str] = None,
        hint: Optional[str] = None
    ) -> str:
        """Format a warning message in Clang style."""
        use_color = cls._supports_color()
        lines = []

        location_parts = []
        if filename:
            location_parts.append(f"{filename}")
        if line_number is not None:
            location_parts.append(f"{line_number}")
        if column is not None:
            location_parts.append(f"{column}")

        location = ":".join(location_parts) if location_parts else "stacker"

        if use_color:
            warning_label = f"{cls.BOLD}{cls.YELLOW}warning:{cls.RESET}"
            location = f"{cls.BOLD}{location}{cls.RESET}"
        else:
            warning_label = "warning:"

        lines.append(f"{location}: {warning_label} {message}")

        if source_line is not None and line_number is not None:
            line_num_str = str(line_number)

            if use_color:
                line_prefix = f"{cls.BLUE}{line_num_str} |{cls.RESET} "
                blank_prefix = f"{cls.BLUE}{' ' * len(line_num_str)} |{cls.RESET} "
            else:
                line_prefix = f"{line_num_str} | "
                blank_prefix = f"{' ' * len(line_num_str)} | "

            lines.append(blank_prefix)
            lines.append(f"{line_prefix}{source_line}")

            if column is not None and column > 0:
                indicator_pos = column - 1
                spaces = ' ' * indicator_pos

                if use_color:
                    indicator = f"{blank_prefix}{spaces}{cls.BOLD}{cls.YELLOW}^{cls.RESET}"
                else:
                    indicator = f"{blank_prefix}{spaces}^"

                lines.append(indicator)

        if hint:
            if use_color:
                lines.append(f"{cls.BOLD}{cls.CYAN}hint:{cls.RESET} {hint}")
            else:
                lines.append(f"hint: {hint}")

        return "\n".join(lines)


class StackerErrorWithContext(Exception):
    """
    Enhanced Stacker error with source context information.

    This exception stores additional information needed for
    rich error formatting.
    """

    def __init__(
        self,
        message: str,
        error_type: str = "StackerError",
        filename: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        source_line: Optional[str] = None,
        hint: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.filename = filename
        self.line_number = line_number
        self.column = column
        self.source_line = source_line
        self.hint = hint

    def format(self) -> str:
        """Format this error using the ErrorFormatter."""
        return ErrorFormatter.format_error(
            filename=self.filename,
            line_number=self.line_number,
            column=self.column,
            error_type=self.error_type,
            message=self.message,
            source_line=self.source_line,
            hint=self.hint
        )

    def __str__(self) -> str:
        """Return formatted error message."""
        return self.format()
