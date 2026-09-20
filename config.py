import os
import subprocess
from pathlib import Path


def open_editor(filename):
    subprocess.run(["kitty", "-e", "nvim", str(filename)], check=True)


def latex_document(latex):
    return (
        r"""
        \documentclass[12pt,border=12pt]{standalone}

        \usepackage[utf8]{inputenc}
        \usepackage[T1]{fontenc}
        \usepackage{textcomp}
        \usepackage{amsmath, amssymb}
        \newcommand{\R}{\mathbb R}

        \begin{document}
    """
        + latex
        + r"\end{document}"
    )


config = {
    # For example '~/.config/rofi/ribbon.rasi' or None
    "rofi_theme": None,
    "toggle_key": "F12",
    "style_leader": "space",
    "style_timeout": 1.0,
    # Font that's used to add text in inkscape
    "font": "monospace",
    "font_size": 10,
    "open_editor": open_editor,
    "latex_document": latex_document,
}


# From https://stackoverflow.com/a/67692
def import_file(name, path):
    import importlib.util as util

    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "inkscape-shortcut-manager"

if (CONFIG_PATH / "config.py").exists():
    userconfig = import_file("user_shortcut_config", CONFIG_PATH / "config.py").config
    config.update(userconfig)
