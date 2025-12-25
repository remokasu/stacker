import argparse
import importlib
import logging
import os
import shutil
import sys
import traceback
from pathlib import Path
import stacker

from stacker.runtime.exec_modes import CommandLineMode, ReplMode, ScriptMode

from stacker.lib import disp_logo
from stacker.lib.config import plugins_dir_path, stacker_dotfile_path
from stacker.stacker import Stacker
from stacker.util import colored

parser = argparse.ArgumentParser(description="Stacker command line interface.")
parser.add_argument(
    "--addplugin", metavar="path", type=str, help="Path to the plugin to add."
)
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("-e", default=None, help="Execute the given command.")
parser.add_argument("script", nargs="?", default=None, help="Script file to run.")
argv = parser.parse_args()

sys.setrecursionlimit(1 << 30)


def load_stacker_lib(stacker: Stacker, dir_path) -> bool:
    """Load the Stacker library from the specified directory.
    :param stacker: The Stacker instance to pass to the plugins.
    :param dir_path: The directory to load the Stacker library from.
    :return: None
    """
    # Add the library directory path
    sys.path.insert(0, dir_path)
    for filename in os.listdir(dir_path):
        try:
            if filename.endswith(".stk"):
                include_stacker_script = Path(dir_path) / filename
                stacker.include(str(include_stacker_script))
        except Exception as e:
            print(colored(f"Failed load slib ({filename}). {e}", "red"))
            sys.path.pop(0)
            return False
    sys.path.pop(0)
    return True


def load_plugins(stacker: Stacker, plugins_dir_path) -> bool:
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
        print(f"An error occurred while loading the dotfile: {str(e)}")


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
            f"An error occurred while adding the plugin ({str(plugin_path)}): {str(e)}"
        )
        if debug_mode:
            traceback.print_exc()


def main():
    """Main entry point for the Stacker CLI."""
    # add plugin
    if argv.addplugin:
        copy_plugin_to_install_dir(argv.addplugin, argv.debug)
        return

    if argv.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    rpn_calculator = Stacker()

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

    # load the Stacker library
    library_dir = os.path.join(script_dir, "slib")
    if not load_stacker_lib(rpn_calculator, library_dir):
        sys.exit(1)

    if argv.e is not None:
        # Execute the given command
        commandline_mode = CommandLineMode(rpn_calculator)
        if stacker_dotfile_path.exists():
            commandline_mode.execute_stacker_dotfile(stacker_dotfile_path)
        commandline_mode.run(argv.e)
        return

    if argv.script:
        # Script Mode
        script_mode = ScriptMode(rpn_calculator)
        if stacker_dotfile_path.exists():
            script_mode.execute_stacker_dotfile(stacker_dotfile_path)
        if argv.debug:
            script_mode.debug_mode()
        rpn_calculator.clear_trace()
        script_mode.run(argv.script)
    else:
        # REPL mode
        repl_mode = ReplMode(rpn_calculator)
        # execute the dotfile
        if stacker_dotfile_path.exists():
            repl_mode.execute_stacker_dotfile(stacker_dotfile_path)
        if argv.debug:
            repl_mode.debug_mode()
        if repl_mode.disp_logo_mode:
            disp_logo()
        rpn_calculator.clear_trace()
        repl_mode.run()


if __name__ == "__main__":
    main()
