import os
import gettext

from gi.repository import GLib

CONFIG_ROOT = os.path.join(GLib.get_user_config_dir(), 'fcitx')

def init_locale():
    global INIT
    try:
        INIT
    except:
        gettext.install('fcitx-gimpanel', unicode=True)

        INIT = True

init_locale()
