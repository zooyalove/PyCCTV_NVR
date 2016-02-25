import os
from datetime import datetime

import gi
gi.require_version('Gst', '1.0')

from gi.repository import GObject, Gst, Gdk, GLib, GstApp
from pushbullet import Pushbullet

class Pipeline(object):
    def __init__(self, app, name):
        self.app = app
        self.pipe = Gst.ElementFactory.make('pipeline', name)
        
class SnapshotPipeline(Pipeline):
    def __init__(self, pb, app, name):
        super(SnapshotPipeline, self).__init__(app, name + '_snap_pipe')
        self.file_source = ""
        self.pb = pb
        self.name = name
        
        self.create_snapshot()
        
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message_cb, None)
        
    def create_snapshot(self):
        self.appsrc = Gst.ElementFactory.make('appsrc', self.name+'_snapsrc')
        self.pipe.add(self.appsrc)
        
        jpegenc = Gst.ElementFactory.make('jpegenc', self.name+'_jpegenc')
        self.pipe.add(jpegenc)
        
        self.filesink = Gst.ElementFactory.make('filesink', self.name+'_jpgfilesink')
        self.pipe.add(self.filesink)
        
        self.appsrc.link(jpegenc)
        jpegenc.link(self.filesink)
        
    def send_snapshot(self):
        dtime = Gst.DateTime.new_now_local_time()
        g_datetime = dtime.to_g_date_time()
        timestamp = g_datetime.format("%F_%H%M%S")
        timestamp = timestamp.replace("-", "")
        filename = self.app.app.SNAPSHOT_PREFIX + self.name + '_' + timestamp + ".jpg"
        self.file_source = filename
        print("Filename : %s" % filename)
        
        self.filesink.set_property('location', os.path.join(self.app.SNAPSHOT_PATH, filename))
        self.filesink.set_property('async', False)
        
        self.pipe.set_state(Gst.State.PLAYING)
        
        
    def on_message_cb(self, bus, msg, data):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Snapshot pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
              
            self.pipe.set_state(Gst.State.NULL)
            self.file_source = ""
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Snapshot pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("Snapshot End-Of-Stream received")
            print(datetime.now())
            print("")
            self.pipe.set_state(Gst.State.NULL)
            
            Gdk.threads_enter()
            if self.file_source != "":
                with open(self.file_source, 'rb') as pic:
                    file_data = self.pb.upload_file(pic, self.file_source)
                for key in file_data.keys():
                    print("%s in File data of value : %s" % (key , file_data[key]))
                push = self.pb.push_file(title="Motion detected", **file_data)
                print(push)
                self.file_source = ""
            Gdk.threads_leave()
            
class FilePipeline(Pipeline):
    def __init__(self, app, name):
        super(FilePipeline, self).__init__(app, name+'_rec_pipe')
        
        self.rec_thread_id = 0
        
        self.appsrc = Gst.ElementFactory.make('appsrc', name+'_recsrc')
        self.pipe.add(self.appsrc)
        self.rec_parse = Gst.ElementFactory.make('h264parse', name+'_rec_parse')
        self.pipe.add(self.rec_parse)
        mp4mux = Gst.ElementFactory.make('mp4mux', name+'_mp4mux')
        self.pipe.add(mp4mux)
        self.filesink = Gst.ElementFactory.make('filesink', name+'_recfilesink')
        self.pipe.add(self.filesink)
        
        self.appsrc.link(self.rec_parse)
        recp_pad = self.rec_parse.get_static_pad('src')
        mp4_pad = mp4mux.get_request_pad('video_%u')
        recp_pad.link(mp4_pad)
        mp4mux.link(self.filesink)
        
        recbus = self.pipe.get_bus()
        recbus.add_signal_watch()
        recbus.connect('message', self.on_message_cb, None)
        
        
    def start_recording(self):
        print("Record start - start")
        if self.rec_thread_id != 0:
            GLib.Source.remove(self.rec_thread_id)
            self.rec_thread_id = 0
        else:
            dtime = Gst.DateTime.new_now_local_time()
            g_datetime = dtime.to_g_date_time()
            timestamp = g_datetime.format("%F_%H%M%S")
            timestamp = timestamp.replace("-", "")
            filename = timestamp + ".mp4"
            print("Filename : %s" % filename)
            self.filesink.set_property('location', os.path.join(self.app.VIDEO_DIR, filename))
            self.filesink.set_property('async', False)
            
            print("Rec Pipeline state : ")
            print(self.pipe.get_state(Gst.CLOCK_TIME_NONE)[1])
            if self.pipe.get_state(Gst.CLOCK_TIME_NONE)[1] == Gst.State.NULL: 
                self.pipe.set_state(Gst.State.PLAYING)
                print(datetime.now())
                self.start_timer()
            
        print("Record start - end")

    def start_timer(self):
        Gdk.threads_enter()
        print("Timer start : %s" % datetime.now())
        self.rec_thread_id = GLib.timeout_add_seconds(30, self.stop_recording)
        print(self.rec_thread_id)
        Gdk.threads_leave()
        print("Timer end")
        
    def stop_recording(self):
        Gdk.threads_enter()
        print("Record stop - start")
        self.appsrc.end_of_stream()
        self.rec_thread_id = 0
        print(datetime.now())
        Gdk.threads_leave()
        print("Record stop - end")
    
    def on_message_cb(self, bus, msg, data):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Record pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
              
            GLib.Source.remove(self.rec_thread_id)
            self.rec_thread_id = 0
            self.pipe.set_state(Gst.State.NULL)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Record pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("Record End-Of-Stream received")
            print(datetime.now())
            print("")
            self.pipe.set_state(Gst.State.NULL)
            self.start_recording()


class Bin(object):
    def __init__(self, app, name):
        self.app = app
        self.bin = Gst.ElementFactory.make('bin', name)
        
    def add(self, el):
        self.bin.add(el)
        
    def add_pad(self, ghostpad):
        ghostpad.set_active(True)
        self.bin.add_pad(ghostpad)
        

class SourceBin(Bin):
    def __init__(self, source, app, name):
        super(SourceBin, self).__init__(app, name+'_src_bin')
        
        src = Gst.ElementFactory.make('tcpclientsrc', name+'_src')
        src.set_property('host', source['ip'])
        src.set_property('port', source['port'])
        self.add(src)
        
        depay = Gst.ElementFactory.make('gdpdepay', name+'_depay')
        self.add(depay)
        
        rtpdepay = Gst.ElementFactory.make('rtph264depay', name+'_rtpdepay')
        self.add(rtpdepay)
        
        parse = Gst.ElementFactory.make('h264parse', name+'_parse')
        self.add(parse)
        
        g_pad = Gst.GhostPad.new('src', parse.get_static_pad('src'))
        self.add_pad(g_pad)
        

class VideoBin(Bin):
    def __init__(self, app, name):
        super(VideoBin, self).__init__(app, name+'_video_bin')
        
        vid_q = Gst.ElementFactory.make('queue', None)
        self.add(vid_q)
        
        dec = Gst.ElementFactory.make('avdec_h264', None)
        self.add(dec)
        
        conv = Gst.ElementFactory.make('videoconvert', None)
        self.add(conv)
        
        vidsink = Gst.ElementFactory.make('autovideosink', None)
        vidsink.set_property('sync', True)
        self.add(vidsink)
        
        vid_q.link(dec)
        dec.link(conv)
        conv.link(vidsink)
        
        g_pad = Gst.GhostPad.new('sink', vid_q.get_static_pad('sink'))
        self.add_pad(g_pad)
        

class RecordBin(Bin):
    def __init__(self, app, name):
        super(RecordBin, self).__init__(app, name+'_rec_bin')
        
        rec_q = Gst.ElementFactory.make('queue', None)
        self.add(rec_q)
        scale = Gst.ElementFactory.make('videoscale', None)
        self.add(scale)
        caps = Gst.caps_from_string("video/x-raw, width=420, height=240")
        filter1 = Gst.ElementFactory.make('capsfilter', 'filter1')
        filter1.set_property('caps', caps) 
        self.add(filter1)
        rate = Gst.ElementFactory.make('videorate', None)
        self.add(rate)
        caps = Gst.caps_from_string("video/x-raw, framerate=(fraction)15/1")
        filter2 = Gst.ElementFactory.make('capsfilter', 'filter2')
        filter2.set_property('caps', caps)
        self.add(filter2)
        vidconv2 = Gst.ElementFactory.make('videoconvert', 'vidconv2')
        self.add(vidconv2)
        enc = Gst.ElementFactory.make('x264enc', 'enc')
        enc.set_property('tune', 0x00000004)
        self.add(enc)
        filter3 = Gst.ElementFactory.make('capsfilter', 'filter3')
        filter3.set_property('caps', Gst.caps_from_string('video/x-h264, profile=baseline'))
        self.add(filter3)
        recsink = Gst.ElementFactory.make('appsink', 'recsink')
        recsink.set_property('emit-signals', True)
        recsink.set_property('async', False)
        recsink.connect('new-sample', self.on_new_sample, self.app)
        self.add(recsink)
        
        rec_q.link(scale)
        scale.link(filter1)
        filter1.link(rate)
        rate.link(filter2)
        filter2.link(vidconv2)
        vidconv2.link(enc)
        enc.link(filter3)
        filter3.link(recsink)
        
        g_pad = Gst.GhostPad.new('sink', rec_q.get_static_pad('sink'))
        self.add_pad(g_pad)

    def on_new_sample(self, recsink, app):
        appsrc = app.filerec.appsrc
        sample = recsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        Gdk.threads_enter()
        state = appsrc.get_state(Gst.CLOCK_TIME_NONE)[1]
        if state == Gst.State.PLAYING:
            appsrc.set_caps(caps)
            appsrc.push_buffer(buffer)
        Gdk.threads_leave()
        
        return Gst.FlowReturn.OK
    

class MotionBin(Bin):
    def __init__(self, app, name):
        super(MotionBin, self).__init__(app, name + '_motion_bin')
        
        motion_q = Gst.ElementFactory.make('queue', 'motion_q')
        self.add(motion_q)
        
        scale = Gst.ElementFactory.make('videoscale', None)
        self.add(scale)
        caps = Gst.caps_from_string("video/x-raw, width=420, height=240")
        filter1 = Gst.ElementFactory.make('capsfilter', 'filter1')
        filter1.set_property('caps', caps) 
        self.add(filter1)
        rate = Gst.ElementFactory.make('videorate', None)
        self.add(rate)
        caps = Gst.caps_from_string("video/x-raw, framerate=(fraction)4/1")
        filter2 = Gst.ElementFactory.make('capsfilter', 'filter2')
        filter2.set_property('caps', caps)
        self.add(filter2)
        vidconv2 = Gst.ElementFactory.make('videoconvert', 'vidconv2')
        self.add(vidconv2)
        
        motioncells = Gst.ElementFactory.make('motioncells', 'motioncells')
        motioncells.set_property('sensitivity', 0.5)
        self.add(motioncells)
        
        motionsink = Gst.ElementFactory.make('appsink', 'motionsink')
        self.add(motionsink)
        motionsink.set_property('emit-signals', True)
        motionsink.set_property('async', False)
        motionsink.connect('new-sample', self.on_new_sample, self.app)
        
        motion_q.link(scale)
        scale.link(filter1)
        filter1.link(rate)
        rate.link(filter2)
        filter2.link(vidconv2)
        vidconv2.link(motioncells)
        motioncells.link(motionsink)
        
        g_pad = Gst.GhostPad.new('sink', motion_q.get_static_pad('sink'))
        self.add_pad(g_pad)
        
    def on_new_sample(self, motionsink, app):
        sample = motionsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        Gdk.threads_enter()
        appsrc = app.snapshot.appsrc
        state = appsrc.get_state(Gst.CLOCK_TIME_NONE)[1]
        if state == Gst.State.PLAYING:
            appsrc.set_caps(caps)
            appsrc.push_buffer(buffer)
            appsrc.end_of_stream()
            
        Gdk.threads_leave()
        
        return Gst.FlowReturn.OK
    
                
class CameraBin(Bin):
    __gsignals__ = {
            'record-start' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_NONE,)),
            'record-stop' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_NONE,))
            }
    
    def __init__(self, source, app, name):
        super(CameraBin, self).__init__(app, name + '_bin')
        
        self.filerec = FilePipeline(name)
        self.snapshot = SnapshotPipeline(app.pb, name)
        
        self.src = SourceBin(source, self, name)
        self.add(self.src)
        
        tee = Gst.ElementFactory.make('tee', 'tee')
        self.add(tee)
        
        self.video = VideoBin(self, name)
        self.add(self.video)
        
        self.record = RecordBin(self, name)
        self.add(self.record)
        
        self.motion = MotionBin(self, name)
        self.add(self.motion)
        