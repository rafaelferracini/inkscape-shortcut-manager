"""Start one manager per display and open Inkscape using XWayland."""
import os
from pathlib import Path
import subprocess
import sys

from config import CONFIG_PATH


def main():
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    with (CONFIG_PATH / 'manager.log').open('ab') as log:
        subprocess.Popen([sys.executable, str(Path(__file__).with_name('main.py'))],
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         start_new_session=True)
    env = os.environ.copy()
    env['GDK_BACKEND'] = 'x11'
    # A dedicated application ID avoids reusing an existing native Wayland process.
    os.execvpe('inkscape', ['inkscape', '--app-id-tag=shortcutmanager', *sys.argv[1:]], env)


if __name__ == '__main__':
    main()
