import os
import logging

from gi.repository import Gtk, Gdk, GObject
from gimpanel.ui import Handle
from gimpanel.debug import log_traceback, log_func
from gimpanel.common import CONFIG_ROOT

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
    visible = GObject.Property(type=bool, default=False)
    visible_task_id = GObject.Property(type=int, default=0)

    fcitx_prop_dict = {
        '/Fcitx/logo': 'logo',
        '/Fcitx/im': 'im',
#        '/Fcitx/vk': 'vk',
        '/Fcitx/chttrans': 'chttrans',
        '/Fcitx/punc': 'punc',
        '/Fcitx/fullwidth': 'fullwidth',
        '/Fcitx/remind': 'remind',
    }

    prop_fcitx_dict = dict((v, k) for k, v in fcitx_prop_dict.iteritems())

    def __init__(self, controller):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)

        self.set_border_width(2)
        self.set_resizable(False)

        self._controller = controller

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
        self._im_button.connect('clicked', self.on_im_button_clicked)
        self._toolbar.insert(self._im_button, -1)

#        self._vk_button = Gtk.ToolButton()
#        self._toolbar.insert(self._vk_button, -1)

        self._chttrans_button = Gtk.ToolButton()
        self._toolbar.insert(self._chttrans_button, -1)

        self._punc_button = Gtk.ToolButton()
        self._toolbar.insert(self._punc_button, -1)

        self._fullwidth_button = Gtk.ToolButton()
        self._toolbar.insert(self._fullwidth_button, -1)

        self._remind_button = Gtk.ToolButton()
        self._toolbar.insert(self._remind_button, -1)

        self._about_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        self._about_button.connect('clicked', self.on_about_clicked)
        self._toolbar.insert(self._about_button, -1)

        self.add(self._toolbar)

        self.connect('realize', self.on_languagebar_realize)
        self.connect('destroy', self.on_languagebar_destroy)
        self.connect('size-allocate', self.on_languagebar_position)
        for signal_name in self.fcitx_prop_dict.values():
            self.connect('notify::%s' % signal_name, self.on_property_notify, '_%s_button' % signal_name)

        for button in self._toolbar.get_children()[1:-1]:
            button.connect('clicked', self.on_button_clicked)

    def do_visible_task(self):
        if self.visible_task_id == 0:
            self.visible_task_id = GObject.timeout_add(100, self._do_real_visible_task)

    def _do_real_visible_task(self):
        if self.visible != self.get_visible():
            self.set_visible(self.visible)
        self.visible_task_id = 0

    def on_im_button_clicked(self, widget):
        self.emit('popup_menu')

    def on_about_clicked(self, widget=None):
        #TODO
        dialog = Gtk.AboutDialog()
        dialog.set_property("program-name", 'Gim Panel for Fcitx')
        dialog.set_property("logo-icon-name", 'fcitx')
        dialog.run()
        dialog.destroy()

    def on_button_clicked(self, widget):
        if widget.fcitx_prop != '/Fcitx/im':
            self._controller.TriggerProperty(widget.fcitx_prop)
        else:
            log.error('Do Not TriggerProperty for /Fcitx/im')

    def reset_toolbar_items(self):
        for key in self.fcitx_prop_dict.values():
            setattr(self, key, '')

    def is_default_im(self):
        #TODO do not hard code
        try:
            value = self.get_property('im').split(':')[2]
            if value != 'fcitx-kbd':
                return True
            else:
                return False
        except Exception, e:
            log_traceback(log)
            return True

    def get_current_im(self):
        try:
            return self.get_property('im').split(':')[1]
        except Exception, e:
            log_traceback(log)
            return ''

    def get_current_im_icon_name(self):
        try:
            return self.get_property('im').split(':')[2]
        except Exception, e:
            log_traceback(log)
            return ''

    def on_property_notify(self, widget, prop, widget_name):
        if self.get_property(prop.name):
            label, icon_name, tooltip = self.get_property(prop.name).split(':')[1:]

            getattr(self, widget_name).fcitx_prop = self.prop_fcitx_dict[prop.name]
            getattr(self, widget_name).set_visible(True)
            getattr(self, widget_name).set_label(label)
            getattr(self, widget_name).set_icon_name(icon_name)
            getattr(self, widget_name).set_tooltip_text(tooltip)
        else:
            getattr(self, widget_name).set_visible(False)

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
        except Exception, e:
            log_traceback(log)

    def on_languagebar_position(self, widget, *args):
        window_right = self.panel_x + widget.get_allocation().width
        window_bottom = self.panel_y + widget.get_allocation().height


        root_window = Gdk.get_default_root_window()
        screen_width, screen_height = root_window.get_width(), root_window.get_height()
        if window_right > screen_width:
            self.panel_x = screen_width - widget.get_allocation().width

        if window_bottom > screen_height:
            self.panel_y = screen_height - widget.get_allocation().height

        self.move(self.panel_x, self.panel_y)

GObject.type_register(LangPanel)
