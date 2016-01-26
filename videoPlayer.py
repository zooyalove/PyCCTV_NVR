import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, Gtk, Gdk
from gi.repository import GdkX11, GstVideo

class VideoPlayer(Gtk.Window):
    def __init__(self, parent):
        Gtk.Window.__init__(self)
        
        self.par = parent
        self.set_size_request(640, 480)
        self.set_transient_for(parent)
        self.set_destroy_with_parent(True)
        self.set_modal(True)
        
        vbox = Gtk.VBox()
        btn = Gtk.Button("App Window")
        vbox.add(btn)
        self.add(vbox)
        self.show_all()