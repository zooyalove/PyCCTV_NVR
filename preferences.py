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
    <general>
        <period>30</period>
        <save_dir>%s</save_dir>
    </general>
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
            <msg_body</msg_body>
        </email>
    </service_provider>
    <video>
        <motion>1</motion>
        <timeout>30</timeout>
    </video>
    <snapshot>
        <prefix>sshot_</prefix>
        <quality>80</quality>
    </snapshot>
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
    def __init__(self, app, parent=None):
        '''
        Constructor
        '''
        # self._file = os.path.join(app.RESOURCE_PATH, 'preferences.xml')
        self._prefdlg = None
        self._app = app
        self._parent = parent
        self._data = None
        self._exists = False

        self._data_init()

    def _data_init(self):
        # self._exists, self._data = xml_parse(self._file)
        pass

    def _get_preferences(self):
        pass

    def _create_ui(self, data):
        print(data)
        notebook = Gtk.Notebook()

        general = self._create_general()
        notebook.append_page(general, Gtk.Label(u'일반'))

        video = self._create_video()
        notebook.append_page(video, Gtk.Label(u'영상'))

        snapshot = self._create_snapshot()
        notebook.append_page(snapshot, Gtk.Label(u'사진'))

        notebook.connect('switch-page', self._on_switch_page)
        notebook.show_all()
        return notebook

    def _create_top_label(self, label):
        vbox = Gtk.VBox()
        vbox.set_border_width(10)
        top_label = Gtk.Label(label)
        top_label.set_halign(Gtk.Align.START)
        vbox.pack_start(top_label, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep, False, True, 5)
        return vbox

    def _create_general(self):
        vbox = self._create_top_label(u'일반 :')
        return vbox

    def _create_video(self):
        vbox = self._create_top_label(u'영상 :')
        return vbox

    def _create_snapshot(self):
        vbox = self._create_top_label(u'사진 :')

        pb_frame = self._create_pushbullet()
        vbox.pack_start(pb_frame, True, True, 10)

        em_frame = self._create_email()
        vbox.pack_start(em_frame, True, True, 10)
        return vbox

    def _create_pushbullet(self):
        pb_frame = Gtk.Frame(label='Pushbullet')
        pb_vbox = Gtk.VBox()
        self._pb_check = Gtk.CheckButton(u"사용")
        pb_vbox.pack_start(self._pb_check, False, False, 5)
        pb_frame.add(pb_vbox)
        return pb_frame

    def _create_email(self):
        em_frame = Gtk.Frame(label='E-mail')
        em_vbox = Gtk.VBox()
        self._em_check = Gtk.CheckButton(u"사용")
        em_vbox.pack_start(self._em_check, False, False, 5)
        em_frame.add(em_vbox)
        return em_frame

    def _on_switch_page(self, notebook, page, page_num):
        if page_num == 2:
            self._prefdlg.resize(400, 500)
        else:
            self._prefdlg.resize(400, 300)

    def is_exists(self):
        return self._exists

    def set_parent(self, parent):
        if isinstance(parent, Gtk.Window):
            self._parent = parent

    '''
    @return: preferences's data xml
    @rtype: Gtk.ResponseType
    '''
    def run(self):
        self._prefdlg = Gtk.Dialog(u'Preference', self._parent,
                                   Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self._prefdlg.set_position(Gtk.WindowPosition.CENTER)
        self._prefdlg.set_size_request(400, 300)
        self._prefdlg.set_border_width(5)
        self._prefdlg.set_transient_for(self._parent)

        content_box = self._prefdlg.get_content_area()
        nb = self._create_ui(self._data)
        content_box.add(nb)

        hsep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        hsep.show()
        content_box.pack_end(hsep, False, True, 5)

        response = self._prefdlg.run()
        if response == Gtk.ResponseType.OK:
            pass
        self._prefdlg.destroy()

        return self._get_preferences()

if __name__ == '__main__':
    pref = Preferences(None, parent=Gtk.Window(Gtk.WindowType.TOPLEVEL))
    pref.run()
