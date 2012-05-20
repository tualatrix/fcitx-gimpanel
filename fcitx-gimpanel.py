#!/usr/bin/python

import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import Gtk, Gdk, Gio, GObject
from gi.repository import AppIndicator3 as AppIndicator

GObject.threads_init()
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
dbus.mainloop.glib.threads_init()


class GimPanelController(dbus.service.Object):
    def __init__(self, session_bus):
        bus_name = dbus.service.BusName('org.kde.impanel', bus=session_bus)
        dbus.service.Object.__init__(self, bus_name, '/org/kde/impanel')

        self.PanelCreated()

    @dbus.service.signal('org.kde.impanel')
    def PanelCreated(self):
        pass


class GimPanel(Gtk.Window):
    def __init__(self, session_bus):
        Gtk.Window.__init__(self)

        self.set_default_size(100, 20)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)

        hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(hbox)

        self._preedit_label = Gtk.Label()
        self._preedit_label.set_alignment(0, 0.5)
        hbox.pack_start(self._preedit_label, False, False, 0)

        self._aux_label = Gtk.Label()
        self._aux_label.set_alignment(0, 0.5)
        hbox.pack_start(self._aux_label, False, False, 0)

        self._lookup_label = Gtk.Label()
        self._lookup_label.set_alignment(0, 0.5)
        hbox.pack_start(self._lookup_label, False, False, 0)

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

        self.connect('destroy', Gtk.main_quit)

    def setup_indicator(self):
        self.appindicator = AppIndicator.Indicator.new('gimpanel',
                                                       'ibus-keyboard',
                                                       AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self.appindicator.set_attention_icon('ibus-keyboard')
        self.appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()
        item = Gtk.MenuItem('Exit')
        item.connect('activate', Gtk.main_quit)

        menu.append(item)
        menu.show_all()

        self.appindicator.set_menu(menu)

    def signal_handler(self, *args, **kwargs):
        print "Caught signal: %s, %s\n" % (args, kwargs)

        if 'UpdatePreeditText' == kwargs['member']:
            self._preedit_label.set_text(args[0])
        elif 'UpdateAux' == kwargs['member']:
            self._aux_label.set_text(args[0])
        elif 'UpdateLookupTable' == kwargs['member']:
            text = []
            for i, index in enumerate(args[0]):
                text.append("%s%s" % (index, args[1][i]))

            self._lookup_label.set_text(''.join(text))
        elif 'ShowPreedit' == kwargs['member']:
            self._show_preedit = args[0]
            self._preedit_label.set_text('')
            self._preedit_label.set_visible(self._show_preedit)
            if not self._preedit_label:
                self._preedit_label.set_text('')
        elif 'ShowLookupTable' == kwargs['member']:
            self._show_lookup = args[0]
            self._lookup_label.set_visible(self._show_lookup)
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
    session_bus = dbus.SessionBus()

    gimpanel = GimPanel(session_bus)
    gimpanel.run()
