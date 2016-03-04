#!/usr/bin/python3

import sys, os, threading, time

import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
#from gi.repository import GdkX11, GstVideo

from pushbullet import Pushbullet

from nvrmanager import NvrManager
from camerawidget import CameraWidget 

PB_API_KEY = 'o.cJzinoZ3SdlW7JxYeDm7tbIrueQAW5aK'

class NvrController(threading.Thread):
    def __init__(self, mntdir):
        super(NvrController, self).__init__()
        
        self.sleepTime = 30 #minute
        
        self.mntdir = mntdir
        
        self.panel = Gtk.VBox()
        
        self.lvlHDD = Gtk.LevelBar()
        self.lvlHDD.set_min_value(0.0)
        self.lvlHDD.set_max_value(1.0)
        self.lvlHDD.set_value(0.0)
        self.lvlHDD.set_size_request(250, -1)
        self.lvlHDD.set_margin_left(10)
        self.lvlHDD.set_margin_right(10)
        self.panel.pack_start(self.lvlHDD, False, False, 5)
        
        self.lblHdd_Percent = Gtk.Label()
        self.lblHdd_Percent.set_text("Usage / Total - 0%")
        self.panel.pack_start(self.lblHdd_Percent, True, False, 0)
        
        
    def run(self):
        while True:
            self.calculate_diskusage()
            time.sleep(self.sleepTime * 60)
    
    def stop(self):
        self.bTerminate = not self.bTerminate

    def get_panel(self):
        return self.panel
    
    def calculate_diskusage(self):
        if hasattr(os, 'statvfs'):
            st = os.statvfs(self.mntdir)
            total = st.f_blocks * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
        else:
            import ctypes
            _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
            ret = fun(self.mntdir, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
            if ret == 0:
                raise ctypes.WinError()
            used = total.value - free.value
            print(used)
            total = total.value
            print(total)
        
        f = round(used/total, 3)
        percentage = "%0.1f" % (f * 100)
        
        self.lvlHDD.set_value(f)
        self.lblHdd_Percent.set_text("Usage {0} / Total {1} - {2}%".format(self.calculate_disksize(used), self.calculate_disksize(total), percentage))
    
    def calculate_disksize(self, dsize):
        dsize_format = ('Byte','KB', 'MB', 'GB', 'TB')
        count = 0
        
        while dsize >= 1024:
            dsize = round(float(dsize) / 1024, 1)
            count += 1
        
        return '%0.1f%s' % (dsize, dsize_format[count])
    
        
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

        hbox = Gtk.HBox()
        vbox.pack_end(hbox, False, False, 10)
        
        hbox.pack_start(Gtk.Label(), True, True, 0)
        
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_QUIT, Gtk.IconSize.BUTTON)
        quitBtn = Gtk.Button()
        quitBtn.set_image(image)
        quitBtn.set_margin_right(10)
        quitBtn.set_tooltip_text('프로그램 끝내기')
        quitBtn.connect('clicked', self.quit)
        hbox.pack_end(quitBtn, False, False, 0)
        
        if os.name == 'nt':
            self.controller = NvrController('D:\\')
        else:
            self.controller = NvrController('/home/zia')

        self.controller.setDaemon(True)
        hbox.pack_end(self.controller.get_panel(), False, False, 0)
        
    def start(self):
        self.win.show_all()
        self.manager.start()
        self.controller.start()
        Gtk.main()
                
    def quit(self, widget):
        self.manager.stop()
        Gtk.main_quit()
        
                
if __name__ == "__main__":
    GObject.threads_init()
    Gdk.threads_init()
    Gst.init(None)

    app = PurunNVR()
    app.start()
