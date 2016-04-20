'''
Created on 2016. 4. 18.

@author: zia

'''
import os
import gi
gi.require_version('Gtk', '3.0')

import xml.etree.ElementTree as ET

from gi.repository import Gtk

DEFAULT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_PREF = '''<preferences>
    <service_provider>
        <pushbullet use="0">
            <token></token>
            <channel></channel>
        </pushbullet>
        <email use="0">
            <smtpsrv_addr>smtp.gmail.com</smtpsrv_addr>
            <smtpsrv_port>587</smtpsrv_port>
            <username></username>
            <userpass></userpass>
            <from></from>
            <to></to>
            <subject></subject>
            <msg-body</msg-body>
        </email>
    </service_provider>
    <video>
        <period>30</period>
        <timeout>10</timeout>
        <motion>1</motion>
    </video>
    <snapshot prefix="sshot_" />
    <save_dir>%s</save_dir>
</preferences>''' % DEFAULT_PATH


def xml_parse(source):
    exists = False
    if os.path.exists(source) and os.path.isfile(source):
        data = ET.parse(source)
        exists = True
    else:
        data = ET.fromstring(DEFAULT_PREF)
    return exists, data.getroot()


class Preferences(object):
    '''
    classdocs
    '''
    def __init__(self, app, parent):
        '''
        Constructor
        '''
        self._file = os.path.join(self._app.RESOURCE_PATH, 'preferences.xml')
        self._prefdlg = None
        self._app = app
        self._parent = parent
        self._data = None
        self._exists = False

        self._data_init()

    def _data_init(self):
        self._exists, self._data = xml_parse(self._file)

    def _get_preferences(self):
        pass

    def is_exists(self):
        return self._exists

    '''
    @return: preferences's data xml
    @rtype: Gtk.ResponseType
    '''
    def run(self):
        self._prefdlg = Gtk.Dialog()

        response = self._prefdlg.run()
        if response == Gtk.ResponseType.OK:
            pass
        self._prefdlg.destroy()

        return self._get_preferences()
