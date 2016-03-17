from gi.repository import Gtk, Gdk, GdkPixbuf

im = Gtk.Image()

PLAY_BTN_DEFAULT = [
    "12 13 3 1",
    "  c None",
    "X c black",
    "O c #808080",
    "  X         ",
    "  XX        ",
    "  XOX       ",
    "  XOOX      ",
    "  XOOOX     ",
    "  XOOOOX    ",
    "  XOOOOOX   ",
    "  XOOOOX    ",
    "  XOOOX     ",
    "  XOOX      ",
    "  XOX       ",
    "  XX        ",
    "  X         "
    ]

play_default_image = GdkPixbuf.Pixbuf.new_from_xpm_data(PLAY_BTN_DEFAULT)

PLAY_BTN_HOVER = [
    "12 13 3 1",
    "  c None",
    "X c black",
    "O c #FF8000",
    "  X         ",
    "  XX        ",
    "  XOX       ",
    "  XOOX      ",
    "  XOOOX     ",
    "  XOOOOX    ",
    "  XOOOOOX   ",
    "  XOOOOX    ",
    "  XOOOX     ",
    "  XOOX      ",
    "  XOX       ",
    "  XX        ",
    "  X         "
    ]

play_hover_image = GdkPixbuf.Pixbuf.new_from_xpm_data(PLAY_BTN_HOVER)

im.set_from_pixbuf(play_default_image)

def on_enter_notify(widget, event, data):
    print(event.type)
    if event.type == Gdk.EventType.ENTER_NOTIFY:
        data.set_from_pixbuf(play_hover_image)
    else:
        data.set_from_pixbuf(play_default_image)
    

win = Gtk.Window(Gtk.WindowType.TOPLEVEL)
win.set_title('Pixbuf xpm test')
win.set_size_request(200, 50)
win.connect('destroy', Gtk.main_quit)

hbox = Gtk.HBox()
win.add(hbox)
evtbox = Gtk.EventBox()
evtbox.add(im)
evtbox.set_events(evtbox.get_events() | Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
evtbox.connect('enter_notify_event', on_enter_notify, im)
evtbox.connect('leave_notify_event', on_enter_notify, im)
hbox.pack_start(evtbox, False, False, 10)

def main():
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()