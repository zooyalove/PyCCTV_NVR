#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import Gdk

from splashscreen import Splashscreen
from preferences import Preferences
from nvrwindow import NvrWindow

PB_API_KEY = 'o.cJzinoZ3SdlW7JxYeDm7tbIrueQAW5aK'

'''
    - PurunNVR 클래스의 기능 -
        > 화면 보이기
        > 파일 저장하기 
        > 모션 감지시 사진 저장하고 PushBullet으로 사진 전송하기 
        > 모션감지는 설정에 의해서 기능가능 여부를 판단한다 
'''


class PurunNVR(object):
    MAX_CAMERA_NUM = 4
    APP_PATH = os.path.abspath(os.path.dirname(__file__))
    RESOURCE_PATH = os.path.join(APP_PATH, 'resources')

    def __init__(self):
        '''self.config = {}
        if mntdir is None:
            self.config['VIDEO_PATH'] = os.path.join(self.APP_PATH, 'videos')
            self.config['SNAPSHOT_PATH'] = os.path.join(self.APP_PATH, 'snapshot')
        else:
            self.config['VIDEO_PATH'] = os.path.join(mntdir, 'videos')
            self.config['SNAPSHOT_PATH'] = os.path.join(mntdir, 'snapshot')

        self.config['SNAPSHOT_PREFIX'] = 'sshot_'
        self.config['Motion'] = True
        self.config['Timeout'] = 30 * 60'''

        # self.pb = Pushbullet(PB_API_KEY)
        self.pref = Preferences(self)
        self._setupUI()

    def _setupUI(self):
        self.win = NvrWindow(self)

    def start(self):
        self.win.start()
        Gtk.main()


if __name__ == "__main__":
    GObject.threads_init()
    Gdk.threads_init()
    Gst.init(None)

    spl = Splashscreen('purun_nvr.png')
    while Gtk.events_pending():
        Gtk.main_iteration()

    app = PurunNVR()
    spl.destroy()
    app.start()
