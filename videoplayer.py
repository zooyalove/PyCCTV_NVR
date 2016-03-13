import os, gi
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')

from gi.repository import Gst, Gtk, Gdk
from gi.repository import GdkX11, GstVideo, GstPbutils

class VideoPlayer(Gtk.Window):
    player_title = u'PyCCTV_NVR VideoPlayer'
    def __init__(self, app):
        super(VideoPlayer, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        
        self.app = app
        
        self.set_title(self.player_title)
        self.set_border_width(2)
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(20000, 20000, 20000))
        self.set_transient_for(app)
        self.set_destroy_with_parent(True)
        self.set_modal(True)
        
        self.setupUI()
        
    def setupUI(self):
        hbox = Gtk.HBox()
        self.add(hbox)
        
        vbox = Gtk.VBox()
        hbox.add(vbox)
        
        sc_win = Gtk.ScrolledWindow()
        sc_win.set_size_request(200, -1)
        sc_win.set_border_width(4)
        sc_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sc_win.set_shadow_type(Gtk.ShadowType.IN)
        
        self.store = self.create_model()
        self.listview = Gtk.TreeView(self.store)
        
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

        ctrl_buttons = ((self.prev_btn, Gtk.STOCK_MEDIA_PREVIOUS, u'이전 영상', self.on_prev_clicked),
                        (self.rewind_btn, Gtk.STOCK_MEDIA_REWIND, u'10초전으로', self.on_rewind_clicked),
                        (self.play_btn, Gtk.STOCK_MEDIA_PLAY, u'재생', self.on_play_clicked),
                        (self.stop_btn, Gtk.STOCK_MEDIA_STOP, u'정지', self.on_stop_clicked),
                        (self.forward_btn, Gtk.STOCK_MEDIA_FORWARD, u'10초앞으로', self.on_forward_clicked),
                        (self.next_btn, Gtk.STOCK_MEDIA_NEXT, u'다음 영상', self.on_next_clicked))
        
        for btn, st_img, tooltip, func in ctrl_buttons:
            btn_img = Gtk.Image()
            btn_img.set_from_stock(st_img, Gtk.IconSize.BUTTON)
            btn.set_image(btn_img)
            btn.set_tooltip_text(tooltip)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.connect('clicked', func)
            ctrl2_hbox.pack_start(btn, False, False, 0)
            
        
        vbox.pack_end(ctrl2_hbox, False, False, 2)
        
        # play time, progress
        ctrl1_hbox = Gtk.HBox(spacing=4)
        
        self.lbl_pos = Gtk.Label('00:00:00')
        self.lbl_pos.set_margin_left(4)
        self.lbl_pos.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 30000, 0))
        ctrl1_hbox.pack_start(self.lbl_pos, False, False, 0)
        
        self.progress = Gtk.HScale()
        self.progress.set_draw_value(False)
        self.progress.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(65535, 30000, 0))
        ctrl1_hbox.pack_start(self.progress, True, True, 0)
        
        self.lbl_dur = Gtk.Label('00:00:00')
        self.lbl_dur.set_margin_right(4)
        self.lbl_dur.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 30000, 0))
        ctrl1_hbox.pack_start(self.lbl_dur, False, False, 0)
        
        vbox.pack_end(ctrl1_hbox, False, False, 3)
        
        self.show_all()
    
    def create_model(self):
        store = Gtk.ListStore(str, str)
        return store
    
    def get_videos(self, prefix):
        def nsec2time(nsec):
            sec = nsec / Gst.SECOND
            m, s = divmod(sec, 60)
            h, m = divmod(m, s)
            
            return '%02d:%02d:%02d' % (h, m, s)
            
        vid_list = os.listdir(self.app.config['VIDEO_PATH'])
        for filename in vid_list:
            full_filename = os.path.join(self.app.config['VIDEO_PATH'], filename)
            if os.path.isfile(full_filename) and filename.startswith(prefix):
                discoverer = GstPbutils.Discoverer.new(Gst.SECOND)
                info = discoverer.discover_uri('file://'+full_filename)
                print(info.get_duration())
                self.store.append([filename, nsec2time(info.get_duration())])
    
    def change_title(self, title):
        self.set_title(title + self.player_title)
        
    def on_prev_clicked(self, widget):
        pass
        
    def on_rewind_clicked(self, widget):
        pass

    def on_play_clicked(self, widget):
        pass

    def on_stop_clicked(self, widget):
        pass

    def on_forward_clicked(self, widget):
        pass

    def on_next_clicked(self, widget):
        pass
    
    
if __name__ == '__main__':
    from gi.repository import GObject
    
    GObject.threads_init()
    #Gst.init(None)
    
    vp = VideoPlayer(None)
    vp.connect('destroy', Gtk.main_quit)
    Gtk.main()