from gi.repository import Gtk, Gdk, GObject


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
        context.set_background(self.get_parent_window())

        Gtk.render_handle(context,
                          cr,
                          0,
                          0,
                          self.get_allocation().width,
                          self.get_allocation().height)
        context.restore()

        return False
