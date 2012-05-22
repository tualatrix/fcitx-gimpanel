import os
import logging

from gi.repository import Gtk, Gdk, GObject

from ui import Handle
from debug import log_traceback, log_func
from common import CONFIG_ROOT

log = logging.getLogger('LangPanel')

class LangPanel(Gtk.Window):
    panel_x = GObject.Property(type=int, default=0)
    panel_y = GObject.Property(type=int, default=0)

    logo = GObject.Property(type=str, default='')
    im = GObject.Property(type=str, default='')
    vk = GObject.Property(type=str, default='')
    chttrans = GObject.Property(type=str, default='')
    punc = GObject.Property(type=str, default='')
    fullwidth = GObject.Property(type=str, default='')
    remind = GObject.Property(type=str, default='')

    fcitx_prop_dict = {
        '/Fcitx/logo': 'logo',
        '/Fcitx/im': 'im',
        '/Fcitx/vk': 'vk',
        '/Fcitx/chttrans': 'chttrans',
        '/Fcitx/punc': 'punc',
        '/Fcitx/fullwidth': 'fullwidth',
        '/Fcitx/remind': 'remind',
    }

    def __init__(self):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)

        self.set_border_width(2)

        self._toolbar = Gtk.Toolbar()
        self._toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        self._toolbar.set_show_arrow(False)
        self._toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)

        self._handle = Gtk.ToolItem()
        handle = Handle()
        handle.connect('move-end', self.on_handle_move_end)
        self._handle.add(handle)
        self._toolbar.insert(self._handle, -1)

        self._logo_button = Gtk.ToolButton()
        self._toolbar.insert(self._logo_button, -1)

        self._im_button = Gtk.ToolButton()
        self._toolbar.insert(self._im_button, -1)

        self._vk_button = Gtk.ToolButton()
        self._toolbar.insert(self._vk_button, -1)

        self._chttrans_button = Gtk.ToolButton()
        self._toolbar.insert(self._chttrans_button, -1)

        self._punc_button = Gtk.ToolButton()
        self._toolbar.insert(self._punc_button, -1)

        self._fullwidth_button = Gtk.ToolButton()
        self._toolbar.insert(self._fullwidth_button, -1)

        self._remind_button = Gtk.ToolButton()
        self._toolbar.insert(self._remind_button, -1)

        self._about_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        self._toolbar.insert(self._about_button, -1)

        self.add(self._toolbar)

        self.connect('realize', self.on_languagebar_realize)
        self.connect('destroy', self.on_languagebar_destroy)
        self.connect('size-allocate', self.on_languagebar_position)
        for signal_name in self.fcitx_prop_dict.values():
            self.connect('notify::%s' % signal_name, self.on_property_notify, '_%s_button' % signal_name)

    def on_property_notify(self, widget, prop, widget_name):
        label, icon_name, tooltip = self.get_property(prop.name).split(':')[1:]

        getattr(self, widget_name).set_label(label)
        getattr(self, widget_name).set_icon_name(icon_name)
        getattr(self, widget_name).set_tooltip_text(tooltip)

    def on_handle_move_end(self, widget):
        self.panel_x, self.panel_y = self.get_position()

    def on_languagebar_destroy(self, widget):
        try:
            f = open(os.path.join(CONFIG_ROOT, 'gimpanel-state'), 'w')
            f.write("%d %d" % (self.panel_x, self.panel_y))
            f.close()
        except Exception, e:
            log_traceback(log)

    def on_languagebar_realize(self, widget):
        try:
            size = open(os.path.join(CONFIG_ROOT, 'gimpanel-state')).read().strip()
            x, y = size.split()
            self.panel_x, self.panel_y = int(x), int(y)
            log.debug("Realize bar, the bar_x and bar_y: %dx%d" % (self.panel_x, self.panel_y))
        except Exception, e:
            log_traceback(log)

    def on_languagebar_position(self, widget, *args):
        window_right = self.panel_x + widget.get_allocation().width
        window_bottom = self.panel_y + widget.get_allocation().height

        log.debug("Bar window right and bottom: %dx%d" % (window_right, window_bottom))

        root_window = Gdk.get_default_root_window()
        screen_width, screen_height = root_window.get_width(), root_window.get_height()
        if window_right > screen_width:
            self.panel_x = screen_width - widget.get_allocation().width

        if window_bottom > screen_height:
            self.panel_y = screen_height - widget.get_allocation().height

        log.debug("Move bar to %sx%s" % (self.panel_x, self.panel_y))
        self.move(self.panel_x, self.panel_y)

GObject.type_register(LangPanel)
