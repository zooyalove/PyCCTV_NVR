import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
from gi.repository import GstVideo

class CropTest(Gtk.Window):
    def __init__(self):
        super(CropTest, self).__init__()
        
        self.connect('destroy', self.on_quit)
        self.create_ui()
        self.create_control()
        
    def create_ui(self):
        screen = self.get_screen()
        w = screen.get_width() - 10
        h = screen.get_height() - 65
        self.set_default_size(w, h)
        
        hbox = Gtk.HBox()
        self.add(hbox)
        
        da = Gtk.DrawingArea()
        da.set_size_request(1280, 720)
        da.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        hbox.pack_start(da, False, False, 2)
        
        vbox = Gtk.VBox()
        hbox.pack_end(vbox, True, True, 2)
        
        lblLeft = Gtk.Label("Left :")
        lblLeft.set_halign(Gtk.Align.START)
        vbox.pack_start(lblLeft, False, False, 0)
        
        adjLeft = Gtk.Adjustment(0, 0, 200, 10, 20, 0)
        adjLeft.connect('value-changed', self.on_left_changed)
        sclLeft = Gtk.HScale(adjustment=adjLeft)
        vbox.pack_start(sclLeft, False, True, 0)
        
        vbox.pack_start(Gtk.Label(""), False, False, 2)
        
        lblTop = Gtk.Label("Top :")
        lblTop.set_halign(Gtk.Align.START)
        vbox.pack_start(lblTop, False, False, 0)
        
        adjTop = Gtk.Adjustment(0, 0, 200, 10, 20, 0)
        adjTop.connect('value-changed', self.on_top_changed)
        sclTop = Gtk.HScale(adjustment=adjTop)
        vbox.pack_start(sclTop, False, True, 0)
        
        vbox.pack_start(Gtk.Label(""), False, False, 2)
        
        lblRight = Gtk.Label("Right :")
        lblRight.set_halign(Gtk.Align.START)
        vbox.pack_start(lblRight, False, False, 0)
        
        adjRight = Gtk.Adjustment(0, 0, 400, 10, 20, 0)
        adjRight.connect('value-changed', self.on_right_changed)
        sclRight = Gtk.HScale(adjustment=adjRight)
        vbox.pack_start(sclRight, False, True, 0)

        vbox.pack_start(Gtk.Label(""), False, False, 2)
        
        lblBottom = Gtk.Label("Bottom :")
        lblBottom.set_halign(Gtk.Align.START)
        vbox.pack_start(lblBottom, False, False, 0)
        
        adjBottom = Gtk.Adjustment(0, 0, 200, 10, 20, 0)
        adjBottom.connect('value-changed', self.on_bottom_changed)
        sclBottom = Gtk.HScale(adjustment=adjBottom)
        vbox.pack_start(sclBottom, False, True, 0)
        
        hbox2 = Gtk.HBox()
        vbox.pack_end(hbox2, True, False, 2)
        
        startBtn = Gtk.Button(label='Start')
        startBtn.connect('clicked', self.run)
        hbox2.pack_start(startBtn, True, True, 2)
        
        exitBtn = Gtk.Button(label='Exit')
        exitBtn.connect('clicked', self.on_quit)
        hbox2.pack_start(exitBtn, True, True, 2)
        
    def create_control(self):
        self.pipe = Gst.Pipeline.new('videocrop_test')
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        
        src = Gst.ElementFactory.make('tcpclientsrc', 'src')
        src.set_property('host', '192.168.0.79')
        src.set_property('port', 5001)
        self.pipe.add(src)
        
        depay = Gst.ElementFactory.make('gdpdepay', 'depay')
        self.pipe.add(depay)
        
        rtpdepay = Gst.ElementFactory.make('rtph264depay', 'rtpdepay')
        self.pipe.add(rtpdepay)
        
        parse = Gst.ElementFactory.make('h264parse', 'parse')
        self.pipe.add(parse)
        
        dec = Gst.ElementFactory.make('avdec_h264', 'dec')
        self.pipe.add(dec)
        
        conv = Gst.ElementFactory.make('videoconvert', 'convert')
        self.pipe.add(conv)
        
        self.crop = Gst.ElementFactory.make('videocrop', 'crop')
        self.crop.set_property('left', 0)
        self.crop.set_property('top', 0)
        self.crop.set_property('right', 0)
        self.crop.set_property('bottom', 0)
        self.pipe.add(self.crop)
        
        conv2 = Gst.ElementFactory.make('videoconvert', 'conv2')
        self.pipe.add(conv2)
        
        sink = Gst.ElementFactory.make('autovideosink', 'sink')
        sink.set_property('sync', False)
        self.pipe.add(sink)
        
        src.link(depay)
        depay.link(rtpdepay)
        rtpdepay.link(parse)
        parse.link(dec)
        dec.link(conv)
        conv.link(self.crop)
        self.crop.link(conv2)
        conv2.link(sink)

    def start(self):
        self.show_all()
        
    def run(self, widget):
        self.pipe.set_state(Gst.State.PLAYING)    
    
    def on_left_changed(self, adjustmnt):
        val = int(adjustmnt.get_value())
        self.crop.set_property('left', val)
        
    def on_top_changed(self, adjustmnt):
        val = int(adjustmnt.get_value())
        self.crop.set_property('top', val)
        
    def on_right_changed(self, adjustmnt):
        val = int(adjustmnt.get_value())
        self.crop.set_property('right', val)
        
    def on_bottom_changed(self, adjustmnt):
        val = int(adjustmnt.get_value())
        self.crop.set_property('bottom', val)
        
    def on_quit(self, widget):
        self.pipe.set_state(Gst.State.NULL)
        self.pipe.unref()
        Gtk.main_quit()
        
if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)
    
    win = CropTest()
    win.start()
    Gtk.main()
    