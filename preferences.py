'''
Created on 2016. 4. 18.

@author: zia

'''
from gi.repository import Gtk

import os
import gi
gi.require_version('Gtk', '3.0')

DEFAULT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_PREF = '''<preferences>
    <service-provider>
        <pushbullet use="0">
            <token></token>
            <channel></channel>
        </pushbullet>
        <email use="0"></email>
    </service-provider>
    <video-period period="30">10</video-period>
    <save-dir>%s</save-dir>
    <>
    <>
</preferences>''' % DEFAULT_PATH


class Preferences(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self._prefdlg = None
