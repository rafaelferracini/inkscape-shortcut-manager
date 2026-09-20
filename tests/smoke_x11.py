"""Opt-in desktop test. Opens only a temporary Inkscape document."""
import json
import os
import shutil
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def wait_for(check, message, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = check()
        if result:
            return result
        time.sleep(.1)
    raise AssertionError(message)


def main():
    disp = Display()
    processes = []
    previous = json.loads(subprocess.check_output(['hyprctl', '-j', 'activewindow']))
    try:
        with tempfile.TemporaryDirectory(prefix='shortcut-smoke-') as folder:
            folder = Path(folder)
            svg = folder / 'shortcut-smoke.svg'
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><path id="test" d="M 40,40 L 200,180" style="fill:none;stroke:red;stroke-width:2"/></svg>')
            env = dict(os.environ, GDK_BACKEND='x11', XDG_CONFIG_HOME=str(folder / 'config'))
            # Keep the test menu on X11 so XTEST can type into it.
            env.pop('WAYLAND_DISPLAY', None)
            objects = folder / 'config' / 'inkscape-shortcut-manager' / 'objects'
            objects.mkdir(parents=True)
            for source in (Path.home() / '.config/inkscape-shortcut-manager/objects').glob('eixo_*.svg'):
                shutil.copy2(source, objects / source.name)
            with (folder / 'manager.log').open('w+') as log:
                manager = subprocess.Popen([sys.executable, str(ROOT / 'main.py')], env=env, stdout=log, stderr=log, start_new_session=True)
                processes.append(manager)
                proc = subprocess.Popen(['inkscape', '--app-id-tag=shortcutsmoke', str(svg)], env=env,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                processes.append(proc)
                atom = disp.intern_atom('_NET_WM_PID')
                def find():
                    from main import windows
                    for w in windows(disp):
                        prop = w.get_full_property(atom, X.AnyPropertyType)
                        if prop and prop.value[0] == proc.pid and w.get_wm_class() and 'inkscape' in str(w.get_wm_class()).lower():
                            return w
                win = wait_for(find, 'Janela XWayland não apareceu')
                def attached():
                    log.seek(0)
                    return 'Gerenciando janela' in log.read()
                wait_for(attached, 'Gerenciador não detectou janela nova')
                wait_for(lambda: any(c.get('pid') == proc.pid and c.get('mapped') for c in json.loads(subprocess.check_output(['hyprctl', '-j', 'clients']))), 'Janela ainda não mapeada')
                subprocess.run(['xdotool', 'windowactivate', '--sync', str(win.id)], check=True)
                time.sleep(.5)
                def send(kind, key):
                    xtest.fake_input(disp, kind, disp.keysym_to_keycode(XK.string_to_keysym(key)))
                    disp.sync()
                    time.sleep(.05)
                def chord(*keys):
                    for key in keys: send(X.KeyPress, key)
                    for key in reversed(keys): send(X.KeyRelease, key)
                    time.sleep(.3)
                chord('Escape')
                chord('Control_L', 'a')
                chord('space')
                chord('d')
                chord('a')
                time.sleep(1.2)
                chord('Control_L', 's')
                def saved_style():
                    path = ET.parse(svg).getroot().find('.//{http://www.w3.org/2000/svg}path[@id="test"]')
                    return path.attrib.get('style', '')
                wait_for(lambda: 'marker-end:url(' in saved_style() and 'stroke-dasharray:' in saved_style(), 'Acorde d+a não aplicou estilo: ' + saved_style())
                from main import Manager
                from clipboard import get_after_copy
                from constants import TARGET
                sender = Manager(win.id)
                try:
                    copied = get_after_copy(sender, TARGET)
                    assert 'clipboard' in copied
                    ET.fromstring(copied)
                    print('OK: cópia assíncrona do SVG selecionado')
                finally:
                    sender.disp.close()
                print('OK: Espaço → d → a, teclas sequenciais e timeout; seta gravada; Ctrl+A/Ctrl+S preservados')
                chord('z')
                chord('Control_L', 's')
                wait_for(lambda: 'marker-end:url(' not in saved_style(), 'z não desfez o estilo')
                print('OK: z enviado como Ctrl+Z ao Inkscape 1.4.4')
                clients = json.loads(subprocess.check_output(['hyprctl', '-j', 'clients']))
                client = next(c for c in clients if c['pid'] == proc.pid)
                assert client['workspace']['id'] == 5, client
                print('OK: Inkscape abriu no workspace 5')
                def paths():
                    return len(list(ET.parse(svg).getroot().iter('{http://www.w3.org/2000/svg}path')))
                def menu_visible():
                    for w in disp.screen().root.query_tree().children:
                        try:
                            if 'rofi' in str(w.get_wm_class()).lower() and w.get_attributes().map_state == X.IsViewable:
                                return True
                        except Exception:
                            pass
                    return False
                for name in ('eixo_xy', 'eixo_xyz'):
                    before = paths()
                    chord('a')
                    wait_for(menu_visible, 'Menu de objetos não abriu')
                    subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '60', name], check=True)
                    chord('Return')
                    wait_for(lambda: not menu_visible(), 'Menu não fechou')
                    time.sleep(.4)
                    chord('Control_L', 's')
                    wait_for(lambda: paths() > before, 'Objeto não inserido: ' + name)
                    print('OK: objeto selecionado pelo menu e inserido: ' + name)
                log.seek(0)
                print(log.read())
    finally:
        for proc in reversed(processes):
            if proc is manager:
                os.killpg(proc.pid, signal.SIGTERM)
            else:
                proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait()
        disp.close()
        if previous.get('address'):
            subprocess.run(['hyprctl', 'dispatch', 'hl.dsp.focus({ window = ' + json.dumps('address:' + previous['address']) + ' })'], stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
