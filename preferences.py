'''
Created on 2016. 4. 18.

@author: zia

'''
import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

DEFAULT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_PREF = '''<preferences>
    <service-provider>
        <pushbullet use="0">
            <token></token>
            <channel></channel>
        </pushbullet>
        <email use="0">
            <smtpsrv-addr>smtp.gmail.com</smtpsrv-addr>
            <smtpsrv-port></smtpsrv-port>
            <from></from>
            <to></to>
            <subject></subject>
            <msg-body</msg-body>
        </email>
    </service-provider>
    <video>
        <period>30</period>
        <timeout>10</timeout>
        <motion>1</motion>
    </video>
    <snapshot prefix="sshot_" />
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
