import sys, os, time, threading

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, Pango

from src.controller.gstelements import CameraBin
from src.controller.videowidget import VideoWidget

class CameraWidget(Gtk.VBox):
    IS_LINUX = sys.platform.startswith("linux")
    NOT_RECORD = "Don't Recording."
    RECORDING = "Now Recording..."
    
    RECORD_IMAGE = Gtk.STOCK_MEDIA_RECORD
    
    def __init__(self, app, name, source={'ip':'127.0.0.1', 'port':6001}, dest={'ip':'127.0.0.1', 'port':5001}, size=(640, 360), save_timeout=60):
        super(CameraWidget, self).__init__()

        self.app = app
        self.is_recording = False
        self.__camera_bin = None
        
        self._video_dir_config(name)
        self.set_source(source)
        self.__set_camera_name(name)
        self.set_size(size)
        self.set_save_timeout(save_timeout) # save_timeout => minute
        self._setupUI()

    def _video_dir_config(self, name):
        name = name.upper()
        dir_name = os.path.join(self.app.VIDEO_PATH, name)
        if not os.path.exists(dir_name):
            pass
            #os.mkdir(dir_name)
            
        self.VIDEO_DIR = dir_name
                
    def _setupUI(self):
        
        self._overlay = Gtk.Overlay()
        self.pack_start(self._overlay, True, True, 0)
        
        # Video screen renderer object initialize
        self.video_widget = VideoWidget(self)
        self.video_widget.set_size_request(self._size[0], self._size[1])
        
        self._overlay.add(self.video_widget)

        if self.__source is None:
            self.logo = Gtk.Image()
            self.logo.set_from_file(os.path.join(self.app.RESOURCE_PATH, 'purun_nvr.png'))
            self.logo.set_halign(Gtk.Align.CENTER)
            self.logo.set_valign(Gtk.Align.CENTER)
            self._overlay.add_overlay(self.logo)
        
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
        self._rec_image.set_from_stock(self.RECORD_IMAGE, Gtk.IconSize.LARGE_TOOLBAR)
        self._rec_image.set_margin_right(5)
        hbox.pack_start(self._rec_image, False, False, 0)
        
        self._rec_text = Gtk.Label(self.NOT_RECORD)
        self._rec_text.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('white'))
        self._rec_text.set_margin_right(10)
        hbox.pack_start(self._rec_text, False, False, 0)

        self._overlay.add_overlay(hbox)
            
        self.show_all()
    
    
    def __createCameraBin(self, source, dest):
        if self.__camera_bin is not None:
            self.__camera_bin = None
        
        self.__camera_bin = CameraBin(source, dest, self.app, self.get_camera_name().lower())
        self.__camera_bin.connect('recording', self._on_video_recording)
        
    
    def _on_video_recording(self, cambin, bRecord):
        self.is_recording = bRecord
        if self.is_recording:
            def record_blink():
                while self.is_recording:
                    if self._rec_image.get_opacity() > 0.3:
                        self._rec_image.set_opacity(0.3)
                    else:
                        self._rec_image.set_opacity(1.0)
                        
                    time.sleep(1)
            
            t = threading.Thread(target=record_blink)
            t.start()
            
            self._rec_text.set_text(self.RECORDING)
        else:
            self._rec_image.set_opacity(1.0)
            self._rec_text.set_text(self.NOT_RECORD)
        
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
        
    def set_source(self, source):
        self.__source = source
        if source is not None:
            self.__createCameraBin(source)
        
    def set_save_timeout(self, timeout):
        self.__save_timeout = timeout
        
    def get_save_timeout(self):
        return self.__save_timeout
        
        