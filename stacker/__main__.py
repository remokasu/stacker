import argparse
import importlib
import logging
import os
import shutil
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from types import TracebackType

import stacker
from stacker.engine import recursion
from stacker.engine.recursion import (
    DEFAULT_RECURSION_LIMIT,
    HOST_RECURSION_LIMIT,
    NO_LIMIT,
)
from stacker.lib import disp_logo
from stacker.lib.config import plugins_dir_path, stacker_dotfile_path
from stacker.runtime.exec_modes import CommandLineMode, ReplMode, ScriptMode
from stacker.stacker import Stacker
from stacker.util import colored
from stacker.version import __version__

parser = argparse.ArgumentParser(description="Stacker command line interface.")
parser.add_argument(
    "--addplugin", metavar="path", type=str, help="Path to the plugin to add."
)
parser.add_argument("--version", action="version", version=f"Stacker {__version__}")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument(
    "--no-compile",
    action="store_true",
    help="Do not compile the blocks that run often; run every block in the interpreter.",
)
parser.add_argument("-e", default=None, help="Execute the given command.")
parser.add_argument(
    "--recursion-limit",
    metavar="N",
    type=int,
    default=DEFAULT_RECURSION_LIMIT,
    help=(
        "How deep a program may nest its calls, blocks and loops "
        f"(default {DEFAULT_RECURSION_LIMIT}; {NO_LIMIT} for no limit)."
    ),
)
parser.add_argument("script", nargs="?", default=None, help="Script file to run.")
parser.add_argument(
    "args",
    nargs=argparse.REMAINDER,
    help="Arguments for the script (the word `args` reads them); with -e, every positional is one.",
)
argv = parser.parse_args()
if argv.e is not None and argv.script is not None:
    # -e takes no script: the first positional is an argument like the rest
    argv.args = [argv.script] + argv.args
    argv.script = None
if argv.args and argv.args[0] == "--":
    argv.args = argv.args[1:]

if argv.recursion_limit < 0:
    parser.error(f"--recursion-limit must be {NO_LIMIT} (no limit) or more, got {argv.recursion_limit}")
recursion.set_limit(argv.recursion_limit)

# The host's own depth, for the Python words that run Stacker code and for the values whose structure is shown
sys.setrecursionlimit(HOST_RECURSION_LIMIT)


def load_plugins(stacker: Stacker, plugins_dir_path: str) -> bool:
    """Load plugins from the plugins directory.
    :param stacker: The Stacker instance to pass to the plugins.
    :return: None
    """
    # Add the plugin directory path
    sys.path.insert(0, plugins_dir_path)
    for filename in os.listdir(plugins_dir_path):
        try:
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = os.path.splitext(filename)[0]  # remove .py extension
                plugin_module = importlib.import_module(module_name)
                plugin_module.setup(stacker)
                logging.debug(f"Loaded plugin '{module_name}'.")
        except Exception as e:
            print(colored(f"Failed load plugin ({filename}). {e}", "red"))
            sys.path.pop(0)
            return False
    sys.path.pop(0)
    return True


def load_dotfile(stacker: Stacker, dotfile_path: str | Path) -> None:
    """Load the dotfile.
    :param stacker: The Stacker instance to pass to the plugins.
    :param dotfile_path: The path to the dotfile.
    :return: None
    """
    try:
        if not os.path.isfile(dotfile_path):
            print(f"Error: The file '{dotfile_path}' does not exist.")
            return
        stacker.include(str(dotfile_path))
    except Exception as e:
        print(f"An error occurred while loading the dotfile: {e!s}")


def copy_plugin_to_install_dir(plugin_path: str, debug_mode: bool) -> None:
    try:
        # Get the installation directory of Stacker
        # stacker_dist = get_distribution("pystacker")
        # plugin_dir = stacker_dist.location + "/stacker/plugins"
        stacker_package_dir = os.path.dirname(os.path.abspath(stacker.__file__))
        plugin_dir = os.path.join(stacker_package_dir, "plugins")

        # Check if the plugin file exists
        if not os.path.isfile(plugin_path):
            print(f"Error: The file '{plugin_path}' does not exist.")
            return

        # Copy the plugin file to the Stacker's installation directory
        assert Path(plugin_dir).exists
        shutil.copy(plugin_path, plugin_dir)
        print(f"Successfully added the plugin '{plugin_path}' to Stacker.")
        print(plugin_dir)
    except Exception as e:
        print(
            f"An error occurred while adding the plugin ({plugin_path!s}): {e!s}"
        )
        if debug_mode:
            traceback.print_exc()


def silent_on_interrupt(report: Callable[[type[BaseException], BaseException, TracebackType | None], object]) -> Callable:
    """Wraps an exception hook so that it says nothing for Ctrl-C.

    The host still flushes the streams and ends the process by the signal,
    so a shell loop around the program stops too; exiting with a code of
    its own would let the loop go on to its next round.

    Args:
        report: The hook in place, called for every other exception.

    Returns:
        The hook to install with ``sys.excepthook``.
    """

    def hook(kind: type[BaseException], value: BaseException, tb: TracebackType | None) -> None:
        if not issubclass(kind, KeyboardInterrupt):
            report(kind, value, tb)

    return hook


def main() -> None:
    """Main entry point for the Stacker CLI."""
    # With --debug, the traceback of Ctrl-C shows where the program was
    if not argv.debug:
        sys.excepthook = silent_on_interrupt(sys.excepthook)

    # add plugin
    if argv.addplugin:
        copy_plugin_to_install_dir(argv.addplugin, argv.debug)
        return

    # Scripts and files are UTF-8; so are the standard streams, whatever the
    # host's locale says (a console is written through the host's own path)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")

    if argv.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    rpn_calculator = Stacker(compile=not argv.no_compile)
    rpn_calculator.arguments = list(argv.args)

    # load plugins from the Stacker's installation directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(script_dir, plugins_dir_path)
    if not load_plugins(rpn_calculator, plugins_dir):
        sys.exit(1)

    # load plugins from current directory
    plugins_dir = os.path.join(os.getcwd(), plugins_dir_path)
    if Path(plugins_dir).exists():
        if not load_plugins(rpn_calculator, plugins_dir):
            sys.exit(1)

    if argv.e is not None:
        # Execute the given command
        commandline_mode = CommandLineMode(rpn_calculator)
        if stacker_dotfile_path.exists():
            commandline_mode.run_stackerrc(stacker_dotfile_path)
        commandline_mode.run(argv.e)
        return

    if argv.script:
        # Script Mode
        script_mode = ScriptMode(rpn_calculator)
        if stacker_dotfile_path.exists():
            script_mode.run_stackerrc(stacker_dotfile_path)
        if argv.debug:
            script_mode.debug_mode()
        rpn_calculator.clear_trace()
        script_mode.run(argv.script)
    else:
        # REPL mode
        repl_mode = ReplMode(rpn_calculator)
        # execute the dotfile
        if stacker_dotfile_path.exists():
            repl_mode.run_stackerrc(stacker_dotfile_path)
        if argv.debug:
            repl_mode.debug_mode()
        if repl_mode.disp_logo_mode:
            disp_logo()
        rpn_calculator.clear_trace()
        repl_mode.run()


if __name__ == "__main__":
    main()
