import os, time, threading
import platform

import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, Gtk, Gdk, GObject, GLib
from gi.repository import GstVideo, GdkX11, GstApp

os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp/"

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
        
        self.pipe = Gst.Pipeline.new('record_test')
        tcpsrc = Gst.ElementFactory.make('tcpclientsrc', 'tcpsrc')
        tcpsrc.set_property('host', "192.168.0.79")
        #tcpsrc.set_property('host', "songsul.iptime.org")
        tcpsrc.set_property('port', 5001)
        self.pipe.add(tcpsrc)
        
        #q = Gst.ElementFactory.make('queue', None)
        #self.pipe.add(q)
        
        gdpdepay = Gst.ElementFactory.make('gdpdepay', None)
        self.pipe.add(gdpdepay)
        rtpdepay = Gst.ElementFactory.make('rtph264depay', None)
        self.pipe.add(rtpdepay)
        parser = Gst.ElementFactory.make('h264parse', None)
        self.pipe.add(parser)
        tee = Gst.ElementFactory.make('tee', None)
        self.pipe.add(tee)
        
        monitor_q = Gst.ElementFactory.make('queue', None)
        self.pipe.add(monitor_q)
        avdec = Gst.ElementFactory.make('avdec_h264', None)
        self.pipe.add(avdec)
        vidconv = Gst.ElementFactory.make('videoconvert', None)
        self.pipe.add(vidconv)
        #monitor_sink = Gst.ElementFactory.make('autovideosink', None)
        monitor_sink = Gst.ElementFactory.make('xvimagesink', None)
        monitor_sink.set_property('sync', False)
        self.pipe.add(monitor_sink)

        record_q = Gst.ElementFactory.make('queue', None)
        #record_q.set_property('leaky', 2)
        record_q.set_property('max-size-time', 30 * Gst.SECOND)
        self.pipe.add(record_q)
        caps = Gst.caps_from_string("video/x-h264, alignment=au, stream-format=avc")
        capsfilter = Gst.ElementFactory.make('capsfilter', None)
        self.pipe.add(capsfilter)
        capsfilter.set_property('caps', caps)
        record_sink = Gst.ElementFactory.make('appsink', None)
        record_sink.set_property('emit-signals', True)
        record_sink.connect('new-sample', self.on_new_sample_recsink)
        self.pipe.add(record_sink)
        
        tcpsrc.link(gdpdepay)
        gdpdepay.link(rtpdepay)
        rtpdepay.link(parser)
        parser.link(tee)
        
        monitor_q.link(avdec)
        avdec.link(vidconv)
        vidconv.link(monitor_sink)
        
        record_q.link(capsfilter)
        capsfilter.link(record_sink)
        
        t_pad = tee.get_request_pad('src_%u')
        q_pad = monitor_q.get_static_pad('sink')
        t_pad.link(q_pad)
        
        t_pad = tee.get_request_pad('src_%u')
        q_pad = record_q.get_static_pad('sink')
        t_pad.link(q_pad)
         
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message_cb)
        bus.connect("sync-message::element", self.on_sync_message_cb)
        bus.unref()
        
        """ Video Recording Element Initialize """
        self.rec_pipe = Gst.ElementFactory.make('pipeline', 'record_pipeline')
        
        self.rec_src = Gst.ElementFactory.make('appsrc', 'rec_src')
        self.rec_src.set_property('do-timestamp', True)
        self.rec_pipe.add(self.rec_src)
        
        mp4mux = Gst.ElementFactory.make('mp4mux', None)
        #mp4mux.set_property('streamable', True)
        self.rec_pipe.add(mp4mux)
        
        self.filesink = Gst.ElementFactory.make('filesink', None)
        self.filesink.set_property('async', False)
        self.rec_pipe.add(self.filesink)
        
        self.rec_src.link(mp4mux)
        mp4mux.link(self.filesink)
        
        rec_bus = self.rec_pipe.get_bus()
        rec_bus.add_signal_watch()
        rec_bus.connect('message', self.on_rec_message_cb)
        rec_bus.unref()
        
        self.rec_timer_id = 0
        self.rec_lock = threading.Lock()

        self.window.show_all()

        Gst.debug_bin_to_dot_file(self.pipe, Gst.DebugGraphDetails.ALL, 'app_recording_test')
        Gst.debug_bin_to_dot_file(self.rec_pipe, Gst.DebugGraphDetails.ALL, 'record_pipe_test')
                
        self.pipe.set_state(Gst.State.PLAYING)
        print("레코딩 시작")
        self.start_recording()
        
        
    def on_new_sample_recsink(self, appsink):
        sample = appsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        self.rec_lock.acquire()
        print("레코딩 샘플 Lock 시작")
        nowstate = self.rec_pipe.get_state(Gst.CLOCK_TIME_NONE)[1] 
        if nowstate == Gst.State.PLAYING:
            self.rec_src.set_caps(caps)
            self.rec_src.push_buffer(buffer)
         
        self.rec_lock.release()
        print("레코딩 샘플 Lock 끝")
        
        return Gst.FlowReturn.OK
    
    def start_recording(self):
        print("레코딩 Lock 시작")
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
            print("Filename : %s" % filename)
            print("Current directory's name : %s" % os.path.curdir)
            filepath = os.path.abspath(os.path.join(os.path.curdir, filename))
            print("Totally filepath is ' %s '" % filepath)
            self.filesink.set_property('location', filepath)
            self.filesink.set_property('async', False)
            
            self.rec_pipe.set_state(Gst.State.PLAYING)
    
            self.start_timer()
            
        print("레코딩 Lock 끝")

    
    def start_timer(self):
        self.rec_lock.acquire()
        print("타이머 Lock 시작")
        self.rec_timer_id = GLib.timeout_add_seconds(30, self.stop_recording)
        print(self.rec_timer_id)
        self.rec_lock.release()
        print("타이머 Lock 끝")
        
        
    def stop_recording(self):
        self.rec_lock.acquire()
        print("레코딩 중지 Lock 시작")
        self.rec_src.end_of_stream()
        print("Recording stopped")
        self.rec_lock.release()
        print("레코딩 중지 Lock 끝")
        
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
            print("Record pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
              
            GLib.Source.remove(self.rec_timer_id)
            self.rec_timer_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Record pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("End-Of-Stream received.")
            self.rec_timer_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            self.start_recording()
            
        return True
    
            
    def on_message_cb(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Main pipeline -> Error : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info : \n%s" % debug)
            
            self.on_quit(None)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Main pipeline -> Warning : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info : \n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("Got EOS")
            self.on_quit(None)
        pass
                    
    def on_quit(self, window):
        self.rec_src.end_of_stream()
        self.pipe.set_state(Gst.State.NULL)
        self.pipe.unref()
        Gtk.main_quit()
    
if __name__ == "__main__":
    f = FaceDetect()
    Gtk.main()
