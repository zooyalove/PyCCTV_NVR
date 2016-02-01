import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, Gtk, Gdk

class VideoWidget(Gtk.DrawingArea):
    
    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        
        self._sink = None
        self._xid = None
        
        self.modify_bg(Gtk.StateType.NORMAL, self.get_style().BLACK)
        
    def do_expose_event(self, event):
        if self._sink is not None:
            self._sink.expose()
            return False
        else:
            return True
        
    def set_sink(self, sink):
        self._sink = sink
        self._xid = self.get_property('window').get_xid()
        self._sink.set_window_handle(self._xid)
        