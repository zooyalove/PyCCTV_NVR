import gi
gi.require_version('Gst', '1.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import GstVideo

class VideoWidget(Gtk.DrawingArea):
    
    def __init__(self, parent):
        Gtk.DrawingArea.__init__(self)
        
        self._parent = parent
        self._sink = None
        self._xid = None
        
        self.modify_bg(Gtk.StateType.NORMAL, self.get_style().black)
        self.show()
        
    def do_expose_event(self, event):
        if self._sink is not None:
            self._sink.expose()
            return False
        else:
            return True
        
    def set_sink(self, sink):
        self._xid = self.get_property('window').get_xid()
        self._sink = sink
        self._sink.set_property('force-aspect-ratio', True)
        self._sink.set_window_handle(self._xid)
        