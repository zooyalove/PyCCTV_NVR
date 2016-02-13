import os, threading
#from datetime import datetime

import gi
from datetime import datetime
gi.require_version('Gst', '1.0')

from gi.repository import Gst, Gtk, GObject, Gdk, GLib
from gi.repository import GstApp

class Record(object):
    def __init__(self):
        #self.win = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        #self.win.connect('destroy', self.quit)
        
        def on_pad_added(demuxer, pad, data):
            parse_pad = data.get_static_pad('sink')
            if pad.can_link(parse_pad):
                pad.link(parse_pad)
            #parse_pad.unref()
            
        self.pipe = Gst.ElementFactory.make('pipeline', 'record')
        
        filesrc = Gst.ElementFactory.make('filesrc', 'filesrc')
        filesrc.set_property('location', 'sintel_trailer-480p.webm')
        self.pipe.add(filesrc)
        demux = Gst.ElementFactory.make('decodebin', 'demux')
        self.pipe.add(demux)
        vidconv = Gst.ElementFactory.make('videoconvert', 'vidconv')
        self.pipe.add(vidconv)
        tee = Gst.ElementFactory.make('tee', 'tee')
        self.pipe.add(tee)
        
        filesrc.link(demux)
        vidconv.link(tee)
        
        demux.connect('pad-added', on_pad_added, vidconv)
                
        vid_q = Gst.ElementFactory.make('queue', None)
        self.pipe.add(vid_q)
        vidsink = Gst.ElementFactory.make('autovideosink', None)
        vidsink.set_property('sync', True)
        self.pipe.add(vidsink)
        
        vid_q.link(vidsink)
        
        temp_pad = tee.get_request_pad('src_%u')
        q_pad = vid_q.get_static_pad('sink')
        temp_pad.link(q_pad)
        
        rec_q = Gst.ElementFactory.make('queue', None)
        self.pipe.add(rec_q)
        scale = Gst.ElementFactory.make('videoscale', None)
        scale.set_property('method', 3)
        self.pipe.add(scale)
        caps = Gst.caps_from_string("video/x-raw, width=420, height=240")
        filter1 = Gst.ElementFactory.make('capsfilter', 'filter1')
        filter1.set_property('caps', caps) 
        self.pipe.add(filter1)
        rate = Gst.ElementFactory.make('videorate', None)
        self.pipe.add(rate)
        caps = Gst.caps_from_string("video/x-raw, framerate=(fraction)15/1")
        filter2 = Gst.ElementFactory.make('capsfilter', 'filter2')
        filter2.set_property('caps', caps)
        self.pipe.add(filter2)
        vidconv2 = Gst.ElementFactory.make('videoconvert', 'vidconv2')
        self.pipe.add(vidconv2)
        recsink = Gst.ElementFactory.make('appsink', 'recsink')
        recsink.set_property('emit-signals', True)
        recsink.connect('new-sample', self.on_new_sample)
        self.pipe.add(recsink)
        
        rec_q.link(scale)
        scale.link(filter1)
        filter1.link(rate)
        rate.link(filter2)
        filter2.link(vidconv2)
        vidconv2.link(recsink)
        
        temp_pad = tee.get_request_pad('src_%u')
        q_pad = rec_q.get_static_pad('sink')
        temp_pad.link(q_pad)
        
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message_cb, None)
        
        self.rec_pipe = Gst.ElementFactory.make('pipeline', 'rec_pipe')
        recbus = self.rec_pipe.get_bus()
        recbus.connect('message', self.on_rec_message_cb, None)
        
        self.appsrc = Gst.ElementFactory.make('appsrc', 'recsrc')
        self.rec_pipe.add(self.appsrc)
        self.enc = Gst.ElementFactory.make('x264enc', 'enc')
        self.rec_pipe.add(self.enc)
        mp4mux = Gst.ElementFactory.make('mp4mux', 'mp4mux')
        self.rec_pipe.add(mp4mux)
        self.filesink = Gst.ElementFactory.make('filesink', 'filesink')
        self.rec_pipe.add(self.filesink)
        
        self.appsrc.link(self.enc)
        mp4mux.link(self.filesink)
        
        mux_pad = mp4mux.get_request_pad('video_%u')
        enc_pad = self.enc.get_static_pad('src')
        enc_pad.link(mux_pad)
        
        self.rec_thread_id = 0
        
    def start_recording(self):
        #Gdk.threads_enter()
        print("Record start - start")
        if self.rec_thread_id != 0:
            GLib.Source.remove(self.rec_thread_id)
            self.rec_thread_id = 0
        else:
            self.enc.set_property('tune', 'zerolatency')
            dtime = Gst.DateTime.new_now_local_time()
            g_datetime = dtime.to_g_date_time()
            timestamp = g_datetime.format("%F_%H:%M:%S")
            filename = timestamp + ".mp4"
            print("Filename : %s" % filename)
            self.filesink.set_property('location', filename)
            self.filesink.set_property('async', False)
            
            print("Rec Pipeline state : ")
            print(self.rec_pipe.get_state(Gst.CLOCK_TIME_NONE)[1])
            if self.rec_pipe.get_state(Gst.CLOCK_TIME_NONE)[1] == Gst.State.NULL: 
                self.rec_pipe.set_state(Gst.State.PLAYING)
                print(datetime.now())
                self.start_timer()
            
        #Gdk.threads_leave()
        print("Record start - end")

    def start_timer(self):
        Gdk.threads_enter()
        print("Timer start : %s" % datetime.now())
        self.rec_thread_id = Gdk.threads_add_timeout_seconds(GLib.PRIORITY_DEFAULT, 30, self.stop_recording)
        Gdk.threads_leave()
        print("Timer end")
        
    def stop_recording(self):
        Gdk.threads_enter()
        print("Record stop - start")
        self.appsrc.end_of_stream()
        print(datetime.now())
        Gdk.threads_leave()
        print("Record stop - end")
    
    def on_new_sample(self, recsink):
        sample = recsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        Gdk.threads_enter()
        state = self.appsrc.get_state(Gst.CLOCK_TIME_NONE)[1]
        print(state)
        if state == Gst.State.PLAYING:
            self.appsrc.set_caps(caps)
            self.appsrc.push_buffer(buffer)
            
        Gdk.threads_leave()
    
    def on_rec_message_cb(self, bus, msg, data):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Record pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
              
            GLib.Source.remove(self.rec_timer_id)
            self.rec_thread_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Record pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("End-Of-Stream received")
            print(datetime.now())
            self.rec_thread_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            self.start_recording()
    
    def on_message_cb(self, bus, msg, data):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Main pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
            if self.rec_thread_id != 0:  
                GLib.Source.remove(self.rec_thread_id)
                self.rec_thread_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            self.pipe.set_state(Gst.State.NULL)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Main pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            self.rec_thread_id = 0
            self.rec_pipe.set_state(Gst.State.NULL)
            self.pipe.set_state(Gst.State.NULL)
    
    
    def quit(self):
        Gtk.main_quit()
        
    def run(self):
        #self.win.show_all()
        self.pipe.set_state(Gst.State.PLAYING)
        self.start_recording()
        Gtk.main()

if __name__ == "__main__":
    GObject.threads_init()
    
    Gdk.threads_init()
    Gst.init(None)

    w = Record()
    w.run()
    