#!/usr/bin/python

import os
import logging

from gi.repository import Gtk, Gdk, Gio, GObject
from gi.repository import AppIndicator3 as AppIndicator

from gimpanel.debug import log_traceback, log_func
from gimpanel.ui import Handle
from gimpanel.common import CONFIG_ROOT
from gimpanel.controller import GimPanelController
from gimpanel.langpanel import LangPanel

log = logging.getLogger('GimPanel')

class GimPanel(Gtk.Window):
    preedit_box_height = GObject.Property(type=int, default=0)

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

        self._preedit_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                               spacing=6)
        vbox.pack_start(self._preedit_hbox, True, True, 0)

        self._preedit_label = Gtk.Label()
        self._preedit_label.set_alignment(0, 0.5)
        self._preedit_hbox.pack_start(self._preedit_label, True, True, 0)
        self._preedit_hbox.connect('size-allocate', self._on_lookup_size_request)

        self._lookup_separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self._preedit_hbox.pack_start(self._lookup_separator, False, False, 0)

        self.look_forward_button = self._create_arrow_button(Gtk.STOCK_GO_FORWARD)
        self.look_forward_button.connect('clicked', self.on_lookup_forward)
        self._preedit_hbox.pack_end(self.look_forward_button, False, False, 0)

        self.look_back_button = self._create_arrow_button(Gtk.STOCK_GO_BACK)
        self.look_back_button.connect('clicked', self.on_lookup_back)
        self._preedit_hbox.pack_end(self.look_back_button, False, False, 0)

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
        self._cursor_h = 0
        self._showing_popup = False

        self._controller = GimPanelController(session_bus, self)

        self.setup_indicator()

        self.langpanel = LangPanel(self._controller)
        self.langpanel.show_all()
        self.langpanel.hide()
        self.langpanel.connect('popup_menu', self.show_popup_menu)

        self.connect('destroy', self.on_gimpanel_exit)
        self.connect("size-allocate", lambda w, a: self._move_position())
        self.connect('realize', self.on_realize)

    def _on_lookup_size_request(self, widget, allocation):
        if self.preedit_box_height < allocation.height:
            #TODO hard code 3 pixel
            self.preedit_box_height = allocation.height - 3
        self._preedit_hbox.set_size_request(-1, self.preedit_box_height)

    def on_lookup_back(self, widget):
        self.set_resizable(True)
        self._controller.LookupTablePageUp()

    def on_lookup_forward(self, widget):
        self.set_resizable(True)
        self._controller.LookupTablePageDown()

    def _create_arrow_button(self, stock_id):
        button = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
        image = Gtk.Image.new_from_stock(stock_id=stock_id,
                                         size=Gtk.IconSize.MENU)
        button.add(image)
        button.show_all()

        return button

    def on_realize(self, widget):
        self._controller.PanelCreated()
        self._controller.PanelCreated2()
        self._controller.TriggerProperty('/Fcitx/im')
        self.do_visible_task()

    @log_func(log)
    def on_gimpanel_exit(self, widget):
        self.langpanel.destroy()
        Gtk.main_quit()

    def setup_indicator(self):
        self.appindicator = AppIndicator.Indicator.new('gimpanel',
                                                       'fcitx-kbd',
                                                       AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self.appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        menu = Gtk.Menu()
        menu.connect('hide', self.on_indicator_menu_hide)

        item = Gtk.MenuItem(_('Quit'))
        item.connect('activate', self.on_gimpanel_exit)
        menu.append(item)

        menu.show_all()

        self.appindicator.set_menu(menu)

    @log_func(log)
    def on_trigger_menu(self, widget):
        GObject.timeout_add(50, self._real_traiiger_menu, widget)

    @log_func(log)
    def on_indicator_menu_hide(self, widget):
        self._showing_popup = False
        for item in widget.get_children()[-2:]:
            item.show()

    def _real_traiiger_menu(self, widget):
        self._controller.TriggerProperty(widget._im)

    @log_func(log)
    def show_popup_menu(self, widget):
        self._showing_popup = True
        menu = self.appindicator.get_menu()

        for item in menu.get_children()[-2:]:
            item.hide()

        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    @log_func(log)
    def update_menu(self, args=None):
        menu = self.appindicator.get_menu()

        if args:
            for item in menu.get_children()[:-1]:
                item.destroy()

            if args[0]:
                menu.insert(Gtk.SeparatorMenuItem(), 0)

            group_item = None
            for i, arg in enumerate(args):
                log.debug("menu item: %s" % arg)
                item_name = arg.split(':')[1]
                item = Gtk.RadioMenuItem(item_name)
                item._im = arg.split(':')[0]
                if group_item:
                    item.set_property('group', group_item)
                if i == 0:
                    group_item = item
                if self.langpanel.get_current_im() == item_name:
                    item.set_active(True)

                item.connect('activate', self.on_trigger_menu)
                menu.insert(item, i)
        else:
            for item in menu.get_children()[:-2]:
                item.handler_block_by_func(self.on_trigger_menu)
                item.set_active(item.get_label() == self.langpanel.get_current_im())
                item.handler_unblock_by_func(self.on_trigger_menu)

        menu.show_all()

    @log_func(log)
    def ExecMenu(self, *args):
        if not self._showing_popup:
            self.update_menu(args[0])

    def UpdatePreeditText(self, text, attr):
        if self._preedit_label.get_text() != text:
            self.set_resizable(False)
            self._preedit_label.set_markup('<span color="#c131b5">%s</span>' % text)

    def UpdateAux(self, text, attr):
        self._aux_label.set_markup('<span color="blue">%s</span>' % text)

    def UpdateLookupTable(self, label, text,
                          attr, can_back, can_forward):
        markup_text = []
        highlight_first = (len(label) > 1)
        self.set_resizable(True)

        for i, index in enumerate(label):
            if i == 0 and highlight_first:
                markup_text.append("%s<span bgcolor='#f07746' fgcolor='white'>%s</span> " % (index, text[i].strip()))
            else:
                markup_text.append("%s%s" % (index, text[i]))

        self._lookup_label.set_markup(''.join(markup_text))

        if can_back or can_forward:
            #FIXME if set_sensitive to button, then the relief will be fixed. GTK+ bug?
            self.look_back_button.get_child().set_sensitive(can_back)
            self.look_forward_button.get_child().set_sensitive(can_forward)
            self.look_back_button.show()
            self.look_forward_button.show()
            self._lookup_separator.show()
        else:
            self.look_back_button.hide()
            self.look_forward_button.hide()
            self._lookup_separator.hide()

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

    @log_func(log)
    def RegisterProperties(self, args):
        self.langpanel.reset_toolbar_items()

        for arg in args:
            prop_name = arg.split(':')[0]

            if prop_name in self.langpanel.fcitx_prop_dict.keys():
                setattr(self.langpanel, self.langpanel.fcitx_prop_dict[prop_name], arg)
            else:
                log.warning('RegisterProperties: No handle prop name: %s' % prop_name)

    def UpdateProperty(self, value):
        prop_name = value.split(':')[0]
        icon_name = value.split(':')[2]

        if prop_name in self.langpanel.fcitx_prop_dict.keys():
            if self.langpanel.is_default_im():
                self.appindicator.set_property("attention-icon-name", icon_name)
                self.appindicator.set_status(AppIndicator.IndicatorStatus.ATTENTION)
            else:
                self.appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
            setattr(self.langpanel, self.langpanel.fcitx_prop_dict[prop_name], value)
        else:
            log.warning('UpdateProperty: No handle prop name: %s' % prop_name)

    @log_func(log)
    def Enable(self, enabled):
        if not self._showing_popup:
            self.update_menu()
        self.langpanel.visible = enabled or self._showing_popup
        self.langpanel.do_visible_task()

    def do_visible_task(self):
        if self._preedit_label.get_text() or \
           self._aux_label.get_text() or \
           self._lookup_label.get_text():
            self.set_visible(True)
        else:
            self.set_visible(False)

    def _move_position(self):
        window_right = self._cursor_x + self.get_allocation().width
        window_bottom = self._cursor_y + self._cursor_h + self.get_allocation().height

        root_window = Gdk.get_default_root_window()
        screen_width, screen_height = root_window.get_width(), root_window.get_height()
        if window_right > screen_width:
            x = screen_width - self.get_allocation().width
        else:
            x = self._cursor_x

        if window_bottom > screen_height:
            y = self._cursor_y - self.get_allocation().height
        else:
            y = self._cursor_y + self._cursor_h

        log.debug("Move gimpanel to %sx%s" % (x, y))
        self.move(x, y)
