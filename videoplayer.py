import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, Gtk, Gdk
from gi.repository import GdkX11, GstVideo

class VideoPlayer(Gtk.Window):
    def __init__(self, app):
        super(VideoPlayer, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        
        self.app = app
        self.set_transient_for(app)
        self.set_destroy_with_parent(True)
        self.set_modal(True)
        
        hbox = Gtk.HBox()
        self.add(hbox)
        
        vbox = Gtk.VBox()
        hbox.add(vbox)
        
        self.video_frame = Gtk.DrawingArea()
        self.video_frame.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        self.video_frame.set_size_request(640, 480)
        vbox.pack_start(self.video_frame, True, True, 0)
        
        # play control
        ctrl2_hbox = Gtk.HBox()
        ctrl2_hbox.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(20000, 20000, 20000))
        
        btn_img = Gtk.Image()
        btn_img.set_from_stock(Gtk.STOCK_MEDIA_PREVIOUS, Gtk.IconSize.BUTTON)
        self.prev_btn = Gtk.Button()
        self.prev_btn.set_image(btn_img)
        self.prev_btn.set_relief(Gtk.ReliefStyle.NONE)
        ctrl2_hbox.pack_start(self.prev_btn, False, False, 0)
        
        btn_img = Gtk.Image()
        btn_img.set_from_stock(Gtk.STOCK_MEDIA_REWIND, Gtk.IconSize.BUTTON)
        self.rewind_btn = Gtk.Button()
        self.rewind_btn.set_image(btn_img)
        self.rewind_btn.set_relief(Gtk.ReliefStyle.NONE)
        ctrl2_hbox.pack_start(self.rewind_btn, False, False, 0)
        
        btn_img = Gtk.Image()
        btn_img.set_from_stock(Gtk.STOCK_MEDIA_PLAY, Gtk.IconSize.BUTTON)
        self.play_btn = Gtk.Button()
        self.play_btn.set_image(btn_img)
        self.play_btn.set_relief(Gtk.ReliefStyle.NONE)
        ctrl2_hbox.pack_start(self.play_btn, False, False, 0)
        
        btn_img = Gtk.Image()
        btn_img.set_from_stock(Gtk.STOCK_MEDIA_STOP, Gtk.IconSize.BUTTON)
        self.stop_btn = Gtk.Button()
        self.stop_btn.set_image(btn_img)
        self.stop_btn.set_relief(Gtk.ReliefStyle.NONE)
        ctrl2_hbox.pack_start(self.stop_btn, False, False, 0)
        
        btn_img = Gtk.Image()
        btn_img.set_from_stock(Gtk.STOCK_MEDIA_FORWARD, Gtk.IconSize.BUTTON)
        self.forward_btn = Gtk.Button()
        self.forward_btn.set_image(btn_img)
        self.forward_btn.set_relief(Gtk.ReliefStyle.NONE)
        ctrl2_hbox.pack_start(self.forward_btn, False, False, 0)
        
        btn_img = Gtk.Image()
        btn_img.set_from_stock(Gtk.STOCK_MEDIA_NEXT, Gtk.IconSize.BUTTON)
        self.next_btn = Gtk.Button()
        self.next_btn.set_image(btn_img)
        self.next_btn.set_relief(Gtk.ReliefStyle.NONE)
        ctrl2_hbox.pack_start(self.next_btn, False, False, 0)
        
        vbox.pack_end(ctrl2_hbox, False, False, 2)
        
        #play time, progress
        ctrl1_hbox = Gtk.HBox(spacing=4)
        ctrl1_hbox.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(20000, 20000, 20000))
        
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
        
        sc_win = Gtk.ScrolledWindow()
        sc_win.set_size_request(200, -1)
        sc_win.set_border_width(4)
        sc_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        hbox.pack_end(sc_win, False, True, 0)
        
        self.show_all()
        
if __name__ == '__main__':
    from gi.repository import GObject
    
    GObject.threads_init()
    #Gst.init(None)
    
    vp = VideoPlayer(None)
    vp.connect('destroy', Gtk.main_quit)
    Gtk.main()