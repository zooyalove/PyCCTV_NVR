import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, Gtk, Gdk
from gi.repository import GdkX11, GstVideo

class VideoPlayer(Gtk.Window):
    def __init__(self, app):
        super(VideoPlayer, self).__init__(parent=app)
        
        self.app = app
        self.set_size_request(640, 480)
        self.set_transient_for(app)
        self.set_destroy_with_parent(True)
        self.set_modal(True)
        
        vbox = Gtk.VBox()
        self.add(vbox)
        
        self.video_frame = Gtk.DrawingArea()
        self.video_frame.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        vbox.add(self.video_frame)
        
        self.show_all()