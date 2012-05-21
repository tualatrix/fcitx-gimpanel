#!/usr/bin/python

import os
import logging

import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import Gtk, Gdk, Gio, GObject
from gi.repository import AppIndicator3 as AppIndicator

from debug import log_traceback, log_func
from common import CONFIG_ROOT

GObject.threads_init()
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
dbus.mainloop.glib.threads_init()

log = logging.getLogger('GimPanel')


class GimPanelController(dbus.service.Object):
    def __init__(self, session_bus, panel):
        self._panel = panel

        bus_name = dbus.service.BusName('org.kde.impanel', bus=session_bus)
        dbus.service.Object.__init__(self, bus_name, '/org/kde/impanel')
        session_bus.add_signal_receiver(self.signal_handler,
                                        dbus_interface='org.kde.kimpanel.inputmethod',
                                        member_keyword='member')

    def signal_handler(self, *args, **kwargs):
        signal_name = kwargs['member']

        if hasattr(self._panel, signal_name):
            getattr(self._panel, signal_name)(*args)
        else:
            log.warning("Un-handle signal_name: %s" % signal_name)
            for i, arg in enumerate(args):
                log.warning("\targs-%d: %s" % (i + 1, arg))
            for k, v in enumerate(kwargs):
                log.warning("\tdict args-%d: %s: %s" % (k, v, kwargs[v]))

        self._panel.do_visible_task()

    @dbus.service.signal('org.kde.impanel')
    def PanelCreated(self):
        pass


class Handle(Gtk.EventBox):
    __gsignals__ = {
        "move-begin": (GObject.SignalFlags.RUN_LAST, None, ()),
        "move-end": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__ (self):
        super(Handle, self).__init__()

        self.set_visible_window(False)
        self.set_size_request(10, -1)
        self.set_events(Gdk.EventMask.EXPOSURE_MASK | \
                        Gdk.EventMask.BUTTON_PRESS_MASK | \
                        Gdk.EventMask.BUTTON_RELEASE_MASK | \
                        Gdk.EventMask.BUTTON1_MOTION_MASK)

        self._move_begined = False

    def do_button_press_event(self, event):
        if event.button == 1:
            self._move_begined = True
            toplevel = self.get_toplevel()
            x, y = toplevel.get_position()
            self._press_pos = event.x_root - x, event.y_root - y
            self.get_parent_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.FLEUR))
            self.emit("move-begin")
            return True
        return False

    def do_button_release_event(self, event):
        if event.button == 1:
            self._move_begined = False
            self.get_parent_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))
            self.emit("move-end")
            return True

        return False

    def do_motion_notify_event(self, event):
        if not self._move_begined:
            return
        toplevel = self.get_toplevel()
        x, y = toplevel.get_position()
        x  = int(event.x_root - self._press_pos[0])
        y  = int(event.y_root - self._press_pos[1])

        toplevel.move(x, y)

    def do_draw(self, cr):
        context = self.get_style_context()
        context.save()
        context.add_class(Gtk.STYLE_CLASS_SEPARATOR)

        Gtk.render_handle(context,
                          cr,
                          0,
                          0,
                          self.get_allocation().width,
                          self.get_allocation().height)
        context.restore()

        return False


class LanguageBar(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self, type=Gtk.WindowType.POPUP)

        self._bar_x = 0
        self._bar_y = 0

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

        self._fullwidth_button = Gtk.ToolButton()
        self._toolbar.insert(self._fullwidth_button, -1)

        self._about_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        self._toolbar.insert(self._about_button, -1)

        self.add(self._toolbar)

        self.connect('destroy', self.on_languagebar_destroy)
        self.connect('realize', self.on_languagebar_realize)
        self.connect('size-allocate', self.on_languagebar_position)

    def on_handle_move_end(self, widget):
        self._bar_x, self._bar_y = self.get_position()

    @log_func(log)
    def on_languagebar_destroy(self, widget):
        try:
            f = open(os.path.join(CONFIG_ROOT, 'gimpanel-state'), 'w')
            f.write("%d %d" % (self._bar_x, self._bar_y))
            f.close()
        except Exception, e:
            log_traceback(log)

    @log_func(log)
    def on_languagebar_realize(self, widget):
        try:
            size = open(os.path.join(CONFIG_ROOT, 'gimpanel-state')).read().strip()
            x, y = size.split()
            self._bar_x, self._bar_y = int(x), int(y)
            log.debug("Realize bar, the bar_x and bar_y: %dx%d" % (self._bar_x, self._bar_y))
        except Exception, e:
            log_traceback(log)

    def on_languagebar_position(self, widget, *args):
        window_right = self._bar_x + widget.get_allocation().width
        window_bottom = self._bar_y + widget.get_allocation().height

        log.debug("Bar window right and bottom: %dx%d" % (window_right, window_bottom))

        root_window = Gdk.get_default_root_window()
        screen_width, screen_height = root_window.get_width(), root_window.get_height()
        if window_right > screen_width:
            self._bar_x = screen_width - widget.get_allocation().width

        if window_bottom > screen_height:
            self._bar_y = screen_height - widget.get_allocation().height

        log.debug("Move bar to %sx%s" % (self._bar_x, self._bar_y))
        self.move(self._bar_x, self._bar_y)


class GimPanel(Gtk.Window):
    def __init__(self, session_bus):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.set_resizable(False)
        self.set_border_width(6)
        self.set_size_request(100, -1)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(hbox)

        handle = Handle()
        hbox.pack_start(handle, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                       spacing=3)
        hbox.pack_start(vbox, True, True, 6)

        self._preedit_label = Gtk.Label()
        self._preedit_label.set_alignment(0, 0.5)
        vbox.pack_start(self._preedit_label, True, True, 0)

        self._separator = Gtk.Separator()
        vbox.pack_start(self._separator, False, False, 0)

        self._aux_label = Gtk.Label()
        self._aux_label.set_alignment(0, 0.5)
        vbox.pack_start(self._aux_label, True, True, 0)

        self._lookup_label = Gtk.Label()
        self._lookup_label.set_alignment(0, 0.5)
        vbox.pack_start(self._lookup_label, True, True, 0)

        self._show_preedit = False
        self._show_lookup = False
        self._show_aux = False

        self._cursor_x = 0
        self._cursor_y = 0

        self._controller = GimPanelController(session_bus, self)

        self.setup_indicator()

        self._languagebar = LanguageBar()
        self._languagebar.show_all()

        self.connect('destroy', self.on_gimpanel_exit)
        self.connect("size-allocate", lambda w, a: self._move_position())
        self.connect('realize', self.on_realize)

    def on_realize(self, widget):
        self._controller.PanelCreated()

    @log_func(log)
    def on_gimpanel_exit(self, widget):
        self._languagebar.destroy()
        Gtk.main_quit()

    def setup_indicator(self):
        self.appindicator = AppIndicator.Indicator.new('gimpanel',
                                                       'ibus-keyboard',
                                                       AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self.appindicator.set_attention_icon('ibus-keyboard')
        self.appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()
        item = Gtk.MenuItem('Exit')
        item.connect('activate', self.on_gimpanel_exit)

        menu.append(item)
        menu.show_all()

        self.appindicator.set_menu(menu)

    def UpdatePreeditText(self, text, attr):
        self._preedit_label.set_markup('<span color="#c131b5">%s</span>' % text)

    def UpdateAux(self, text, attr):
        self._aux_label.set_markup('<span color="blue">%s</span>' % text)

    def UpdateLookupTable(self, *args):
        text = []
        highlight_first = (len(args[0]) > 1)
        for i, index in enumerate(args[0]):
            if i == 0 and highlight_first:
                text.append("%s<span bgcolor='#f07746' fgcolor='white'>%s</span> " % (index, args[1][i].strip()))
            else:
                text.append("%s%s" % (index, args[1][i]))

        self._lookup_label.set_markup(''.join(text))

    def ShowPreedit(self, to_show):
        self._show_preedit = to_show
        self._preedit_label.set_visible(self._show_preedit)
        self._separator.set_visible(self._show_preedit)
        if not self._show_preedit:
            self._preedit_label.set_text('')

    def ShowLookupTable(self, to_show):
        self._show_lookup = to_show
        if not self._show_lookup:
            self._lookup_label.set_text('')

    def ShowAux(self, to_show):
        self._show_aux = to_show
        self._aux_label.set_visible(self._show_aux)
        if not self._show_aux:
            self._aux_label.set_text('')

    def UpdateSpotLocation(self, x, y):
        self._cursor_x, self._cursor_y = x, y

    def RegisterProperties(self, args):
        for arg in args:
            log.debug("RegisterProperties: %s" % arg)
            if arg.split(':')[0] == '/Fcitx/logo':
                self._languagebar._logo_button.set_icon_name(arg.split(':')[2])
            elif arg.split(':')[0] == '/Fcitx/im':
                self._languagebar._im_button.set_icon_name(arg.split(':')[2])
            elif arg.split(':')[0] == '/Fcitx/vk':
                self._languagebar._vk_button.set_icon_name(arg.split(':')[2])
            elif arg.split(':')[0] == '/Fcitx/fullwidth':
                self._languagebar._fullwidth_button.set_icon_name(arg.split(':')[2])

    def UpdateProperty(self, value):
        log.debug("UpdateProperty: %s" % value)
        if value.split(':')[0] == '/Fcitx/logo':
            self._languagebar._logo_button.set_icon_name(value.split(':')[2])
        elif value.split(':')[0] == '/Fcitx/im':
            self._languagebar._im_button.set_icon_name(value.split(':')[2])
        elif value.split(':')[0] == '/Fcitx/vk':
            self._languagebar._vk_button.set_icon_name(value.split(':')[2])
        elif value.split(':')[0] == '/Fcitx/fullwidth':
            self._languagebar._fullwidth_button.set_icon_name(value.split(':')[2])

    def Enable(self, enabled):
        log.debug("Enable: %s" % enabled)
        self._languagebar.set_visible(enabled)

    def do_visible_task(self):
        if self._preedit_label.get_text() or \
           self._aux_label.get_text() or \
           self._lookup_label.get_text():
            self.set_visible(True)
        else:
            self.set_visible(False)

    def _move_position(self):
        window_right = self._cursor_x + self.get_allocation().width
        window_bottom = self._cursor_y + self.get_allocation().height

        root_window = Gdk.get_default_root_window()
        screen_width, screen_height = root_window.get_width(), root_window.get_height()
        if window_right > screen_width:
            x = screen_width - self.get_allocation().width
        else:
            x = self._cursor_x

        if window_bottom > screen_height:
            # TODO 20 should be the cursor size and do not be hard-coded
            y = self._cursor_y - self.get_allocation().height - 20
        else:
            y = self._cursor_y

        log.debug("Move gimpanel to %sx%s" % (x, y))
        self.move(x, y)

    def run(self):
        self.show_all()
        self.do_visible_task()
        Gtk.main()

if __name__ == '__main__':
    from debug import enable_debugging
    enable_debugging()

    session_bus = dbus.SessionBus()

    gimpanel = GimPanel(session_bus)
    gimpanel.run()
