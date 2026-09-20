from pathlib import Path
import xml.etree.ElementTree as ET
from Xlib import X

from clipboard import copy, get_after_copy
from constants import TARGET
from config import config, CONFIG_PATH
from rofi import rofi


def create_if_not_exists(directory):
    directory.mkdir(parents=True, exist_ok=True)
    return directory


data_dirs = {kind: create_if_not_exists(CONFIG_PATH / folder)
             for kind, folder in (('style', 'styles'), ('object', 'objects'))}
rofi_theme_params = ['-theme', config['rofi_theme']] if config.get('rofi_theme') else []


def saved_files(type_):
    return sorted(p for p in data_dirs[type_].glob('*.svg') if p.is_file() and not p.name.startswith('.'))


def choose_saved(type_, self):
    """Choose an exact filename in a visible menu, including shared prefixes."""
    files = saved_files(type_)
    names = [p.stem for p in files]
    prompt = 'Inserir objeto' if type_ == 'object' else 'Aplicar estilo'
    if not files:
        rofi(prompt + ' — nenhum salvo (Shift+A / Shift+S)', [], rofi_theme_params + ['-no-custom'])
        return
    status, index, name = rofi(prompt, names, rofi_theme_params + ['-no-custom'])
    if status != 0 or index < 0 or name not in names:
        return
    svg = files[names.index(name)].read_text(encoding='utf-8')
    root = ET.fromstring(svg)
    if root.tag.rsplit('}', 1)[-1] != 'svg':
        raise ValueError('O objeto salvo não contém SVG.')
    copy(svg, target=TARGET)
    self.press('v', X.ControlMask | (X.ShiftMask if type_ == 'style' else 0))


def valid_name(name):
    return bool(name.strip()) and name not in ('.', '..') and not any(
        c in name for c in ('/', '\\', '\0', '\n', '\r'))


def save_mode(type_, self):
    svg = get_after_copy(self, TARGET)
    root = ET.fromstring(svg)
    if root.tag.rsplit('}', 1)[-1] != 'svg':
        raise ValueError('A seleção não contém SVG.')
    names = [p.stem for p in saved_files(type_)]
    status, _, name = rofi('Salvar como', names, rofi_theme_params, fuzzy=False)
    if status != 0 or not valid_name(name):
        return
    path = data_dirs[type_] / f'{name}.svg'
    if path.is_symlink():
        raise ValueError('O destino é um link simbólico.')
    if path.exists():
        status, _, answer = rofi(f'Sobrescrever {name}?', ['n', 'y'], rofi_theme_params, fuzzy=False)
        if status != 0 or answer != 'y':
            return
    path.write_text(svg, encoding='utf-8')


def save_style_mode(self):
    save_mode('style', self)


def save_object_mode(self):
    save_mode('object', self)
