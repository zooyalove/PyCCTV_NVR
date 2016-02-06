import os
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, Gtk, Gdk, GObject, GLib
from gi.repository import GstVideo, GdkX11, GstApp

GObject.threads_init()
Gst.init(None)


class FaceDetect(object):
    def __init__(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.connect('destroy', self.on_quit)
        self.window.set_size_request(640, 360)
        
        self.da = Gtk.DrawingArea()
        self.da.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        self.window.add(self.da)
        
        self.pipe = Gst.ElementFactory.make('pipeline', 'record_test')
        tcpsrc = Gst.ElementFactory.make('tcpclientsrc', None)
        tcpsrc.set_property('host', "192.168.0.79")
        tcpsrc.set_property('port', 5001)
        gdpdepay = Gst.ElementFactory.make('gdpdepay', None)
        rtpdepay = Gst.ElementFactory.make('rtph264depay', None)
        tee = Gst.ElementFactory.make('tee', None)
        
        monitor_q = Gst.ElementFactory.make('queue', None)
        avdec = Gst.ElementFactory.make('avdec_h264', None)
        vidconv = Gst.ElementFactory.make('videoconvert', None)
        monitor_sink = Gst.ElementFactory.make('autovideosink', None)
        monitor_sink.set_property('sync', False)

        record_q = Gst.ElementFactory.make('queue', None)
        record_q.set_property('leaky', 2)
        record_sink = Gst.ElementFactory.make('appsink', None)
        record_sink.set_property('emit-signals', True)
        record_sink.connect('new-sample', self.on_new_sample_recsink)
        
        for ele in (tcpsrc, gdpdepay, rtpdepay, tee, monitor_q, avdec, vidconv, monitor_sink, record_q, record_sink):
            self.pipe.add(ele)

        tcpsrc.link(gdpdepay)
        gdpdepay.link(rtpdepay)
        rtpdepay.link(tee)
        
        monitor_q.link(avdec)
        avdec.link(vidconv)
        vidconv.link(monitor_sink)
        
        record_q.link(record_sink)
        
        t_pad = tee.get_request_pad('src_%u')
        q_pad = monitor_q.get_static_pad('sink')
        t_pad.link(q_pad)
        t_pad.unref()
        q_pad.unref()
        
        t_pad = tee.get_request_pad('src_%u')
        q_pad = record_q.get_static_pad('sink')
        t_pad.link(q_pad)
        t_pad.unref()
        q_pad.unref()
         
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message_cb)
        bus.connect("sync-message::element", self.on_sync_message_cb)
        bus.unref()
        
        """ Video Recording Element Initialize """
        self.rec_pipe = Gst.ElementFactory.make('pipeline', 'recored_pipeline')
        
        self.rec_src = Gst.ElementFactory.make('appsrc', 'rec_src')
        self.rec_pipe.add(self.rec_src)
        
        parse = Gst.ElementFactory.make('h264parse', None)
        self.rec_pipe.add(parse)
        
        mp4mux = Gst.ElementFactory.make('mp4mux', None)
        self.rec_pipe.add(mp4mux)
        
        self.filesink = Gst.ElementFactory.make('filesink', None)
        self.filesink.set_property('async', False)
        self.rec_pipe.add(self.filesink)
        
        self.rec_src.link(parse)
        parse.link(mp4mux)
        mp4mux.link(self.filesink)
        
        rec_bus = self.rec_pipe.get_bus()
        rec_bus.add_signal_watch()
        rec_bus.connect('message', self.on_rec_message_cb)
        rec_bus.unref()
        
        self.rec_timer_id = 0

        self.window.show_all()
                
        self.pipe.set_state(Gst.State.PLAYING)
        
    def on_new_sample_recsink(self, appsink):
        sample = appsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        if self.rec_src.get_state() == Gst.State.PLAYING:
            print("%" + Gst.TIME_FORMAT + " <= " % Gst.TIME_ARGS(buffer.dts))
            
            self.rec_src.set_caps(caps)
            self.rec_src.push_buffer(buffer)
            
        sample.unref()
        
        return Gst.FlowReturn.OK
    
    def start_recording(self):
        if self.rec_timer_id != 0:
            print("### Will continue recording ###")
            GLib.Source.remove(self.rec_timer_id)
            self.rec_timer_id = 0
        else:
            print("### Start recording ###")
            datetime = Gst.DateTime.new_now_local_time()
            g_datetime = datetime.to_g_date_time()
            timestamp = g_datetime.format("%F_%H:%M:%S")
            filename = timestamp + ".mp4"
            filepath = os.path.abspath(os.path.join(os.path.curdir, filename))
            self.filesink.set_property('location', filepath)
            self.filesink.set_property('async', False)
            
            GLib.free(timestamp)
            GLib.free(filename)
            GLib.free(filepath)
            g_datetime.unref()
            datetime.unref()
            
            self.start_timer()
            
            self.rec_pipe.set_state(Gst.State.PLAYING)
    
    
    def start_timer(self):
        self.rec_timer_id = GLib.timeout_add_seconds(10 * Gst.SECOND, self.stop_recording)
        
        
    def stop_recording(self):
        self.rec_src.end_of_stream()
        self.rec_timer_id = 0
        print("Recording stopped")
        return False
        
    def on_sync_message_cb(self, bus, msg):
        if msg.get_structure().get_name() == "prepare-window-handle":
            sink = msg.src
            sink.set_property('force-aspect-ratio', True)
            sink.set_window_handle(self.da.get_property('window').get_xid())
            
        
    def on_rec_message_cb(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
                
            self.rec_timer_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            self.rec_pipe.set_state(Gst.State.NULL)
            
        return True
    
            
    def on_message_cb(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.STATE_CHANGED:
            newstate = msg.parse_state_changed()[1]
            if newstate == Gst.State.PLAYING:
                self.start_recording()
                
        elif t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Error : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info : \n%s" % debug)
            
            Gtk.main_quit()
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Warning : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info : \n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("Got EOS")
            Gtk.main_quit()
        pass
                    
    def on_quit(self, window):
        self.rec_src.end_of_stream()
        self.pipe.set_state(Gst.State.NULL)
        self.pipe.unref()
        Gtk.main_quit()
    
if __name__ == "__main__":
    f = FaceDetect()
    Gtk.main()
