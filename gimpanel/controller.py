import logging

import dbus
import dbus.service

log = logging.getLogger('GimPanelController')

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
