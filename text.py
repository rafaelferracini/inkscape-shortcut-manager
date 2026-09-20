from Xlib import X
import normal
from config import config


def text_mode(self, event, char):
    """Pass keys through until the toggle key is released."""
    if char in ('`', config['toggle_key']):
        if event.type == X.KeyRelease:
            self.press('Escape')
            self.mode = normal.normal_mode
        return
    self.forward(event)
