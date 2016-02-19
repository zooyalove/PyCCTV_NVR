import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, Gtk, Gdk
from gi.repository import GstVideo

class CropTest(Gtk.Window):
    def __init__(self):
        super(CropTest, self).__init__()
        
        self.connect('destroy', self.on_quit)
        
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
        sclLeft = Gtk.HScale(adjustment=adjLeft)
        vbox.pack_start(sclLeft, False, True, 0)
        
        vbox.pack_start(Gtk.Label(""), False, False, 2)
        
        lblTop = Gtk.Label("Top :")
        lblTop.set_halign(Gtk.Align.START)
        vbox.pack_start(lblTop, False, False, 0)
        
        adjTop = Gtk.Adjustment(0, 0, 200, 10, 20, 0)
        sclTop = Gtk.HScale(adjustment=adjTop)
        vbox.pack_start(sclTop, False, True, 0)
        
        vbox.pack_start(Gtk.Label(""), False, False, 2)
        
        lblRight = Gtk.Label("Right :")
        lblRight.set_halign(Gtk.Align.START)
        vbox.pack_start(lblRight, False, False, 0)
        
        adjRight = Gtk.Adjustment(0, 0, 200, 10, 20, 0)
        sclRight = Gtk.HScale(adjustment=adjRight)
        vbox.pack_start(sclRight, False, True, 0)

        vbox.pack_start(Gtk.Label(""), False, False, 2)
        
        lblBottom = Gtk.Label("Bottom :")
        lblBottom.set_halign(Gtk.Align.START)
        vbox.pack_start(lblBottom, False, False, 0)
        
        adjBottom = Gtk.Adjustment(0, 0, 200, 10, 20, 0)
        sclBottom = Gtk.HScale(adjustment=adjBottom)
        vbox.pack_start(sclBottom, False, True, 0)
        
        
        pipe = Gst.Pipeline.new('videocrop_test')
        bus = pipe.get_bus()
        bus.add_signal_watch()
        
        src = Gst.ElementFactory.make('tcpclientsrc', 'src')
        src.set_property('host', '192.168.0.79')
        src.set_property('port', 5001)
        pipe.add(src)
        
        depay = Gst.ElementFactory.make('gdpdepay', 'depay')
        pipe.add(depay)
        
        rtpdepay = Gst.ElementFactory.make('rtph264depay', 'rtpdepay')
        pipe.add(rtpdepay)
        
        parse = Gst.ElementFactory.make('h264parse', 'parse')
        pipe.add(parse)
        
        dec = Gst.ElementFactory.make('avdec_h264', 'dec')
        pipe.add(dec)
        
        convert = Gst.ElementFactory.make('videoconvert', 'convert')
        pipe.add(convert)
        
        sink = Gst.ElementFactory.make('autovideosink', 'sink')
        pipe.add(sink)
        
        self.show_all()
        
        
    def on_quit(self, window):
        Gtk.main_quit()
        
if __name__ == "__main__":
    GObject.threads_init()
    Gst.init(None)
    
    win = CropTest()
    Gtk.main()
    