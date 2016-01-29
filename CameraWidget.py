import gi
import sys
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, Gst
from pushbullet import Pushbullet

class cameraWidget(Gtk.VBox):
    NOT_RECORD = "Don't Recoding."
    RECORDING = "Now Recording..."
    
    STOP_IMAGE = Gtk.STOCK_MEDIA_STOP
    RECORD_IMAGE = Gtk.STOCK_MEDIA_RECORD
    
    def __init__(self, name, source={'ip':'127.0.0.1', 'port':5000}, size=(640, 480)):
        Gtk.VBox.__init__(self)
        
        self._create_source(source)
        self._set_camera_name(name)
        self.set_size(size)
        self._setupUI()
        
    def _create_source(self, source):
        self._source = source
        
    def _set_camera_name(self, name):
        self._name = name
        
    def _setupUI(self):
        self._overlay = Gtk.Overlay()
        self.add(self._overlay)
        
        # Video screen renderer object initialize
        self._video_renderer = Gtk.DrawingArea()
        self._video_renderer.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        
        self._overlay.add(self._video_renderer)

        self._logo_box = Gtk.EventBox()
        self._logo_box.set_halign(Gtk.Align.CENTER)
        self._logo_box.set_valign(Gtk.Align.CENTER)
        
        tim = Gtk.Image()
        tim.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
        tim.set_halign(Gtk.Align.CENTER)
        tim.set_valign(Gtk.Align.CENTER)
        #tim.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        
        self._logo_box.connect('button-press-event', self._on_video_loading)
        self._logo_box.add(tim)
        self._overlay.add_overlay(self._logo_box)
        
        hbox = Gtk.HBox()
        self.pack_end(hbox, False, True, 2)
        
        #recording image setting
        self._rec_image = Gtk.Image()
        self._rec_image.set_from_stock(self.STOP_IMAGE, Gtk.IconSize.LARGE_TOOLBAR)
        hbox.pack_start(self._rec_image, False, False, 0)
        
        self._rec_text = Gtk.Label(self.NOT_RECORD)
        hbox.pack_start(self._rec_text, False, False, 0)
    
        self.show_all()
        
    def _on_video_loading(self, widget, event):
        print(widget)
        print(event)
        
        widget.hide()
        self._rec_image.set_from_stock(self.RECORD_IMAGE, Gtk.IconSize.LARGE_TOOLBAR)
        self._rec_text.set_text(self.RECORDING)
        
    def _createGstBin(self):
        self._bin = Gst.Bin.new(self._camera_name)
        
        self._cam_src = Gst.ElementFactory.make('tcpclientsrc', self._name.lower())
        self._cam_src.set_property('host', self._source["ip"])
        self._cam_src.set_property('port', self._source["port"])
        
        self._tee = Gst.ElementFactory.make('tee', self._name.lower() + "_tee")
        
        self._vid_sink = Gst.ElementFactory.make('autovideosink', self._name.lower() + "_videosink")
        
        bus = self._bin.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emmision()
        
        bus.connect('message', self._on_message_handler)
        bus.connect('sync-message::element', self._on_sync_message_handler)
    
    def _on_message_handler(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print("Error received from element %s: %s" % (msg.src.get_name(), err))
            print("Debugging information : %s" % debug)
            self.player.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.EOS:
            print("End-Of-Stream reached.")
            self.player.set_state(Gst.State.NULL)
        else:
            print("Not know message received.")
    
    def _on_sync_message_handler(self, bus, msg):
        if msg.get_structure().get_name() == "prepare-window-handle":
            videosink = msg.src
            videosink.set_property('force-aspect-ratio', True)
            videosink.set_window_handle(self._video_renderer.get_property('window').get_xid())
        
        
    def get_size(self):
        self._size
        
    def set_size(self, size):
        if not isinstance(size, tuple):
            print("Not compatible argument type.")
            sys.exit(-1)
            
        self._size = size
        self.set_size_request(size[0], size[1]+20)
        