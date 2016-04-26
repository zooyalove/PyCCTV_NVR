'''
Created on 2016. 4. 18.

@author: zia

'''
import os
import gi
gi.require_version('Gtk', '3.0')

import xml.etree.ElementTree as ET

from gi.repository import Gtk
from gi.repository import Pango
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
            <token verified="0"></token>
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

        video_and_pic = self._create_video_and_picture([data.find("video"), data.find("snapshot")])
        notebook.append_page(video_and_pic, Gtk.Label(u'영상 및 사진'))

        social = self._create_social(data.find("service_provider"))
        notebook.append_page(social, Gtk.Label(u'소셜 서비스'))

        notebook.show_all()
        return notebook

    def _create_top_label(self, label):
        vbox = Gtk.VBox()
        vbox.set_border_width(10)
        top_label = Gtk.Label(label)
        fontdesc = Pango.FontDescription()
        fontdesc.set_weight(Pango.Weight.BOLD)
        top_label.modify_font(fontdesc)
        top_label.set_halign(Gtk.Align.START)
        vbox.pack_start(top_label, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep, False, True, 5)
        return vbox

    def _create_general(self, general_data):
        vbox = self._create_top_label(u'일반')

        grid = Gtk.Grid()
        grid.set_border_width(4)
        grid.set_row_spacing(10)
        grid.set_column_spacing(5)

        lbl = Gtk.Label('영상 보유기한 : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 0, 1, 1)

        self._gnl_period = Gtk
        lbl = Gtk.Label('기본 저장폴더 : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 1, 1, 1)

        self._gnl_folder = Gtk.Entry(text=(general_data.find('save_dir').text or ""))
        self._gnl_folder.set_hexpand(True)
        grid.attach(self._gnl_folder, 1, 1, 1, 1)

        folder_img = Gtk.Image()
        folder_img.set_from_stock(Gtk.STOCK_DIRECTORY, Gtk.IconSize.BUTTON)
        folder_btn = Gtk.Button()
        folder_btn.set_image(folder_img)
        folder_btn.set_tooltip_text()
        grid.attach(folder_btn, 2, 1, 1, 1)

        vbox.pack_start(grid, True, True, 5)
        return vbox

    def _create_video_and_picture(self, video_and_pic):
        vbox = self._create_top_label(u'영상 및 사진')
        return vbox

    def _create_social(self, svc_data):
        vbox = self._create_top_label(u'소셜 서비스')

        pb_frame = self._create_pushbullet(svc_data.find("pushbullet"))
        vbox.pack_start(pb_frame, True, True, 10)

        em_frame = self._create_email(svc_data.find("email"))
        vbox.pack_start(em_frame, True, True, 10)
        return vbox

    def _create_pushbullet(self, pb_data):
        pb_frame = Gtk.Frame(label='Pushbullet')
        pb_vbox = Gtk.VBox()
        pb_vbox.set_border_width(4)

        self._pb_check = Gtk.CheckButton(u'사용')
        self._pb_check.set_active(bool(int(pb_data.get('use'))))
        pb_vbox.pack_start(self._pb_check, False, False, 5)

        tkn_hbox = Gtk.HBox()

        tkn_hbox.pack_start(Gtk.Label('Access Token Key : '), False, False, 5)

        self._tkn_key = Gtk.Entry()
        self._tkn_key.set_placeholder_text('Input token key of Pushbullet apis')
        self._tkn_key.set_text(pb_data.find("token").text or "")
        tkn_hbox.pack_start(self._tkn_key, True, True, 1)

        self._verify_btn = Gtk.Button('Verify')
        tkn_hbox.pack_start(self._verify_btn, False, True, 5)
        pb_vbox.pack_start(tkn_hbox, True, True, 5)

        channel_hbox = Gtk.HBox()

        channel_hbox.pack_start(Gtk.Label('Channels : '), False, False, 5)

        self._channel_store = Gtk.ListStore(int, str, str)
        self._pb_channel = Gtk.ComboBox.new_with_model(self._channel_store)
        renderer_text = Gtk.CellRendererText()
        self._pb_channel.pack_start(renderer_text, True)
        self._pb_channel.add_attribute(renderer_text, 'text', 1)

        channels = pb_data.find('channels')
        row_count = -1
        for channel in channels.findall('channel'):
            row_count = row_count + 1
            self._channel_store.append([int(channel.get('use', 0)), channel.text, channel.get('tag')])
            if int(channel.get('use', 0)) == 1:
                self._pb_channel.set_active(row_count)
        del row_count

        channel_hbox.pack_start(self._pb_channel, False, False, 5)

        pb_vbox.pack_start(channel_hbox, True, True, 5)
        pb_frame.add(pb_vbox)

        self._pb_check.connect('toggled', self._on_pb_check_toggled)
        self._tkn_key.connect('changed', self._on_token_key_changed)
        self._verify_btn.connect('clicked', self._on_verify_clicked)
        self._pb_channel.connect('changed', self._on_channel_combo_changed)

        self._on_pb_check_toggled(None)

        return pb_frame

    def _create_email(self, em_data):
        em_frame = Gtk.Frame(label='E-mail')
        em_vbox = Gtk.VBox()
        em_vbox.set_border_width(4)

        self._em_check = Gtk.CheckButton(u'사용')
        self._em_check.set_active(bool(int(em_data.get('use'))))
        em_vbox.pack_start(self._em_check, False, False, 5)

        grid = Gtk.Grid()
        grid.set_border_width(4)
        grid.set_row_spacing(10)
        grid.set_column_spacing(5)

        lbl = Gtk.Label('SMTP Server Address : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 0, 1, 1)
        srvaddr_entry = Gtk.Entry(text=em_data.find('smtpsrv_addr').text)
        srvaddr_entry.set_editable(False)
        srvaddr_entry.set_sensitive(False)
        grid.attach(srvaddr_entry, 1, 0, 2, 1)

        lbl = Gtk.Label('SMTP Server Port : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 1, 1, 1)
        srvport_entry = Gtk.Entry(text=em_data.find('smtpsrv_port').text)
        srvport_entry.set_editable(False)
        srvport_entry.set_sensitive(False)
        grid.attach(srvport_entry, 1, 1, 2, 1)

        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 2, 3, 1)

        lbl = Gtk.Label('Username(GMAIL) : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 3, 1, 1)
        self._username_entry = Gtk.Entry(text=(em_data.find('username').text or ""))
        grid.attach(self._username_entry, 1, 3, 2, 1)

        lbl = Gtk.Label('User Password : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 4, 1, 1)
        self._userpass_entry = Gtk.Entry(text=(em_data.find('userpass').text or ""))
        self._userpass_entry.set_visibility(False)
        grid.attach(self._userpass_entry, 1, 4, 1, 1)
        self._userpass_check = Gtk.CheckButton(label=u'비밀번호 보이기')
        self._userpass_check.set_hexpand(True)
        self._userpass_check.connect('toggled', lambda c: self._userpass_entry.set_visibility(c.get_active()))
        grid.attach(self._userpass_check, 2, 4, 1, 1)

        lbl = Gtk.Label('From(E-mail) : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 5, 1, 1)
        self._em_from_entry = Gtk.Entry(text=(em_data.find('from').text or ""))
        self._em_from_entry.set_editable(False)
        grid.attach(self._em_from_entry, 1, 5, 2, 1)

        lbl = Gtk.Label('To(E-mail) : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 6, 1, 1)
        self._em_to_entry = Gtk.Entry(text=(em_data.find('to').text or ""))
        self._em_to_entry.set_tooltip_text('콤마스페이스(, ) 구분자로 여러명에게 보낼 수 있습니다')
        grid.attach(self._em_to_entry, 1, 6, 2, 1)

        lbl = Gtk.Label('Subject : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 7, 1, 1)
        self._em_subject_entry = Gtk.Entry(text=(em_data.find('subject').text or ""))
        grid.attach(self._em_subject_entry, 1, 7, 2, 1)

        lbl = Gtk.Label('Msg Body : ')
        lbl.set_halign(Gtk.Align.START)
        grid.attach(lbl, 0, 8, 1, 1)
        self._em_body_entry = Gtk.Entry(text=(em_data.find('msg_body').text or ""))
        grid.attach(self._em_body_entry, 1, 8, 2, 1)

        em_vbox.pack_start(grid, True, True, 5)
        em_frame.add(em_vbox)

        self._em_check.connect('toggled', self._on_em_check_toggled)

        return em_frame

    def _on_pb_check_toggled(self, check):
        checked = self._pb_check.get_active()
        for widget in (self._tkn_key, self._verify_btn, self._pb_channel):
            widget.set_sensitive(checked)
        if checked and self._tkn_key.get_text() == "":
            self._verify_btn.set_sensitive(False)

    def _on_token_key_changed(self, entry):
        if entry.get_text() == "":
            self._verify_btn.set_sensitive(False)
        else:
            self._verify_btn.set_sensitive(True)
        self._verified = False

    def _on_verify_clicked(self, btn):
        token = self._tkn_key.get_text()
        try:
            pb = Pushbullet(token)
        except InvalidKeyError as err:
            self._tkn_key.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_DIALOG_ERROR)
            self._verified = False
            self._channel_store.clear()
            print(type(err))
            print(err.args)
        else:
            self._tkn_key.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_APPLY)
            self._verified = True
            self._channel_store.clear()
            print(pb.channels)
            for channel in pb.channels:
                self._channel_store.append([0, channel.name, channel.channel_tag])
            self._pb_channel.set_active(0)

    def _on_channel_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            use, name, tag = model[tree_iter][:3]
            print(use, name, tag)

    def _on_em_check_toggled(self, check):
        checked = check.get_active()
        for widget in (self._username_entry, self._userpass_entry, self._em_from_entry,
                       self._em_to_entry, self._em_subject_entry, self._em_body_entry):
            widget.set_sensitive(checked)

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
                                   Gtk.DialogFlags.MODAL,
                                   (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self._prefdlg.set_position(Gtk.WindowPosition.CENTER)
        self._prefdlg.set_size_request(500, -1)
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
