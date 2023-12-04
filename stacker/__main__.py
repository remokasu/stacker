import argparse
import traceback
import os
import sys
import shutil
import importlib
import logging

from pkg_resources import get_distribution
from pathlib import Path

from stacker.util import colored
from stacker.stacker import Stacker
from stacker.lib.config import plugins_dir_path
# from stacker.execution_mode import ScriptMode, InteractiveMode
from stacker.exec_modes.interactive_mode import InteractiveMode
from stacker.exec_modes.script_mode import ScriptMode

parser = argparse.ArgumentParser(description='Stacker command line interface.')
parser.add_argument('--addplugin', metavar='path', type=str, help='Path to the plugin to add.')
parser.add_argument('--dmode', action='store_true', help='Enable debug mode')
parser.add_argument('script', nargs='?', default=None, help='Script file to run.')
argv = parser.parse_args()


def load_plugins(stacker: Stacker, plugins_dir_path):
    """ Load plugins from the plugins directory.
    :param stacker: The Stacker instance to pass to the plugins.
    :return: None
    """
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # plugins_dir = os.path.join(script_dir, plugins_dir_path)
    # プラグインディレクトリにパスを追加
    sys.path.insert(0, plugins_dir_path)

    try:
        for filename in os.listdir(plugins_dir_path):
            try:
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = os.path.splitext(filename)[0]  # remove .py extension
                    plugin_module = importlib.import_module(module_name)
                    plugin_module.setup(stacker)
                    logging.debug(f"Loaded plugin '{module_name}'.")
            except Exception as e:
                print(colored(f"[ERROR]{e}", "red"))
            finally:
                continue
    except FileNotFoundError:
        print("Warning: plugins folder not found. Skipping plugin loading.")
    finally:
        # プラグインディレクトリからパスを削除
        sys.path.pop(0)


def copy_plugin_to_install_dir(plugin_path: str, dmode: bool) -> None:
    try:
        # Get the installation directory of Stacker
        stacker_dist = get_distribution("pystacker")
        plugin_dir = stacker_dist.location + "/stacker/plugins"

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
        print(f"An error occurred while adding the plugin: {str(e)}")
        if dmode:
            traceback.print_exc()


def main():
    """ Main entry point for the Stacker CLI.
    """
    # add plugin
    if argv.addplugin:
        copy_plugin_to_install_dir(argv.addplugin, argv.dmode)
        return

    if argv.dmode:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    rpn_calculator = Stacker()

    # load plugins
    plugins_dir = os.path.join(os.getcwd(), plugins_dir_path)
    if Path(plugins_dir).exists():  # カレントディレクトリにpluginsディレクトリがある場合
        load_plugins(rpn_calculator, plugins_dir)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(script_dir, plugins_dir_path)
    load_plugins(rpn_calculator, plugins_dir)

    if argv.script:
        # Script Mode
        script_mode = ScriptMode(rpn_calculator)
        if argv.dmode:
            script_mode.debug_mode()
        script_mode.run(argv.script)
    else:
        # Interactive mode
        interactive_mode = InteractiveMode(rpn_calculator)
        if argv.dmode:
            interactive_mode.debug_mode()
        interactive_mode.run()


if __name__ == "__main__":
    main()
