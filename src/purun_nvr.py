#!/usr/bin/python3

import os

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk
#from gi.repository import GdkX11, GstVideo

from pushbullet import Pushbullet

from src.controller.nvrmanager import NvrManager
from src.controller.camerawidget import CameraWidget 

PB_API_KEY = 'o.cJzinoZ3SdlW7JxYeDm7tbIrueQAW5aK'

"""
    - PurunNVR 클래스의 기능 -
        > 화면 보이기
        > 파일 저장하기 
        > 화면 확대, 축소, 원점으로 되돌리기
        > 화면 이동하기(좌, 우, 상, 하)
        > 모션 감지시 사진 저장하고 PushBullet으로 사진 전송하기 
        > 모션감지는 설정에 의해서 기능가능 여부를 판단한다 
"""
class PurunNVR(object):
    
    MAX_CAMERA_NUM = 4
    APP_PATH = os.path.abspath(os.path.dirname(__file__))
    RESOURCE_PATH = os.path.join(APP_PATH, 'resources')
    VIDEO_PATH = os.path.join(APP_PATH, 'videos')
    SNAPSHOT_PATH = os.path.join(APP_PATH, 'snapshot')
    SNAPSHOT_PREFIX = 'sshot_'    
    
    def __init__(self):
        self.pb = Pushbullet(PB_API_KEY) 
        self.setupUI()

        #cam1 = CameraWidget("CAM1", source={'ip':'songsul.iptime.org', 'port':5001})
        #self.manager.add_camera(cam1)
        cam1 = CameraWidget(self, "CAM1", source=None)
        self.manager.add_camera(cam1)
        
    def setupUI(self):
        self.win = Gtk.Window(title="PyCCTV NVR")
        self.win.set_position(Gtk.WindowPosition.CENTER)
        self.win.set_size_request(660, 500)
        self.win.set_border_width(5)
        self.win.connect('destroy', self.quit)
        
        vbox = Gtk.VBox()
        
        self.manager = NvrManager(self)
        vbox.add(self.manager)
        self.win.add(vbox)
        
        hbox = Gtk.HBox()
        vbox.pack_end(hbox, False, False, 10)
        
        hbox.pack_start(Gtk.Label(), True, True, 0)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_IN, Gtk.IconSize.DIALOG)
        zoomin = Gtk.Button()
        zoomin.set_image(image)
        zoomin.set_margin_left(10)
        zoomin.set_tooltip_text('화면 확대')
        hbox.pack_start(zoomin, False, False, 3)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_100, Gtk.IconSize.DIALOG)
        zoom100 = Gtk.Button()
        zoom100.set_image(image)
        zoom100.set_tooltip_text('원본 화면')
        zoom100.set_sensitive(False)
        hbox.pack_start(zoom100, False, False, 3)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_OUT, Gtk.IconSize.DIALOG)
        zoomout = Gtk.Button()
        zoomout.set_image(image)
        zoomout.set_tooltip_text('화면 축소')
        zoomout.set_sensitive(False)
        hbox.pack_start(zoomout, False, False, 3)
        
        grid = Gtk.Grid()
        grid.set_column_spacing(2)
        grid.set_row_spacing(2)
        
        arwLeft = Gtk.Button()
        arwLeft.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        arwLeft.set_tooltip_text('왼쪽으로 화면 이동')
        
        arwTop = Gtk.Button()
        arwTop.add(Gtk.Arrow(Gtk.ArrowType.UP, Gtk.ShadowType.NONE))
        arwTop.set_tooltip_text('상단으로 화면 이동')

        arwRight = Gtk.Button()
        arwRight.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        arwRight.set_tooltip_text('오른쪽으로 화면 이동')

        arwBottom = Gtk.Button()
        arwBottom.add(Gtk.Arrow(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE))
        arwBottom.set_tooltip_text('하단으로 화면 이동')
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ZOOM_FIT, Gtk.IconSize.BUTTON)
        
        arwCenter = Gtk.Button()
        arwCenter.set_image(image)
        arwCenter.set_tooltip_text('원점으로 화면 재배치')
        
        grid.attach(arwTop, 1, 0, 1, 1)
        grid.attach(arwLeft, 0, 1, 1, 1)
        grid.attach(arwCenter, 1, 1, 1, 1)
        grid.attach(arwRight, 2, 1, 1, 1)
        grid.attach(arwBottom, 1, 2, 1, 1)
        
        hbox.pack_start(grid, False, False, 2)
        hbox.pack_start(Gtk.Label(), True, True, 0)
        
        boxHdd = Gtk.VBox()
        boxHdd.pack_start(Gtk.Label(), True, True, 0)
        
        self.lvlHDD = Gtk.LevelBar()
        self.lvlHDD.set_min_value(0.0)
        self.lvlHDD.set_max_value(1.0)
        self.lvlHDD.set_value(0.5)
        self.lvlHDD.set_size_request(300, -1)
        self.lvlHDD.set_margin_left(10)
        self.lvlHDD.set_margin_right(10)
        boxHdd.pack_start(self.lvlHDD, True, False, 5)
        
        self.lblHdd_Percent = Gtk.Label()
        self.lblHdd_Percent.set_text("Usage / Total - 50%")
        boxHdd.pack_start(self.lblHdd_Percent, True, True, 0)
        boxHdd.pack_end(Gtk.Label(), True, True, 0)
        
        hbox.pack_start(boxHdd, True, True, 0)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_QUIT, Gtk.IconSize.DIALOG)
        quitBtn = Gtk.Button()
        quitBtn.set_image(image)
        quitBtn.set_margin_right(10)
        quitBtn.set_tooltip_text('프로그램 끝내기')
        quitBtn.connect('clicked', self.quit)
        hbox.pack_start(quitBtn, False, False, 0)
        
        hbox.pack_start(Gtk.Label(), True, True, 0)
        

    def on_zoomin(self, widget):
        pass
    
    def on_zoomout(self, widget):
        pass
    
    def start(self):
        self.win.show_all()
        self.manager.start()
        Gtk.main()
                
    def quit(self, widget):
        self.manager.stop()
        Gtk.main_quit()
        
                
if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)

    app = PurunNVR()
    app.start()
