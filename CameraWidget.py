import gi
import sys
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk

class cameraWidget(Gtk.VBox):
    def __init__(self, name="Camera", size=(620, 480)):
        Gtk.VBox.__init__(self)
        
        self._camera_name = name
        self.setupUI()
        self.set_size(size)
        
        
    def setupUI(self):
        # Video screen renderer object initialize
        self._video_renderer = Gtk.DrawingArea()
        self._video_renderer.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        
        self.add(self._video_renderer)
        
        hbox = Gtk.HBox()
        self.pack_end(hbox, True, False, 0)
        label = Gtk.Label("Recording...")
        hbox.pack_start(label)
        
        self.show_all()
        
        
    def set_name(self, name):
        self._camera_name = name
        
    def get_name(self):
        return self._camera_name
    
    def get_size(self):
        self._size
        
    def set_size(self, size):
        if not isinstance(size, tuple):
            print("Not compatible argument type.")
            sys.exit(-1)
            
        self._size = size
        self.set_size_request(size[0], size[1]+20)
        