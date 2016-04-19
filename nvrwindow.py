'''
Created on 2016. 4. 18.

@author: Administrator
'''
from gi.repository import Gtk
from gi.repository import GLib
from nvrmanager import NvrManager
from camerawidget import CameraWidget

import os
import gi
gi.require_version('Gtk', '3.0')


class NvrWindow(Gtk.Window):
    def __init__(self, app):
        super(NvrWindow, self).__init__(Gtk.WindowType.TOPLEVEL)

        self.app = app
        self.manager = NvrManager(app)

        if os.name == 'nt':
            self.mntdir = 'D:\\'
        else:
            self.mntdir = '/home/zia'

        self._setupUI()

    def _setupUI(self):
        self.set_default_icon_from_file(os.path.join(self.app.RESOURCE_PATH, 'purun_nvr_16.png'))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_size_request(660, 500)
        self.set_border_width(5)
        self.set_title(u'Purun CCTV NVR')
        self.connect('destroy', self.quit)

        vbox = Gtk.VBox()
        self.add(vbox)

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

        panel = Gtk.VBox()

        self.lvlHDD = Gtk.LevelBar()
        self.lvlHDD.set_min_value(0.0)
        self.lvlHDD.set_max_value(1.0)
        self.lvlHDD.set_value(0.0)
        self.lvlHDD.set_size_request(250, -1)
        self.lvlHDD.set_margin_left(10)
        self.lvlHDD.set_margin_right(10)
        panel.pack_start(self.lvlHDD, False, False, 5)

        self.lblHdd_Percent = Gtk.Label()
        self.lblHdd_Percent.set_text("Usage / Total - 0%")
        panel.pack_start(self.lblHdd_Percent, True, False, 0)

        hbox.pack_end(panel, False, False, 0)

        # cam1 = CameraWidget("CAM1", source={'ip':'192.168.0.81', 'port':6001}, dest={'ip':'192.168.0.79', 'port':5001})
        # self.manager.add_camera(cam1)
        cam1 = CameraWidget(self, "CAM1", source=None, dest=None)
        self.manager.add_camera(cam1)
        cam2 = CameraWidget(self, "CAM2", source=None, dest=None)
        self.manager.add_camera(cam2)

    def _calculate_diskusage(self):
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
            total = total.value

        f = round(used/total, 3)
        percentage = "%0.1f" % (f * 100)

        self.lvlHDD.set_value(f)
        self.lblHdd_Percent.set_text("Usage {0} / Total {1} - {2}%".format(self._calculate_disksize(used), self._calculate_disksize(total), percentage))

        return True

    def _calculate_disksize(self, dsize):
        dsize_format = ('Byte', 'KB', 'MB', 'GB', 'TB')
        count = 0

        while dsize >= 1024:
            dsize = round(float(dsize) / 1024, 1)
            count += 1

        return '%0.1f%s' % (dsize, dsize_format[count])

    def start(self):
        self.show_all()
        self.manager.start()
        GLib.timeout_add(4, self._calculate_diskusage)

    def quit(self, widget):
        self.manager.stop()
        Gtk.main_quit()
