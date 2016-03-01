#!/usr/bin/python3

import os, threading, time

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
#from gi.repository import GdkX11, GstVideo

from pushbullet import Pushbullet

from src.controller.nvrmanager import NvrManager
from src.controller.camerawidget import CameraWidget 

PB_API_KEY = 'o.cJzinoZ3SdlW7JxYeDm7tbIrueQAW5aK'

class NvrController(threading.Thread):
    def __init__(self, mntdir):
        self.bTerminate = False
        self.sleepTime = 30 #minute
        
        self.mntdir = mntdir
        
        self.panel = Gtk.HBox()
        
        self.panel.pack_start(Gtk.Label(), True, True, 0)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_QUIT, Gtk.IconSize.BUTTON)
        quitBtn = Gtk.Button()
        quitBtn.set_image(image)
        quitBtn.set_margin_right(10)
        quitBtn.set_tooltip_text('프로그램 끝내기')
        quitBtn.connect('clicked', self.quit)
        self.panel.pack_end(quitBtn, False, False, 0)
        
        boxHdd = Gtk.VBox()
        
        self.lvlHDD = Gtk.LevelBar()
        self.lvlHDD.set_min_value(0.0)
        self.lvlHDD.set_max_value(1.0)
        self.lvlHDD.set_value(0.1)
        self.lvlHDD.set_size_request(250, -1)
        self.lvlHDD.set_margin_left(10)
        self.lvlHDD.set_margin_right(10)
        boxHdd.pack_start(self.lvlHDD, False, False, 5)
        
        self.lblHdd_Percent = Gtk.Label()
        self.lblHdd_Percent.set_text("Usage / Total - 0%")
        boxHdd.pack_start(self.lblHdd_Percent, True, False, 0)
        
        self.panel.pack_end(boxHdd, False, False, 0)
        
    def run(self):
        while not self.bTerminate:
            self.calculate_diskusage()
            time.sleep(self.sleepTime * 60)
        
    def calculate_diskusage(self):
        st = os.statvfs(self.mntdir)
        total_space = st.f_blocks * st.f_frsize
        used_space = (st.f_blocks - st.f_bfree) * st.f_frsize
        
        f = round(used_space/total_space, 2)
        percentage = int(f * 100)
        
        self.lvlHDD.set_value(f)
        self.lblHdd_Percent.set_text("Usage {0} / Total {1} - {2}%".format(percentage))
    
        
"""
    - PurunNVR 클래스의 기능 -
        > 화면 보이기
        > 파일 저장하기 
        > 모션 감지시 사진 저장하고 PushBullet으로 사진 전송하기 
        > 모션감지는 설정에 의해서 기능가능 여부를 판단한다 
"""
class PurunNVR(object):
    
    MAX_CAMERA_NUM = 4
    APP_PATH = os.path.abspath(os.path.dirname(__file__))
    RESOURCE_PATH = os.path.join(APP_PATH, 'resources')
    
    def __init__(self):
        self.config = {}
        self.config['VIDEO_PATH'] = os.path.join(self.APP_PATH, 'videos')
        self.config['SNAPSHOT_PATH'] = os.path.join(self.APP_PATH, 'snapshot')
        self.config['SNAPSHOT_PREFIX'] = 'sshot_'
        self.config['Motion'] = True
        self.config['Timeout'] = 30 * 60
            
        self.pb = Pushbullet(PB_API_KEY) 
        self.setupUI()

        #cam1 = CameraWidget("CAM1", source={'ip':'songsul.iptime.org', 'port':5001})
        #self.manager.add_camera(cam1)
        cam1 = CameraWidget(self, "CAM1", source=None, dest=None)
        self.manager.add_camera(cam1)
        
    def setupUI(self):
        self.win = Gtk.Window(title="PyCCTV NVR")
        self.win.set_position(Gtk.WindowPosition.CENTER)
        self.win.set_size_request(660, 500)
        self.win.set_border_width(5)
        self.win.connect('destroy', self.quit)
        
        vbox = Gtk.VBox()
        self.win.add(vbox)
        
        self.manager = NvrManager(self)
        vbox.add(self.manager)

        self.controller = NvrController()
                
        vbox.pack_end(self.controller.panel, False, False, 10)
        
    def start(self):
        self.win.show_all()
        self.manager.start()
        Gtk.main()
                
    def quit(self, widget):
        self.manager.stop()
        self.controller.bTerminate = True
        Gtk.main_quit()
        
                
if __name__ == "__main__":
    GObject.threads_init()
    Gdk.threads_init()
    Gst.init(None)

    app = PurunNVR()
    app.start()
