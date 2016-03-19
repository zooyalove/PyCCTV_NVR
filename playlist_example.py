import gi, os
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')

from gi.repository import Gst, Gtk, Gdk, GdkPixbuf
from gi.repository import GstVideo, GstPbutils

from utils import nsec2time
from urllib.request import pathname2url

import xpm_data

class VideoPlayer(Gtk.Window):
    player_title = u'PyCCTV_NVR VideoPlayer'
    def __init__(self):
        super(VideoPlayer, self).__init__(type=Gtk.WindowType.TOPLEVEL)

        self.playlist = []        
        self.play_index = -1
        self.is_playing = False
        self.is_autostart = True
        
        self.set_title(self.player_title)
        self.set_border_width(2)
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(20000, 20000, 20000))
        
        self._setupUI()
        
    def set_autostart(self, autostart=True):
        if autostart is not None and isinstance(autostart, bool):
            self.is_autostart = autostart
            
    def get_autostart(self):
        return self.is_autostart
        
    def run(self):
        self.show_all()
        
        if self.is_autostart:
            self.on_play_clicked(None)
        
    def _setupUI(self):
        hbox = Gtk.HBox()
        self.add(hbox)
        
        vbox = Gtk.VBox()
        hbox.add(vbox)
        
        sc_win = Gtk.ScrolledWindow()
        sc_win.set_size_request(230, -1)
        sc_win.set_border_width(4)
        sc_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sc_win.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        self.store = self._create_model()
        
        self.listview = Gtk.TreeView(self.store)
        self.listview.set_headers_visible(False)
        self.listview.set_activate_on_single_click(False)
        self.listview.set_can_focus(False)
        self.listview.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        self.listview.connect('row-activated', self.on_list_clicked)
        
        sc_win.add(self.listview)
        
        hbox.pack_end(sc_win, False, True, 0)
        
        self.video_frame = Gtk.DrawingArea()
        self.video_frame.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        self.video_frame.set_size_request(640, 480)
        vbox.pack_start(self.video_frame, True, True, 0)
        
        # play control
        ctrl2_hbox = Gtk.HBox()
        
        self.prev_btn = Gtk.Button()
        self.rewind_btn = Gtk.Button()
        self.play_btn = Gtk.Button()
        self.stop_btn = Gtk.Button()
        self.forward_btn = Gtk.Button()
        self.next_btn = Gtk.Button()
        
        ctrl_buttons = ((self.prev_btn, Gtk.STOCK_MEDIA_PREVIOUS, u'이전 영상 <B>', self.on_prev_clicked, ),
                        (self.rewind_btn, Gtk.STOCK_MEDIA_REWIND, u'10초전으로 <Right Arrow>', self.on_rewind_clicked),
                        (self.play_btn, Gtk.STOCK_MEDIA_PLAY, u'재생 <Spacebar>', self.on_play_clicked),
                        (self.stop_btn, Gtk.STOCK_MEDIA_STOP, u'정지 <S>', self.on_stop_clicked),
                        (self.forward_btn, Gtk.STOCK_MEDIA_FORWARD, u'10초앞으로 <Left Arrow>', self.on_forward_clicked),
                        (self.next_btn, Gtk.STOCK_MEDIA_NEXT, u'다음 영상 <N>', self.on_next_clicked))
        
        for btn, st_img, tooltip, clickfunc in ctrl_buttons:
            btn_img = Gtk.Image()
            btn_img.set_from_stock(st_img, Gtk.IconSize.BUTTON)
            btn.set_image(btn_img)
            btn.set_focus_on_click(False)
            btn.set_tooltip_text(tooltip)
            #btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_sensitive(False)
            btn.connect('clicked', clickfunc)
            ctrl2_hbox.pack_start(btn, False, False, 0)
            
        self.connect('key-release-event', self.on_key_release)
        
        vbox.pack_end(ctrl2_hbox, False, False, 2)
        
        # play time, progress
        ctrl1_hbox = Gtk.HBox(spacing=4)
        
        self.lbl_pos = Gtk.Label('00:00:00')
        self.lbl_pos.set_margin_left(4)
        self.lbl_pos.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 30000, 0))
        ctrl1_hbox.pack_start(self.lbl_pos, False, False, 0)
        
        self.progress = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress.set_draw_value(False)
        self.progress.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(65535, 30000, 0))
        ctrl1_hbox.pack_start(self.progress, True, True, 0)
        
        self.lbl_dur = Gtk.Label('00:00:00')
        self.lbl_dur.set_margin_right(4)
        self.lbl_dur.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 30000, 0))
        ctrl1_hbox.pack_start(self.lbl_dur, False, False, 0)
        
        vbox.pack_end(ctrl1_hbox, False, False, 3)
        
    def _create_model(self):
        store = Gtk.ListStore(str, str)
        return store
    
    def get_videos(self):
        playlist = ['sintel_trailer-480p.webm', 'SAM_1297.MP4', 'SAM_1298.MP4', 'SAM_1300.MP4']
        #playlist = ['ladlaceydanny_2k.wmv', 'ladumawill_2k.wmv', 'rm11026_800.mp4', 'ultra_hot_big.mp4']
        
        info = None
         
        def get_duration(fname):
            discoverer = GstPbutils.Discoverer.new(Gst.SECOND)
            return discoverer.discover_uri('file:'+fname)
        
        pixbuf_cell = Gtk.CellRendererPixbuf()
        tvc = Gtk.TreeViewColumn('Pix', pixbuf_cell)
        tvc.set_cell_data_func(pixbuf_cell, self._pixbuf_play_state)
        
        fname_cell = Gtk.CellRendererText()
        fname_cell.set_property('foreground-rgba', Gdk.RGBA(green=0.46, blue=0))
        tvc.pack_start(fname_cell, True)
        tvc.set_cell_data_func(fname_cell, self._file_name)
        
        self.listview.append_column(tvc)
        
        time_cell = Gtk.CellRendererText()
        time_cell.set_property('foreground-rgba', Gdk.RGBA(green=0.46, blue=0))
        tvc = Gtk.TreeViewColumn('time', time_cell, text=1)
        tvc.set_alignment(1.0)
        tvc.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        
        self.listview.append_column(tvc)
        
        for filename in playlist:
            full_filename = os.path.abspath(os.path.join(os.path.curdir, filename))
            print(full_filename)
            if os.path.isfile(full_filename):
                info = get_duration(pathname2url(full_filename))
                #self.playlist.append(filename)
                print(info.get_uri())
                print(info.get_duration())
                self.playlist.append([filename, info.get_duration()])
                self.store.append([filename, nsec2time(info.get_duration())])
                info = None

        self._init_controller()
        return True
        
    def _init_controller(self):
        if len(self.playlist) > 1:
            self.next_btn.set_sensitive(True)
            
        self.play_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(True)
        
        self.play_index = 0
        
    def _change_duration(self):
        self.lbl_dur.set_text(nsec2time(self.playlist[self.play_index][1]))
        
        adj = Gtk.Adjustment()
    
    def _change_title(self):
        self.set_title(self.playlist[self.play_index][0] + ' - ' + self.player_title)
        
    def _play(self):
        pass
    
    def _pause(self):
        pass
    
    def _stop(self):
        pass

    def _pixbuf_play_state(self, column, cell, model, iter, data):
        if self.play_index == -1:
            pb = None
        else:
            if self.play_index != model.get_path(iter).get_indices()[0]:
                pb = None
            else:
                if self.is_playing:
                    pb = GdkPixbuf.Pixbuf.new_from_xpm_data(xpm_data.PLAY_MINI_BTN_HOVER)
                else:
                    pb = GdkPixbuf.Pixbuf.new_from_xpm_data(xpm_data.PAUSE_MINI_BTN_HOVER)
        
        cell.set_property('pixbuf', pb)
        
    def _file_name(self, column, cell, model, iter, data):
        cell.set_property('text', model.get_value(iter, 0))
        return            
        
    def on_list_clicked(self, tree_view, path, column):
        self.play_index = int(path.get_indices()[0])
        print('list clicked - ', self.play_index)
        if len(self.playlist) < 2:
            self.prev_btn.set_sensitive(False)
            self.next_btn.set_sensitive(False)
        else:
            if self.play_index <= 0:
                self.prev_btn.set_sensitive(False)
                self.next_btn.set_sensitive(True)
            elif self.play_index == (len(self.playlist) - 1):
                self.next_btn.set_sensitive(False)
                self.prev_btn.set_sensitive(True)
            else:
                self.next_btn.set_sensitive(True)
                self.prev_btn.set_sensitive(True)
            
        if self.is_playing:
            self.on_stop_clicked(None)
        
        self.on_play_clicked(None)
        
    def on_key_release(self, widget, eventkey):
        if eventkey.keyval == Gdk.KEY_b:
            if self.prev_btn.get_sensitive():
                self.on_prev_clicked(None)

        elif eventkey.keyval == Gdk.KEY_Left:
            if self.rewind_btn.get_sensitive():
                self.on_rewind_clicked(None)

        elif eventkey.keyval == Gdk.KEY_Right:
            if self.forward_btn.get_sensitive():
                self.on_forward_clicked(None)
            
        elif eventkey.keyval == Gdk.KEY_space:
            if self.play_btn.get_sensitive():
                self.on_play_clicked(None)
            
        elif eventkey.keyval == Gdk.KEY_s:
            if self.stop_btn.get_sensitive():
                self.on_stop_clicked(None)
                
        elif eventkey.keyval == Gdk.KEY_n:
            if self.next_btn.get_sensitive():
                self.on_next_clicked(None)

        print('%s key is released' % eventkey.keyval)
        return True

    def on_prev_clicked(self, widget):
        self.play_index -= 1
        
        if self.play_index <= 0:
            self.prev_btn.set_sensitive(False)
            
        if not self.next_btn.get_sensitive():
            self.next_btn.set_sensitive(True)
            
        self._change_title()
        self.on_stop_clicked(None)
        self.on_play_clicked(None)
        
    def on_rewind_clicked(self, widget):
        pass

    def on_play_clicked(self, widget):
        if not self.is_playing:
            btn_img = Gtk.Image()
            btn_img.set_from_stock(Gtk.STOCK_MEDIA_PAUSE, Gtk.IconSize.BUTTON)
            self.play_btn.set_image(btn_img)
            
            model = self.listview.get_model()
            self._play()
        else:
            btn_img = Gtk.Image()
            btn_img.set_from_stock(Gtk.STOCK_MEDIA_PLAY, Gtk.IconSize.BUTTON)
            self.play_btn.set_image(btn_img)
            self._pause()
        
        self._change_duration()
        self._change_title()
        
        self.is_playing = not self.is_playing
        self.rewind_btn.set_sensitive(True)
        self.forward_btn.set_sensitive(True)

    def on_stop_clicked(self, widget):
        if self.is_playing:
            btn_img = Gtk.Image()
            btn_img.set_from_stock(Gtk.STOCK_MEDIA_PLAY, Gtk.IconSize.BUTTON)
            self.play_btn.set_image(btn_img)
            
            self.is_playing = False
            self._stop()        

    def on_forward_clicked(self, widget):
        pass

    def on_next_clicked(self, widget):
        self.play_index += 1
        
        if self.play_index == (len(self.playlist) - 1):
            self.next_btn.set_sensitive(False)
            
        if not self.prev_btn.get_sensitive():
            self.prev_btn.set_sensitive(True)
            
        self._change_title()
        self.on_stop_clicked(None)
        self.on_play_clicked(None)
        
    
if __name__ == '__main__':
    from gi.repository import GObject
    
    GObject.threads_init()
    Gst.init(None)
    
    vp = VideoPlayer()
    vp.connect('destroy', Gtk.main_quit)
    vp.get_videos()
    vp.run()
    Gtk.main()