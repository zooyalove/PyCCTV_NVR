#!/usr/bin/python3

import sys, os

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
from gi.repository import GdkX11, GstVideo

from src.controller.camerawidget import CameraWidget 

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
        
        cam1 = CameraWidget("CAM1", source={'ip':'songsul.iptime.org', 'port':5001})
        self.add_camera(vbox, cam1)
        
        hbox = Gtk.HBox()
        vbox.pack_end(hbox, False, False, 10)
        
        hbox.pack_start(Gtk.Label(), True, True, 0)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_IN, Gtk.IconSize.DIALOG)
        zoomin = Gtk.Button()
        zoomin.set_image(image)
        zoomin.set_can_focus(False)
        zoomin.set_margin_left(10)
        hbox.pack_start(zoomin, False, False, 3)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_100, Gtk.IconSize.DIALOG)
        zoom100 = Gtk.Button()
        zoom100.set_image(image)
        zoom100.set_can_focus(False)
        hbox.pack_start(zoom100, False, False, 3)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_OUT, Gtk.IconSize.DIALOG)
        zoomout = Gtk.Button()
        zoomout.set_image(image)
        zoomout.set_can_focus(False)
        hbox.pack_start(zoomout, False, False, 3)
        
        grid = Gtk.Grid()
        arwLeft = Gtk.Button()
        arwLeft.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        
        arwTop = Gtk.Button()
        arwTop.add(Gtk.Arrow(Gtk.ArrowType.UP, Gtk.ShadowType.NONE))

        arwRight = Gtk.Button()
        arwRight.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))

        arwBottom = Gtk.Button()
        arwBottom.add(Gtk.Arrow(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE))
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_FIT, Gtk.IconSize.BUTTON)
        
        arwCenter = Gtk.Button()
        arwCenter.set_image(image)
        
        grid.attach(arwTop, 1, 0, 1, 1)
        grid.attach(arwLeft, 0, 1, 1, 1)
        grid.attach(arwCenter, 1, 1, 1, 1)
        grid.attach(arwRight, 2, 1, 1, 1)
        grid.attach(arwBottom, 1, 2, 1, 1)
        
        hbox.pack_start(grid, False, False, 2)
        hbox.pack_start(Gtk.Label(), True, True, 0)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_QUIT, Gtk.IconSize.DIALOG)
        
        boxHdd = Gtk.VBox()
        boxHdd.pack_start(Gtk.Label(), True, True, 0)
        
        self.lvlHDD = Gtk.LevelBar()
        self.lvlHDD.set_min_value(0.0)
        self.lvlHDD.set_max_value(1.0)
        self.lvlHDD.set_value(0.5)
        self.lvlHDD.set_size_request(300, -1)
        self.lvlHDD.set_margin_right(10)
        boxHdd.pack_start(self.lvlHDD, True, False, 5)
        
        self.lblHdd_Percent = Gtk.Label()
        self.lblHdd_Percent.set_text("Usage / Total - 50%")
        boxHdd.pack_start(self.lblHdd_Percent, True, True, 0)
        boxHdd.pack_end(Gtk.Label(), True, True, 0)
        
        hbox.pack_start(boxHdd, True, True, 0)
        
        quitBtn = Gtk.Button()
        quitBtn.set_image(image)
        quitBtn.set_margin_right(10)
        hbox.pack_start(quitBtn, False, False, 0)
        
        hbox.pack_start(Gtk.Label(), True, True, 0)
        
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
        self.window.start()
        
    def do_startup(self):
        Gtk.Application.do_startup(self)
        
if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)

    app = PurunNVR()
    sys.exit(app.run(sys.argv))