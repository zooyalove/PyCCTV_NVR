import gi
import sys
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, Gst
from pushbullet import Pushbullet
from videowidget import VideoWidget

class CameraWidget(Gtk.VBox):
    NOT_RECORD = "Don't Recoding."
    RECORDING = "Now Recording..."
    DEVICE_CONNECTING = "Camera connecting..."
    DEVICE_CONNECT_ERROR = "Error camera connect"
    
    STOP_IMAGE = Gtk.STOCK_MEDIA_STOP
    RECORD_IMAGE = Gtk.STOCK_MEDIA_RECORD
    
    def __init__(self, name, source={'ip':'127.0.0.1', 'port':5000}, size=(648, 365)):
        Gtk.VBox.__init__(self)
        
        self._set_source(source)
        self._set_camera_name(name)
        self.set_size(size)
        self._setupUI()
        
    def _set_source(self, source):
        self._source = source
        
    def _set_camera_name(self, name):
        self._name = name
        
    def get_camera_name(self):
        return self._name
        
    def _setupUI(self):
        self.is_playing = False
        self._overlay = Gtk.Overlay()
        self.add(self._overlay)
        
        # Video screen renderer object initialize
        self._video_renderer = VideoWidget()
        
        self._overlay.add(self._video_renderer)

        self._logo_box = Gtk.EventBox()
        self._logo_box.set_halign(Gtk.Align.CENTER)
        self._logo_box.set_valign(Gtk.Align.CENTER)
        
        tim = Gtk.Image()
        tim.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
        
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
        
    def _createSourceBin(self):
        c_name = self._name.lower() 
        source_bin = Gst.Bin.new(c_name + "_src_bin")
        
        cam_src = Gst.ElementFactory.make('tcpclientsrc', c_name + "_src")
        cam_src.set_property('host', self._source["ip"])
        cam_src.set_property('port', self._source["port"])
        source_bin.add(cam_src)
        
        gdpdepay = Gst.ElementFactory.make('gdpdepay', None)
        source_bin.add(gdpdepay)
        
        rtpdepay = Gst.ElementFactory.make('rtph264depay', None)
        source_bin.add(rtpdepay)
        
        avdec = Gst.ElementFactory.make('avdec_h264', None)
        source_bin.add(avdec)
        
        cam_src.link(gdpdepay)
        gdpdepay.link(rtpdepay)
        rtpdepay.link(avdec)
        
        dec_pad = avdec.get_static_pad('src')
        gh_pad = Gst.GhostPad.new('src', dec_pad)
        dec_pad.link(gh_pad)
        source_bin.add_pad(gh_pad)
        
        return source_bin
        
        
    def _createVideoSinkBin(self):
        #self._tee = Gst.ElementFactory.make('tee', self._name.lower() + "_tee")
        c_name = self._name.lower()
        
        sink_bin = Gst.Bin.new(c_name + "_vidsink_bin")
        
        queue = Gst.ElementFactory.make('queue', None)
        sink_bin.add(queue)
        
        conv1 = Gst.ElementFactory.make('videoconvert', None)
        sink_bin.add(conv1)
        
        crop = Gst.ElementFactory.make('videocrop', c_name + "_crop")
        sink_bin.add(crop)
        
        scale = Gst.ElementFactory.make('videoscale', None)
        sink_bin.add(scale)
        
        caps = Gst.caps_from_string("video/x-raw, width=648, height=365")
        capsfilter = Gst.ElementFactory.make('capsfilter', None)
        capsfilter.set_property('caps', caps)
        sink_bin.add(capsfilter)
        
        conv2 = Gst.ElementFactory.make('videoconvert', None)
        sink_bin.add(conv2)
        
        self._vid_sink = Gst.ElementFactory.make('autovideosink', c_name + "_videosink")
        self._vid_sink.set_property('sync', False)
        sink_bin.add(self._vid_sink)
        
        queue.link(conv1)
        conv1.link(crop)
        crop.link(scale)
        scale.link(capsfilter)
        capsfilter.link(conv2)
        conv2.link(self._vid_sink)
        
        q_pad = queue.get_static_pad('sink')
        gh_pad = Gst.GhostPad.new('sink', q_pad)
        gh_pad.link(q_pad)
        sink_bin.add_pad(gh_pad)
        
        return sink_bin
    
    
    def aa(self):
        bus = self._bin.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emmision()
        
        bus.connect('message', self._on_message_handler)
        bus.connect('sync-message::element', self._on_sync_message_handler)
    
    def _on_video_loading(self, widget, event):
        widget.hide()
        self._rec_image.set_from_stock(self.RECORD_IMAGE, Gtk.IconSize.LARGE_TOOLBAR)
        self._rec_text.set_text(self.RECORDING)
        
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
        