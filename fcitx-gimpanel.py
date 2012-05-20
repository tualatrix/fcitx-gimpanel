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
    def __init__(self, session_bus):
        bus_name = dbus.service.BusName('org.kde.impanel', bus=session_bus)
        dbus.service.Object.__init__(self, bus_name, '/org/kde/impanel')

        self.PanelCreated()

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

        self.set_border_width(5)

        self._toolbar = Gtk.Toolbar()
        self._toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        self._toolbar.set_show_arrow(False)
        self._toolbar.set_icon_size(Gtk.IconSize.MENU)

        self._handle = Gtk.ToolItem()
        handle = Handle()
        self._handle.add(handle)
        self._toolbar.insert(self._handle, -1)

        self._about_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        self._toolbar.insert(self._about_button, -1)

        self.add(self._toolbar)


class GimPanel(Gtk.Window):
    def __init__(self, session_bus):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.set_resizable(False)
        self.set_border_width(6)
        self.set_size_request(100, -1)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(hbox)

        hbox.pack_start(Handle(), False, False, 0)

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
        self._x = 0
        self._y = 0

        self._controller = GimPanelController(session_bus)

        session_bus.add_signal_receiver(self.signal_handler,
                                        dbus_interface='org.kde.kimpanel.inputmethod',
                                        member_keyword='member')
        self.setup_indicator()

        self._languagebar = LanguageBar()
        self._languagebar.connect('realize', self.on_realize)
        self._languagebar.show_all()

        self.connect('destroy', self.on_gimpanel_exit)

    def on_realize(self, widget):
        try:
            size = open(os.path.join(CONFIG_ROOT, 'gimpanel-state')).read().strip()
            width, height = size.split()
            log.debug("Set the window size to: %sx%s" % (width, height))
            self._languagebar.move(int(width), int(height))
        except Exception, e:
            log_traceback(log)


    @log_func(log)
    def on_gimpanel_exit(self, widget):
        try:
            x, y = self._languagebar.get_position()
            f = open(os.path.join(CONFIG_ROOT, 'gimpanel-state'), 'w')
            f.write("%d %d" % (x, y))
            f.close()
        except Exception, e:
            log_traceback(log)

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

    @log_func(log)
    def signal_handler(self, *args, **kwargs):
        if 'UpdatePreeditText' == kwargs['member']:
            self._preedit_label.set_markup('<span color="#c131b5">%s</span>' % (args[0]))
        elif 'UpdateAux' == kwargs['member']:
            self._aux_label.set_markup('<span color="blue">%s</span>' % (args[0]))
        elif 'UpdateLookupTable' == kwargs['member']:
            text = []
            highlight_first = (len(args[0]) > 1)
            for i, index in enumerate(args[0]):
                if i == 0 and highlight_first:
                    text.append("%s<span bgcolor='#f07746' fgcolor='white'>%s</span> " % (index, args[1][i].strip()))
                else:
                    text.append("%s%s" % (index, args[1][i]))

            self._lookup_label.set_markup(''.join(text))
        elif 'ShowPreedit' == kwargs['member']:
            self._show_preedit = args[0]
            self._preedit_label.set_visible(self._show_preedit)
            self._separator.set_visible(self._show_preedit)
            if not self._show_preedit:
                self._preedit_label.set_text('')
        elif 'ShowLookupTable' == kwargs['member']:
            self._show_lookup = args[0]
            if not self._show_lookup:
                self._lookup_label.set_text('')
        elif 'ShowAux' == kwargs['member']:
            self._show_aux = args[0]
            self._aux_label.set_visible(self._show_aux)
            if not self._show_aux:
                self._aux_label.set_text('')
        elif 'UpdateSpotLocation' == kwargs['member']:
            self._x = int(args[0])
            self._y = int(args[1])

        self.do_visible_and_move()

    def do_visible_and_move(self):
        if self._preedit_label.get_text() or \
           self._aux_label.get_text() or \
           self._lookup_label.get_text():
            self.set_visible(True)
            if self._x or self._y:
                self.move(self._x, self._y)
        else:
            self.set_visible(False)

    def run(self):
        self.show_all()
        Gtk.main()

if __name__ == '__main__':
    from debug import enable_debugging
    enable_debugging()

    session_bus = dbus.SessionBus()

    gimpanel = GimPanel(session_bus)
    gimpanel.run()
