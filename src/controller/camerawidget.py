import platform
import gi
import sys
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, Gst, Pango
from pushbullet import Pushbullet
from src.controller.videowidget import VideoWidget

class CameraWidget(Gtk.VBox):
    IS_LINUX = (platform.system().lower() == "linux")
    NOT_RECORD = "Don't Recoding."
    RECORDING = "Now Recording..."
    DEVICE_CONNECTING = "Camera connecting..."
    DEVICE_CONNECT_ERROR = "Error camera connect"
    
    STOP_IMAGE = Gtk.STOCK_MEDIA_STOP
    RECORD_IMAGE = Gtk.STOCK_MEDIA_RECORD
    
    def __init__(self, name, source={'ip':'127.0.0.1', 'port':5000}, size=(640, 360), save_timeout=60):
        super(CameraWidget, self).__init__()
        
        self.is_playing = False
        
        self.__set_source(source)
        self.__set_camera_name(name)
        self.set_size(size)
        self.set_save_timeout(save_timeout)
        self._setupUI()
        if source is not None:
            self.__createCameraBin()
        
    def _setupUI(self):
        
        self._overlay = Gtk.Overlay()
        self.pack_start(self._overlay, True, True, 0)
        
        # Video screen renderer object initialize
        self.video_widget = VideoWidget(self)
        self.video_widget.set_size_request(self._size[0], self._size[1])
        
        self._overlay.add(self.video_widget)

        if self.__source is None:
            tim = Gtk.Image()
            tim.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
            tim.set_halign(Gtk.Align.CENTER)
            tim.set_valign(Gtk.Align.CENTER)
            self._overlay.add_overlay(tim)
        
        #bottom part config
        #Device name setting
        cam_name = Gtk.Label(self.get_camera_name())
        cam_name.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('white'))
        cam_name.modify_font(Pango.FontDescription('sans 16'))
        cam_name.set_halign(Gtk.Align.CENTER)
        cam_name.set_valign(Gtk.Align.END)
        cam_name.set_margin_bottom(10)
        print(cam_name.get_text())
        
        self._overlay.add_overlay(cam_name)
        
        #record info
        #recording image setting
        hbox = Gtk.HBox()
        hbox.set_halign(Gtk.Align.END)
        hbox.set_valign(Gtk.Align.END)
        hbox.set_margin_bottom(10)
        
        self._rec_image = Gtk.Image()
        self._rec_image.set_from_stock(self.STOP_IMAGE, Gtk.IconSize.LARGE_TOOLBAR)
        self._rec_image.set_margin_right(5)
        hbox.pack_start(self._rec_image, False, False, 0)
        
        self._rec_text = Gtk.Label(self.NOT_RECORD)
        self._rec_text.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('white'))
        self._rec_text.set_margin_right(10)
        hbox.pack_start(self._rec_text, False, False, 0)

        self._overlay.add_overlay(hbox)
            
        self.show_all()
    
    
    def __createCameraBin(self):
        c_name = self.get_camera_name().lower()
        self.__camera_bin = Gst.ElementFactory.make('bin', c_name + "_bin")
        src = self.__createSourceBin()
        self.__camera_bin.add(src)
        
        tee = Gst.ElementFactory.make('tee', c_name + "_tee")
        self.__camera_bin.add(tee)
        
        vidsink = self.__createVideoSinkBin()
        self.__camera_bin.add(vidsink)
        
        src.link(tee)
        
        src_pad = tee.get_request_pad("src_%u")
        src_pad.link(vidsink.get_static_pad('sink'))
        
        ret = self.__camera_bin.set_state(Gst.State.READY)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("State of " + c_name.upper() + " change Failured.")
            self.__camera_bin.set_state(Gst.State.NULL)
        
        
    def __createSourceBin(self):
        c_name = self.get_camera_name().lower() 
        source_bin = Gst.ElementFactory.make('bin', c_name + "_src_bin")
        
        cam_src = Gst.ElementFactory.make('tcpclientsrc', c_name + "_src")
        cam_src.set_property('host', self.__source["ip"])
        cam_src.set_property('port', self.__source["port"])
        source_bin.add(cam_src)
        
        gdpdepay = Gst.ElementFactory.make('gdpdepay', None)
        source_bin.add(gdpdepay)
        
        rtpdepay = Gst.ElementFactory.make('rtph264depay', None)
        source_bin.add(rtpdepay)
        
        h264parse = Gst.ElementFactory.make('h264parse', None)
        source_bin.add(h264parse)
        
        cam_src.link(gdpdepay)
        gdpdepay.link(rtpdepay)
        rtpdepay.link(h264parse)
        
        gh_pad = Gst.GhostPad.new('src', h264parse.get_static_pad('src'))
        gh_pad.set_active(True)
        source_bin.add_pad(gh_pad)
        
        return source_bin
        
        
    def __createVideoSinkBin(self):
        c_name = self.get_camera_name().lower()
        
        sink_bin = Gst.ElementFactory.make('bin', c_name + "_vidsink_bin")
        
        queue = Gst.ElementFactory.make('queue', None)
        sink_bin.add(queue)
        
        avdec = Gst.ElementFactory.make('avdec_h264', None)
        sink_bin.add(avdec)
        
        conv1 = Gst.ElementFactory.make('videoconvert', None)
        sink_bin.add(conv1)
        
        self.videocrop = Gst.ElementFactory.make('videocrop', c_name + "_crop")
        sink_bin.add(self.videocrop)
        
        scale = Gst.ElementFactory.make('videoscale', None)
        sink_bin.add(scale)
        
        caps = Gst.caps_from_string("video/x-raw, width=" + str(self._size[0]) + ", height=" + str(self._size[1]))
        capsfilter = Gst.ElementFactory.make('capsfilter', None)
        capsfilter.set_property('caps', caps)
        sink_bin.add(capsfilter)
        
        conv2 = Gst.ElementFactory.make('videoconvert', None)
        sink_bin.add(conv2)
        
        if self.IS_LINUX:
            self._vid_sink = Gst.ElementFactory.make('xvimagesink', c_name + "_videosink")
        else:
            self._vid_sink = Gst.ElementFactory.make('d3dvideosink', c_name + "_videosink")
        self._vid_sink.set_property('sync', False)
        sink_bin.add(self._vid_sink)
        
        queue.link(avdec)
        avdec.link(conv1)
        conv1.link(self.videocrop)
        self.videocrop.link(scale)
        scale.link(capsfilter)
        capsfilter.link(conv2)
        conv2.link(self._vid_sink)
        
        gh_pad = Gst.GhostPad.new('sink', queue.get_static_pad('sink'))
        gh_pad.set_active(True)
        sink_bin.add_pad(gh_pad)
        
        return sink_bin
    
    def _on_video_loading(self, widget, event):
        self._rec_image.set_from_stock(self.RECORD_IMAGE, Gtk.IconSize.LARGE_TOOLBAR)
        self._rec_text.set_text(self.RECORDING)
        
    def get_size(self):
        return self._size
        
    def set_size(self, size):
        if not isinstance(size, tuple):
            print("Not compatible argument type.")
            return False
            
        self._size = size
        self.set_size_request(size[0], size[1]+20)
        return True

    def get_bin(self):
        return self.__camera_bin
        
    def get_camera_name(self):
        return self.__name

    def __set_camera_name(self, name):
        self.__name = name
        
    def get_source(self):
        return self.__source
        
    def __set_source(self, source):
        self.__source = source
        
    def set_save_timeout(self, timeout):
        self.__save_timeout = timeout
        
    def get_save_timeout(self):
        return self.__save_timeout
        
        