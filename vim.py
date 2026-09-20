import tempfile
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from constants import TARGET
from clipboard import copy
from config import config
from Xlib import X

SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)


def text_svg(value):
    root = ET.Element(f'{{{SVG}}}svg')
    elem = ET.SubElement(root, f'{{{SVG}}}text', {
        'style': f"font-size:{config['font_size']}px;font-family:{config['font']};fill:#000000;stroke:none",
        '{http://www.w3.org/XML/1998/namespace}space': 'preserve',
    })
    for index, line in enumerate(value.splitlines()):
        span = ET.SubElement(elem, f'{{{SVG}}}tspan', {'x': '0', 'dy': '0' if index == 0 else '1.25em'})
        span.text = line
    return ET.tostring(root, encoding='unicode')


def render_latex(latex, directory):
    directory = Path(directory)
    source = directory / 'formula.tex'
    source.write_text(config['latex_document'](latex), encoding='utf-8')
    result = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                             '-no-shell-escape', source.name], cwd=directory,
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Falha ao compilar LaTeX:\n' + result.stdout[-4000:])
    subprocess.run(['pdf2svg', 'formula.pdf', 'formula.svg'], cwd=directory,
                   check=True, capture_output=True, timeout=30)
    return (directory / 'formula.svg').read_text()


def open_vim(self, compile_latex):
    with tempfile.TemporaryDirectory(prefix='inkscape-text-') as directory:
        filename = Path(directory) / 'input.tex'
        filename.write_text('$$', encoding='utf-8')
        result = config['open_editor'](str(filename))
        if isinstance(result, int) and result != 0:
            raise RuntimeError('O editor terminou com erro.')
        latex = filename.read_text(encoding='utf-8').strip()
        if not latex or latex == '$$':
            return
        svg = render_latex(latex, directory) if compile_latex else text_svg(latex)
        copy(svg, target=TARGET)
        self.press('v', X.ControlMask)
        self.press('Escape')
