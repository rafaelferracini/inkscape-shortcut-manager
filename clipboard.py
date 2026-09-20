"""Use the X11 selection: the managed Inkscape always runs on X11/XWayland."""
import subprocess
import time
from Xlib.display import Display
from Xlib import X


def copy(string, target=None):
    args = ['xclip', '-selection', 'clipboard']
    if target is not None:
        args += ['-target', target]
    # Wait for the new selection owner instead of racing Inkscape's paste.
    disp = Display()
    try:
        selection = disp.intern_atom('CLIPBOARD')
        previous = disp.get_selection_owner(selection)
        subprocess.run(args, input=string, text=True, check=True, timeout=5)
        deadline = time.monotonic() + 2
        while disp.get_selection_owner(selection) == previous:
            if time.monotonic() >= deadline:
                raise RuntimeError('xclip não assumiu a área de transferência.')
            time.sleep(0.01)
    finally:
        disp.close()


def get(target=None):
    args = ['xclip', '-selection', 'clipboard', '-o']
    if target is not None:
        args += ['-target', target]
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=3).stdout


def get_after_copy(manager, target):
    """Wait for Inkscape's asynchronous Ctrl+C before reading the SVG."""
    disp = Display()
    try:
        selection = disp.intern_atom('CLIPBOARD')
        # Replace any previous Inkscape ownership with our own sentinel first.
        copy('', 'UTF8_STRING')
        old = disp.get_selection_owner(selection)
        manager.press('c', X.ControlMask)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if disp.get_selection_owner(selection) != old:
                try:
                    return get(target)
                except subprocess.CalledProcessError:
                    pass
            time.sleep(0.02)
        raise RuntimeError('Nenhum SVG copiado. Selecione um objeto no Inkscape.')
    finally:
        disp.close()
