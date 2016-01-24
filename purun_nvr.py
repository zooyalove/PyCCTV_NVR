#!/usr/bin/python3

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
from gi.repository import GdkX11, GstVideo
from pushbullet import Pushbullet

"""
    - PurunNVR 클래스의 기능 -
        > 화면 보이기
        > 파일 저장하기 
        > 모션 감지시 사진 저장하고 PushBullet으로 사진 전송하기 
        > 모션감지는 설정에 의해서 기능가능 여부를 판단한다 
"""
class PurunNVR(object):
    def __init__(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_title("PyCCTV NVR")
        #self.window.fullscreen()
        self.window.connect('destroy', self.windowQuit)
        vbox = Gtk.VBox()
        self.window.add(vbox)
        
        self.videowidget = Gtk.DrawingArea()
        vbox.add(self.videowidget)
        
        self.window.show_all()
        
        self.player = Gst.Pipeline.new('CCTV_NVR')
        
    def windowQuit(self, window):
        self.player.set_state(Gst.State.NULL)
        Gtk.main_quit()
        
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
            videosink.set_window_handle(self.videowidget.get_property('window').get_xid())
        
if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)
    app = PurunNVR()
    Gtk.main()