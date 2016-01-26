#!/usr/bin/python3

import sys

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
from gi.repository import GdkX11, GstVideo
from pushbullet import Pushbullet
from videoPlayer import VideoPlayer

"""
    - PurunNVR 클래스의 기능 -
        > 화면 보이기
        > 파일 저장하기 
        > 모션 감지시 사진 저장하고 PushBullet으로 사진 전송하기 
        > 모션감지는 설정에 의해서 기능가능 여부를 판단한다 
"""
class NvrWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.Window.__init__(self, title="PyCCTV NVR", application=app)

        self.setupUI()

    def setupUI(self):
        self.type = Gtk.WindowType.TOPLEVEL
        
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_size_request(660, 500)
        self.connect('destroy', self.on_window_quit)
        
        vbox = Gtk.VBox()
        self.add(vbox)
        
        self.videowidget = Gtk.DrawingArea()
        self.videowidget.set_size_request(640, 480)
        vbox.add(self.videowidget)
    
        VideoPlayer()

        self.player = Gst.Pipeline.new('CCTV_NVR')
        
    def on_window_quit(self, window):
        self.player.set_state(Gst.State.NULL)
        
    def on_message(self, bus, msg):
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
            
        
    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == "prepare-window-handle":
            videosink = msg.src
            videosink.set_property('force-aspect-ratio', True)
            #videosink.set_window_handle(self.videowidget.get_property('window').get_xid())
                
class PurunNVR(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):        
        self.window = NvrWindow(self)
        self.window.show_all()
        
        
GObject.threads_init()
Gst.init(None)

app = PurunNVR()
sys.exit(app.run(sys.argv))