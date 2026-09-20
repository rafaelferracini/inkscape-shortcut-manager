"""Inkscape keyboard manager for X11 and XWayland (not native Wayland)."""
import argparse
import fcntl
import logging
import os
from pathlib import Path
import shutil
import select
import threading
import time

from Xlib import X, XK, error
from Xlib.display import Display
from Xlib.protocol import event

from config import CONFIG_PATH, config
from normal import normal_mode, expire_sequence

LOG = logging.getLogger(__name__)
ACTION_LOCK = threading.RLock()  # The clipboard is shared by all documents.
SPECIAL_KEYS = {XK.string_to_keysym(k): k for k in ('Escape', 'BackSpace', 'Return', 'Tab', 'Delete', config['toggle_key'], config['style_leader'])}


class Manager:
    def __init__(self, inkscape_id):
        self.id = inkscape_id
        self.disp = Display()
        self.root = self.disp.screen().root
        self.inkscape = self.disp.create_resource_object('window', inkscape_id)
        self.mode = normal_mode
        self.events = []
        self.pressed = set()
        self.down = set()
        self.prefix = []
        self.style_keys = set()
        self.style_deadline = None

    def event(self, name, detail, state):
        return name(time=X.CurrentTime, root=self.root, window=self.inkscape,
                    same_screen=1, child=X.NONE, root_x=0, root_y=0,
                    event_x=0, event_y=0, state=state, detail=detail)

    def string_to_keycode(self, key):
        return self.disp.keysym_to_keycode(XK.string_to_keysym(key))

    def press(self, key, mask=X.NONE):
        keycode = self.string_to_keycode(key)
        if not keycode:
            raise ValueError(f'Tecla indisponível no layout: {key}')
        for kind in (event.KeyPress, event.KeyRelease):
            self.inkscape.send_event(self.event(kind, keycode, mask), propagate=True)
        self.disp.sync()

    def forward(self, evt):
        self.inkscape.send_event(evt, propagate=True)
        self.disp.flush()

    def grab(self):
        # Leave Ctrl/Alt/Super/AltGr combinations to Inkscape/the compositor.
        # Include NumLock and CapsLock in the grabs.
        for mask in (0, X.ShiftMask, X.LockMask, X.Mod2Mask,
                     X.ShiftMask | X.LockMask, X.ShiftMask | X.Mod2Mask,
                     X.LockMask | X.Mod2Mask,
                     X.ShiftMask | X.LockMask | X.Mod2Mask):
            self.inkscape.grab_key(X.AnyKey, mask, False, X.GrabModeAsync, X.GrabModeAsync)
        self.inkscape.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask |
                                       X.StructureNotifyMask | X.FocusChangeMask)
        self.disp.sync()

    def reset(self):
        self.events.clear()
        self.pressed.clear()
        self.down.clear()
        self.prefix.clear()
        self.style_keys.clear()
        self.style_deadline = None
        self.mode = normal_mode

    def listen(self):
        try:
            self.grab()
            LOG.info('Gerenciando janela Inkscape 0x%x', self.id)
            while True:
                if not self.disp.pending_events():
                    timeout = None if self.style_deadline is None else max(0, self.style_deadline - time.monotonic())
                    ready, _, _ = select.select([self.disp.fileno()], [], [], timeout)
                    if not ready:
                        try:
                            with ACTION_LOCK:
                                expire_sequence(self)
                        except Exception:
                            LOG.exception('Falha ao aplicar sequência de estilo')
                            self.reset()
                        continue
                evt = self.disp.next_event()
                if evt.type == X.DestroyNotify and evt.window.id == self.id:
                    return
                if evt.type == X.FocusOut and evt.mode == X.NotifyNormal:
                    self.reset()
                if evt.type not in (X.KeyPress, X.KeyRelease):
                    continue
                keysym = self.disp.keycode_to_keysym(evt.detail, 0)
                char = SPECIAL_KEYS.get(keysym, XK.keysym_to_string(keysym))
                try:
                    with ACTION_LOCK:
                        self.mode(self, evt, char)
                except Exception:
                    LOG.exception('Falha no atalho; voltando ao modo normal')
                    self.reset()
        finally:
            self.disp.close()  # Closing the connection releases its grabs.


def is_inkscape(window):
    try:
        classes = window.get_wm_class() or ()
        return any('inkscape' in value.lower() for value in classes)
    except error.BadWindow:
        return False


def windows(disp):
    root = disp.screen().root
    # EWMH covers reparenting window managers; root children cover XWayland.
    found = {w.id: w for w in root.query_tree().children}
    prop = root.get_full_property(disp.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
    if prop:
        for wid in prop.value:
            found[int(wid)] = disp.create_resource_object('window', int(wid))
    result = []
    normal_type = disp.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL')
    type_atom = disp.intern_atom('_NET_WM_WINDOW_TYPE')
    for w in found.values():
        try:
            if not is_inkscape(w) or w.get_attributes().map_state != X.IsViewable:
                continue
            kind = w.get_full_property(type_atom, X.AnyPropertyType)
            if kind is None or normal_type in kind.value:
                result.append(w)
        except error.BadWindow:
            pass
    return result


def create(wid):
    try:
        Manager(wid).listen()
    except error.BadWindow:
        pass  # Window closed between discovery and attachment.
    except Exception:
        LOG.exception('Falha ao gerenciar janela 0x%x', wid)


def doctor():
    failed = False
    for name in ('inkscape', 'xclip', 'rofi', 'kitty', 'nvim', 'pdflatex', 'pdf2svg'):
        path = shutil.which(name)
        print(f'{name}: {path or "NÃO ENCONTRADO"}')
        if name in ('inkscape', 'xclip') and not path:
            failed = True
    print(f'Configuração: {CONFIG_PATH}')
    print(f'Sessão: {os.environ.get("XDG_SESSION_TYPE", "desconhecida")}')
    try:
        disp = Display()
        matches = windows(disp)
        print(f'Conexão X11/XWayland: OK; janelas Inkscape compatíveis: {len(matches)}')
        disp.close()
    except error.DisplayConnectionError as exc:
        print(f'Conexão X11/XWayland: FALHOU ({exc})')
        failed = True
    if os.environ.get('WAYLAND_DISPLAY'):
        print('Abra as figuras com inkscape-managed; janelas Wayland nativas não são capturadas.')
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--doctor', action='store_true', help='verificar dependências e conexão X11')
    args = parser.parse_args()
    if args.doctor:
        return doctor()
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    display_name = os.environ.get('DISPLAY', 'none').replace('/', '_')
    with (CONFIG_PATH / f'manager-{display_name}.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            LOG.info('O gerenciador já está ativo neste display.')
            return 0
        disp = Display()
        workers = {}
        LOG.info('Monitorando X11/XWayland. Use inkscape-managed para abrir figuras.')
        try:
            while True:
                # WM_CLASS is normally set AFTER CreateNotify. Rescanning also
                # catches MapNotify/property changes and avoids duplicate grabs.
                for window in windows(disp):
                    if window.id not in workers or not workers[window.id].is_alive():
                        worker = threading.Thread(target=create, args=(window.id,), daemon=True)
                        workers[window.id] = worker
                        worker.start()
                workers = {wid: t for wid, t in workers.items() if t.is_alive()}
                time.sleep(0.25)
        finally:
            disp.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
    except error.DisplayConnectionError as exc:
        LOG.error('Não foi possível conectar ao X11/XWayland: %s', exc)
        raise SystemExit(1)
