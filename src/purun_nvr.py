#!/usr/bin/python3

import sys, os

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
from gi.repository import GdkX11, GstVideo

#from videoplayer import VideoPlayer
from src.camerawidget import CameraWidget

"""
    - PurunNVR 클래스의 기능 -
        > 화면 보이기
        > 파일 저장하기 
        > 화면 확대, 축소, 원점으로 되돌리기
        > 화면 이동하기(좌, 우, 상, 하)
        > 모션 감지시 사진 저장하고 PushBullet으로 사진 전송하기 
        > 모션감지는 설정에 의해서 기능가능 여부를 판단한다 
"""
class NvrWindow(Gtk.ApplicationWindow):
    
    MAX_CAMERA_NUM = 4
    
    def __init__(self, app):
        Gtk.Window.__init__(self, title="PyCCTV NVR", application=app)
        self.app = app
        
        self.cameras = dict()
        self.player = Gst.Pipeline.new('CCTV_NVR')
        self.player_configure()
        self.setupUI()

    def setupUI(self):
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_size_request(660, 500)
        self.connect('destroy', self.on_window_quit)
        
        vbox = Gtk.VBox()
        self.add(vbox)
        
        cam1 = CameraWidget("CAM1", source={'ip':'songsul.iptime.org', 'port':5000})
        self.add_camera(vbox, cam1)
        
        hbox = Gtk.HBox()
        vbox.pack_end(hbox, True, False, 5)
        
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        
        toolItem = Gtk.ToolItem()
        lvlHDD = Gtk.LevelBar()
        lvlHDD.set_min_value(0.0)
        lvlHDD.set_max_value(100.0)
        lvlHDD.set_value(50.0)
        toolItem.add(lvlHDD)
        toolItem.set_hexpand(True)
        toolbar.insert(toolItem)
        
        sep = Gtk.SeparatorToolItem()
        toolbar.insert(sep)
        
        quitBtn = Gtk.ToolButton(Gtk.STOCK_QUIT)
        toolbar.insert(quitBtn)
        
        hbox.pack_start(toolbar, True, False, 0)
        
    def add_camera(self, box, camera):
        # 카메라화면 추가
        box.add(camera)
        
        camera_name = camera.get_camera_name().lower()
        print("Camera name : %s" % camera_name)
        self.cameras[camera_name] = camera
    
        self.player.add(camera.get_bin())
        
    def player_configure(self):    
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        
        def sync_msg_handler(bus, msg):
            if msg.get_structure().get_name() == "prepare-window-handle":
                sink = msg.src
                sink_name = sink.get_name()[:sink.get_name().find('_')]
                print("Sink name : %s" % sink_name)
                self.cameras[sink_name].video_widget.set_sink(sink)
                
        bus.connect('sync-message::element', sync_msg_handler)
        

    def start(self):
        self.show_all()
        self.player.set_state(Gst.State.PLAYING)
                
    def on_window_quit(self, window):
        self.player.set_state(Gst.State.NULL)
        self.app.quit()
        
    def on_message(self, bus, msg):
        pass
       
                
class PurunNVR(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)
        
    def do_activate(self):
        self.window = NvrWindow(self)
        
    def do_startup(self):
        Gtk.Application.do_startup(self)
        

GObject.threads_init()
Gst.init(None)

app = PurunNVR()
sys.exit(app.run(sys.argv))