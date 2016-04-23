'''
Created on 2016. 4. 18.

@author: zia

'''
import os
import gi
gi.require_version('Gtk', '3.0')

import xml.etree.ElementTree as ET

from gi.repository import Gtk
from gi.repository import GdkPixbuf
from pushbullet import Pushbullet
from pushbullet.errors import InvalidKeyError, PushbulletError

DEFAULT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_PREF = '''<?xml version="1.0" encoding="UTF-8" ?>
<preferences>
    <general>
        <period>30</period>
        <save_dir>%s</save_dir>
    </general>
    <service_provider>
        <pushbullet use="0">
            <token></token>
            <channels>
            </channels>
        </pushbullet>
        <email use="0">
            <smtpsrv_addr>smtp.gmail.com</smtpsrv_addr>
            <smtpsrv_port>587</smtpsrv_port>
            <username></username>
            <userpass></userpass>
            <from></from>
            <to></to>
            <subject></subject>
            <msg_body></msg_body>
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
    return exists, data


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
        self._verified = False

        self._data_init()

    def _data_init(self):
        # self._exists, self._data = xml_parse(self._file)
        self._exists, self._data = xml_parse(DEFAULT_PREF)

    def _get_preferences(self):
        pass

    def _create_ui(self, data):
        notebook = Gtk.Notebook()

        general = self._create_general(data.find("general"))
        notebook.append_page(general, Gtk.Label(u'일반'))

        video = self._create_video(data.find("video"))
        notebook.append_page(video, Gtk.Label(u'영상'))

        snapshot = self._create_snapshot([data.find("snapshot"), data.find("service_provider")])
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

    def _create_general(self, general_data):
        vbox = self._create_top_label(u'일반 :')
        return vbox

    def _create_video(self, video_data):
        vbox = self._create_top_label(u'영상 :')
        return vbox

    def _create_snapshot(self, sshot_datalist):
        sshot_data, svc_data = sshot_datalist[0], sshot_datalist[1]

        vbox = self._create_top_label(u'사진 :')

        pb_frame = self._create_pushbullet(svc_data.find("pushbullet"))
        vbox.pack_start(pb_frame, True, True, 10)

        em_frame = self._create_email(svc_data.find("email"))
        vbox.pack_start(em_frame, True, True, 10)
        return vbox

    def _create_pushbullet(self, pb_data):
        pb_frame = Gtk.Frame(label='Pushbullet')
        pb_vbox = Gtk.VBox()

        self._pb_check = Gtk.CheckButton(u'사용')
        self._pb_check.set_active(bool(int(pb_data.get('use'))))
        pb_vbox.pack_start(self._pb_check, False, False, 5)

        tkn_hbox = Gtk.HBox()

        tkn_hbox.pack_start(Gtk.Label('Access Token Key : '), False, False, 5)

        self._tkn_key = Gtk.Entry()
        self._tkn_key.set_placeholder_text('Input token key of Pushbullet apis')
        if pb_data.find("token").text is not None:
            self._tkn_key.set_text(pb_data.find("token").text)
        tkn_hbox.pack_start(self._tkn_key, True, True, 1)

        self._verify_btn = Gtk.Button('Verify')
        tkn_hbox.pack_start(self._verify_btn, False, True, 5)
        pb_vbox.pack_start(tkn_hbox, True, True, 5)

        channel_hbox = Gtk.HBox()

        channel_hbox.pack_start(Gtk.Label('Channels : '), False, False, 5)

        self._pb_channel = Gtk.ComboBox()
        channels = pb_data.find('channels')
        print(channels.findall('channel'))
        channel_hbox.pack_start(self._pb_channel, False, False, 5)

        pb_vbox.pack_start(channel_hbox, True, True, 5)
        pb_frame.add(pb_vbox)

        self._pb_check.connect('toggled', self._on_pb_check_toggled)
        self._tkn_key.connect('changed', self._on_token_key_changed)
        self._verify_btn.connect('clicked', self._on_verify_clicked)

        self._on_pb_check_toggled(None)

        return pb_frame

    def _create_email(self, em_data):
        em_frame = Gtk.Frame(label='E-mail')
        em_vbox = Gtk.VBox()

        self._em_check = Gtk.CheckButton(u'사용')
        self._em_check.set_active(bool(int(em_data.get('use'))))
        em_vbox.pack_start(self._em_check, False, False, 5)

        em_frame.add(em_vbox)
        return em_frame

    def _on_token_key_changed(self, entry, data=None):
        if entry.get_text() == "":
            self._verify_btn.set_sensitive(False)
        else:
            self._verify_btn.set_sensitive(True)

    def _on_pb_check_toggled(self, check, data=None):
        checked = self._pb_check.get_active()
        for widget in (self._tkn_key, self._verify_btn):
            widget.set_sensitive(checked)
        if checked and self._tkn_key.get_text() == "":
            self._verify_btn.set_sensitive(False)

    def _on_verify_clicked(self, btn):
        token = self._tkn_key.get_text()
        try:
            pb = Pushbullet(token)
        except InvalidKeyError as err:
            self._tkn_key.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_DIALOG_ERROR)
            self._verified = False
            print(type(err))
            print(err.args)
        else:
            self._tkn_key.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_APPLY)
            self._verified = True
            print(pb.devices)

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
        self._prefdlg.set_size_request(500, 300)
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
    print(DEFAULT_PREF)
    pref = Preferences(None, parent=Gtk.Window(Gtk.WindowType.TOPLEVEL))
    pref.run()
