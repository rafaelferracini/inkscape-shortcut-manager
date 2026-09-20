import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET
from Xlib import X
import normal
import text
import styles
import rofi
from vim import text_svg, render_latex
from main import SPECIAL_KEYS, is_inkscape
from Xlib import XK


def manager():
    return SimpleNamespace(events=[], pressed=set(), down=set(), prefix=[], style_keys=set(), style_deadline=None,
                           forward=Mock(), press=Mock(), mode=normal.normal_mode,
                           disp=SimpleNamespace(keycode_to_keysym=lambda code, group: code))


def key(m, char, kind, state=0):
    normal.normal_mode(m, SimpleNamespace(detail=ord(char), type=kind, state=state), char)


class ManagerTests(unittest.TestCase):
    def test_chord_waits_for_all_releases(self):
        m = manager()
        with patch('normal.paste_style') as paste:
            key(m, 'd', X.KeyPress); key(m, 'a', X.KeyPress)
            key(m, 'd', X.KeyRelease)
            paste.assert_not_called()
            key(m, 'a', X.KeyRelease)
            paste.assert_called_once_with(m, {'d', 'a'})
        self.assertFalse(m.events)

    def test_unknown_overlap_is_forwarded(self):
        m = manager()
        with patch('normal.paste_style') as paste:
            key(m, 'q', X.KeyPress); key(m, 's', X.KeyPress)
            key(m, 'q', X.KeyRelease); key(m, 's', X.KeyRelease)
            paste.assert_not_called()
        self.assertEqual(m.forward.call_count, 4)

    def test_windows_have_independent_chords(self):
        a, b = manager(), manager()
        key(a, 'd', X.KeyPress)
        key(b, 'w', X.KeyPress); key(b, 'w', X.KeyRelease)
        b.press.assert_called_once_with('p')
        self.assertEqual(a.pressed, {'d'})

    def test_ctrl_shortcut_replays(self):
        m = manager()
        key(m, 's', X.KeyPress, X.ControlMask)
        key(m, 's', X.KeyRelease, X.ControlMask)
        self.assertEqual(m.forward.call_count, 2)

    def test_style_xml_valid(self):
        for chord in ({'d', 'a'}, {'f', 's'}, {'x', 'h'}):
            with patch('normal.copy') as copy:
                normal.paste_style(manager(), chord)
                root = ET.fromstring(copy.call_args.args[0])
                self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')

    def test_text_is_escaped_and_multiline(self):
        root = ET.fromstring(text_svg('a < b & c\nsegunda linha'))
        self.assertEqual(''.join(root.itertext()), 'a < b & csegunda linha')
        self.assertEqual(len(list(root.iter('{http://www.w3.org/2000/svg}tspan'))), 2)

    def test_cancel_save_creates_nothing(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(styles.data_dirs, style=Path(d)), \
                patch('styles.get_after_copy', return_value='<svg/>'), \
                patch('styles.rofi', return_value=(-1, -1, '')):
            styles.save_mode('style', manager())
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_cancel_overwrite_preserves_file(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(styles.data_dirs, style=Path(d)), \
                patch('styles.get_after_copy', return_value='<svg/>'), \
                patch('styles.rofi', side_effect=[(0, 0, 'saved'), (-1, -1, '')]):
            path = Path(d) / 'saved.svg'; path.write_text('original')
            styles.save_mode('style', manager())
            self.assertEqual(path.read_text(), 'original')

    def test_save_uses_original_clipboard_snapshot(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(styles.data_dirs, style=Path(d)), \
                patch('styles.get_after_copy', return_value='<svg/>') as get, \
                patch('styles.rofi', return_value=(0, -1, 'novo')):
            styles.save_mode('style', manager())
            self.assertEqual((Path(d) / 'novo.svg').read_text(), '<svg/>')
            get.assert_called_once()

    def test_unsafe_names(self):
        for name in ('', '..', '../fora', '/tmp/foo', 'a/b', 'a\\b'):
            self.assertFalse(styles.valid_name(name))

    def test_leader_sequence_refreshes_timeout_and_applies(self):
        m = manager()
        with patch('normal.time.monotonic', return_value=10) as clock, patch('normal.paste_style') as paste:
            normal.handle_single_key(m, 'space')
            self.assertEqual(m.mode, normal.sequence_mode)
            clock.return_value = 10.8
            normal.sequence_mode(m, SimpleNamespace(type=X.KeyRelease, state=0), 'd')
            clock.return_value = 11.5
            normal.expire_sequence(m)
            paste.assert_not_called()
            normal.sequence_mode(m, SimpleNamespace(type=X.KeyRelease, state=0), 'a')
            clock.return_value = 12.51
            normal.expire_sequence(m)
            paste.assert_called_once_with(m, {'d', 'a'})
            self.assertEqual(m.mode, normal.normal_mode)

    def test_sequence_enter_escape_empty_and_invalid(self):
        for char, apply in [('Return', True), ('Escape', False), ('q', False)]:
            m = manager()
            normal.handle_single_key(m, 'space')
            normal.sequence_mode(m, SimpleNamespace(type=X.KeyRelease, state=0), 'd')
            with patch('normal.paste_style') as paste:
                normal.sequence_mode(m, SimpleNamespace(type=X.KeyRelease, state=0), char)
                self.assertEqual(paste.call_count, int(apply))
                self.assertIsNone(m.style_deadline)
        with patch('normal.paste_style') as paste:
            m = manager(); normal.handle_single_key(m, 'space')
            normal.finish_sequence(m)
            paste.assert_not_called()

    def test_saved_objects_shared_prefixes_and_underscore(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(styles.data_dirs, object=Path(d)):
            for name in ('eixo_xy', 'eixo_xyz'):
                (Path(d) / (name + '.svg')).write_text(f'<svg id="{name}"/>')
            (Path(d) / '.svg').write_text('<svg/>')
            for index, name in enumerate(('eixo_xy', 'eixo_xyz')):
                m = manager()
                with patch('styles.rofi', return_value=(0, index, name)) as menu, patch('styles.copy') as copy:
                    styles.choose_saved('object', m)
                    self.assertEqual(menu.call_args.args[1], ['eixo_xy', 'eixo_xyz'])
                    self.assertIn(name, copy.call_args.args[0])
                    m.press.assert_called_once_with('v', X.ControlMask)
            with patch('styles.rofi', return_value=(-1, -1, '')), patch('styles.copy') as copy:
                styles.choose_saved('object', manager())
                copy.assert_not_called()

    def test_rofi_failure_is_explicit(self):
        with patch('rofi.subprocess.run', return_value=SimpleNamespace(returncode=2, stdout='', stderr='bad')):
            with self.assertRaises(RuntimeError):
                rofi.rofi('save', [])

    def test_latex_error_is_reported(self):
        with tempfile.TemporaryDirectory() as d, patch('vim.subprocess.run', return_value=SimpleNamespace(returncode=1, stdout='bad formula')):
            with self.assertRaisesRegex(RuntimeError, 'bad formula'):
                render_latex('bad', d)

    def test_f12_toggle_only_switches_on_release(self):
        m = manager()
        self.assertTrue(normal.handle_single_key(m, 'F12'))
        self.assertEqual(m.mode, text.text_mode)
        text.text_mode(m, SimpleNamespace(type=X.KeyPress), 'F12')
        self.assertEqual(m.mode, text.text_mode)
        text.text_mode(m, SimpleNamespace(type=X.KeyRelease), 'F12')
        self.assertEqual(m.mode, normal.normal_mode)

    def test_launcher_uses_x11_and_dedicated_instance(self):
        import launch
        with tempfile.TemporaryDirectory() as d, patch.object(launch, 'CONFIG_PATH', Path(d)), \
                patch('launch.subprocess.Popen') as start, patch('launch.os.execvpe') as execute, \
                patch('launch.sys.argv', ['launch.py', '/tmp/figure with spaces.svg']):
            launch.main()
            start.assert_called_once()
            command, args, env = execute.call_args.args
            self.assertEqual(command, 'inkscape')
            self.assertEqual(args, ['inkscape', '--app-id-tag=shortcutmanager', '/tmp/figure with spaces.svg'])
            self.assertEqual(env['GDK_BACKEND'], 'x11')

    def test_wm_class_case_and_instance(self):
        self.assertTrue(is_inkscape(SimpleNamespace(get_wm_class=lambda: ('org.inkscape.Inkscape', 'Inkscape'))))
        self.assertFalse(is_inkscape(SimpleNamespace(get_wm_class=lambda: None)))


if __name__ == '__main__':
    unittest.main()
