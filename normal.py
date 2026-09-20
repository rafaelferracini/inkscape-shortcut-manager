import time
from Xlib import X, XK

from clipboard import copy
from constants import TARGET
from config import config
from vim import open_vim
import text
import styles

STYLE_KEYS = set('sadghxebfw')


def event_to_string(self, event, char=None):
    mods = []
    for mask, name in ((X.ShiftMask, 'Shift'), (X.ControlMask, 'Control'),
                       (X.Mod1Mask, 'Alt'), (X.Mod4Mask, 'Super'), (X.Mod5Mask, 'AltGr')):
        if event.state & mask:
            mods.append(name)
    char = char or XK.keysym_to_string(self.disp.keycode_to_keysym(event.detail, 0))
    return ''.join(mod + '+' for mod in mods) + (char or '?')


def replay(self):
    for evt in self.events:
        self.forward(evt)


def normal_mode(self, event, char):
    # Modifier keys are never chord members. Forward them immediately.
    if not char:
        self.forward(event)
        return
    if event.type == X.KeyRelease and event.detail not in self.down:
        self.forward(event)
        return
    self.events.append(event)
    if event.type == X.KeyPress:
        self.down.add(event.detail)
        self.pressed.add(event_to_string(self, event, char))
        return
    if event.type != X.KeyRelease:
        return
    self.down.discard(event.detail)
    if self.down:
        return
    handled = False
    if len(self.pressed) > 1 and self.pressed <= STYLE_KEYS:
        paste_style(self, set(self.pressed))
        handled = True
    elif len(self.pressed) == 1:
        handled = handle_single_key(self, next(iter(self.pressed)))
    if not handled:
        replay(self)
    self.events.clear()
    self.pressed.clear()

def handle_single_key(self, ev):
    if ev in (config['style_leader'], XK.keysym_to_string(XK.string_to_keysym(config['style_leader']))):
        self.style_keys.clear()
        self.style_deadline = time.monotonic() + float(config['style_timeout'])
        self.mode = sequence_mode
    elif ev == 't':
        # Vim mode
        open_vim(self, compile_latex=False)
    elif ev == 'Shift+t':
        # Vim mode prerendered
        open_vim(self, compile_latex=True)
    elif ev == 'a':
        # Add objects mode
        styles.choose_saved('object', self)
    elif ev == 'Shift+a':
        # Save objects mode
        styles.save_object_mode(self)
    elif ev == 's':
        # Apply style mode
        styles.choose_saved('style', self)
    elif ev == 'Shift+s':
        # Save style mode
        styles.save_style_mode(self)
    elif ev == 'w':
        # Pencil
        self.press('p')
    elif ev == 'x':
        # Snap
        self.press('percent', X.ShiftMask)
    elif ev == 'f':
        # Bezier
        self.press('b')
    elif ev == 'z':
        # Undo
        self.press('z', X.ControlMask)
    elif ev == 'Shift+z':
        # Delete
        self.press('Delete')
    elif ev in ('`', config['toggle_key']):
        # Disabled mode
        self.press('t')
        self.mode = text.text_mode
    else:
        # Not handled
        return False
    return True

def finish_sequence(self, apply=True):
    combination = set(self.style_keys)
    self.style_keys.clear()
    self.style_deadline = None
    self.mode = normal_mode
    if apply and combination:
        paste_style(self, combination)


def expire_sequence(self):
    if self.style_deadline is not None and time.monotonic() >= self.style_deadline:
        finish_sequence(self)


def sequence_mode(self, event, char):
    # Process on release, with a fresh timeout for every sequential key.
    # While a key is held, do not apply a partially entered sequence.
    if event.type == X.KeyPress:
        self.style_deadline = None
        return
    if event.type != X.KeyRelease:
        return
    if char == 'Escape':
        finish_sequence(self, apply=False)
    elif char == 'Return':
        finish_sequence(self)
    elif char in STYLE_KEYS and not event.state & (X.ControlMask | X.Mod1Mask | X.Mod4Mask):
        self.style_keys.add(char)
        self.style_deadline = time.monotonic() + float(config['style_timeout'])
    elif char == 'BackSpace':
        self.style_keys.clear()
        self.style_deadline = time.monotonic() + float(config['style_timeout'])
    elif not char:
        self.style_deadline = time.monotonic() + float(config['style_timeout'])
    else:
        # An invalid sequence never changes the selection's style.
        finish_sequence(self, apply=False)


def paste_style(self, combination):
    """

    This creates the style depending on the combination of keys.

    """

    # Stolen from TikZ
    pt = 1.327 # pixels
    w = 0.4 * pt
    thick_width = 0.8 * pt
    very_thick_width = 1.2 * pt

    style = {
        'stroke-opacity': 1
    }

    if {'s', 'a', 'd', 'g', 'h', 'x', 'e'} & combination:
        style['stroke'] = 'black'
        style['stroke-width'] = w
        style['marker-end'] = 'none'
        style['marker-start'] = 'none'
        style['stroke-dasharray'] = 'none'
    else:
        style['stroke'] = 'none'

    if 'g' in combination:
        w = thick_width
        style['stroke-width'] = w

    if 'h' in combination:
        w = very_thick_width
        style['stroke-width'] = w

    if 'a' in combination:
        style['marker-end'] = f'url(#marker-arrow-{w})'

    if 'x' in combination:
        style['marker-start'] = f'url(#marker-arrow-{w})'
        style['marker-end'] = f'url(#marker-arrow-{w})'

    if 'd' in combination:
        style['stroke-dasharray'] = f'{w},{2*pt}'

    if 'e' in combination:
        style['stroke-dasharray'] = f'{3*pt},{3*pt}'

    if 'f' in combination:
        style['fill'] = 'black'
        style['fill-opacity'] = 0.12

    if 'b' in combination:
        style['fill'] = 'black'
        style['fill-opacity'] = 1

    if 'w' in combination:
        style['fill'] = 'white'
        style['fill-opacity'] = 1

    if {'f', 'b', 'w'} & combination:
        style['marker-end'] = 'none'
        style['marker-start'] = 'none'

    if not {'f', 'b', 'w'} & combination:
        style['fill'] = 'none'
        style['fill-opacity'] = 1

    if style['fill'] == 'none' and style['stroke'] == 'none':
        return

    # Start creation of the svg.
    # Later on, we'll write this svg to the clipboard, and send Ctrl+Shift+V to
    # Inkscape, to paste this style.

    svg = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
          <svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
          '''
    # If a marker is applied, add its definition to the clipboard
    # Arrow styles stolen from tikz
    if ('marker-end' in style and style['marker-end'] != 'none') or \
            ('marker-start' in style and style['marker-start'] != 'none'):
        svg += f'''
                <defs id="marker-defs">
                <marker
                id="marker-arrow-{w}"
                orient="auto-start-reverse"
                refY="0" refX="0"
                markerHeight="1.690" markerWidth="0.911">
                  <g transform="scale({(2.40 * w + 3.87)/(4.5*w)})">
                    <path
                       d="M -1.55415,2.0722 C -1.42464,1.29512 0,0.1295 0.38852,0 0,-0.1295 -1.42464,-1.29512 -1.55415,-2.0722"
                       style="fill:none;stroke:#000000;stroke-width:{0.6};stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:10;stroke-dasharray:none;stroke-opacity:1"
                       inkscape:connector-curvature="0" />
                   </g>
                </marker>
                </defs>
                '''

    style_string = ';'.join('{}: {}'.format(key, value)
                            for key, value in sorted(style.items(), key=lambda x: x[0])
                           )
    svg += f'<inkscape:clipboard style="{style_string}" /></svg>'

    copy(svg, target=TARGET)
    self.press('v', X.ControlMask | X.ShiftMask)
