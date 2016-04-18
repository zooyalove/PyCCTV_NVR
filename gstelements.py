import os
import time
from datetime import datetime

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')

from gi.repository import GObject, Gst, Gdk, GLib, GstApp
from pushbullet import Pushbullet

class Pipeline(GObject.GObject):
    def __init__(self, app, name):
        self.app = app
        self.pipe = Gst.ElementFactory.make('pipeline', name)

        self.bus = self.pipe.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message_cb)
    
    def add(self, el):
        self.pipe.add(el)

    def play(self):
        self.pipe.set_state(Gst.State.PLAYING)
        
    def stop(self):
        self.pipe.set_state(Gst.State.NULL)
        
    def get_state(self):
        return self.pipe.get_state(Gst.CLOCK_TIME_NONE)[1]
    
    def unref(self):
        self.bus.unref()
        self.pipe.unref()
        
        return GObject.GObject.unref(self)

    def on_message_cb(self, bus, msg, data=None):
        pass


class AlertPipeline(Pipeline):
    def __init__(self, app, name):
        super(AlertPipeline, self).__init__(app, name+'_snd_pipe')
        
        sndsrc = Gst.ElementFactory.make('filesrc', None)
        sndsrc.set_property('location', os.path.join(self.app.RESOURCE_PATH, 'alert.wav'))
        self.add(sndsrc)
        
        wavparse = Gst.ElementFactory.make('wavparse', None)
        self.add(wavparse)
        
        aconv = Gst.ElementFactory.make('audioconvert', None)
        self.add(aconv)
        
        asink = Gst.ElementFactory.make('autoaudiosink', None)
        self.add(asink)
        
        sndsrc.link(wavparse)
        wavparse.link(aconv)
        aconv.link(asink)

class VideoPipeline(Pipeline):
    def __init__(self, app, name):
        super(VideoPipeline, self).__init__(app, name+'_vid_pipe')
        
        self.appsrc = Gst.ElementFactory.make('appsrc', name+'_vidsrc')
        self.add(self.appsrc)
        
        self.vidsink = Gst.ElementFactory.make('autovideosink', name+'_vidsink')
        self.vidsink.set_property('sync', False)
        self.add(self.vidsink)
        
        self.appsrc.link(self.vidsink)
        
        self.play()
        
        
class SnapshotPipeline(Pipeline):
    def __init__(self, app, name):
        super(SnapshotPipeline, self).__init__(app, name+'_snap_pipe')
        self.file_source = ""
        self.name = name
        self.pb = app.pb
        
        self.appsrc = Gst.ElementFactory.make('appsrc', name+'_snapsrc')
        self.add(self.appsrc)
        
        jpegenc = Gst.ElementFactory.make('jpegenc', name+'_jpegenc')
        self.add(jpegenc)
        
        self.filesink = Gst.ElementFactory.make('filesink', name+'_jpgfilesink')
        self.add(self.filesink)
        
        self.appsrc.link(jpegenc)
        jpegenc.link(self.filesink)
        
    def send_snapshot(self):
        time.sleep(1.5) # 얼굴이나 형체등을 알기위해서 잠시 쉬었다가 파이프라인 시작
        dtime = Gst.DateTime.new_now_local_time()
        g_datetime = dtime.to_g_date_time()
        timestamp = g_datetime.format("%F_%H%M%S")
        timestamp = timestamp.replace("-", "")
        filename = self.app.config['SNAPSHOT_PREFIX'] + self.name + '_' + timestamp + ".jpg"
        self.file_source = os.path.join(self.app.config['SNAPSHOT_PATH'], filename)
        print("Filename : %s" % filename)
        
        self.filesink.set_property('location', self.file_source)
        self.filesink.set_property('async', False)
        
        self.play()
        
        
    def on_message_cb(self, bus, msg, data):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Snapshot pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
              
            self.stop()
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
            self.stop()
            
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
    __gsignals__ = {
            'rec-started' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_BOOLEAN,)),
            'rec-stopped' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_BOOLEAN,))
        }
    
    def __init__(self, app, name):
        super(FilePipeline, self).__init__(app, name+'_rec_pipe')
        
        self.name = name        
        self.rec_thread_id = 0
        
        self.appsrc = Gst.ElementFactory.make('appsrc', name+'_recsrc')
        self.add(self.appsrc)
        self.rec_parse = Gst.ElementFactory.make('h264parse', name+'_rec_parse')
        self.add(self.rec_parse)
        mp4mux = Gst.ElementFactory.make('mp4mux', name+'_mp4mux')
        self.add(mp4mux)
        self.filesink = Gst.ElementFactory.make('filesink', name+'_recfilesink')
        self.add(self.filesink)
        
        self.appsrc.link(self.rec_parse)
        recp_pad = self.rec_parse.get_static_pad('src')
        recp_pad.link(mp4mux.get_request_pad('video_%u'))
        mp4mux.link(self.filesink)
        
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
            filename = self.name + '_' + timestamp + ".mp4"
            print("Filename : %s" % filename)
            self.filesink.set_property('location', os.path.join(self.app.config['VIDEO_PATH'], filename))
            self.filesink.set_property('async', False)
            
            print("Rec Pipeline state : ")
            print(self.get_state())
            if self.get_state() == Gst.State.NULL: 
                self.play()
                print(datetime.now())
                self.emit('rec-started', True)
                
                if not self.app.config['Motion']:
                    self.start_timer(self.app.config['Timeout'])
            
        print("Record start - end")

    def start_timer(self, timeout):
        Gdk.threads_enter()
        print("Timer start : %s" % datetime.now())
        self.rec_thread_id = GLib.timeout_add_seconds(timeout, self.stop_recording)
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
            self.stop()
            self.emit('rec-stopped', False)
            
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
            self.stop()
            self.emit('rec-stopped', False)
            
            if not self.app.config['Motion']:
                self.start_recording()

    def do_rec_started(self, bStart):
        print("Recording started")
        
    def do_rec_stopped(self, bStop):
        print("Recording stopped")

GObject.type_register(FilePipeline)


class Bin(GObject.GObject):
    def __init__(self, app, name):
        super(Bin, self).__init__()
        self.app = app
        self.bin = Gst.ElementFactory.make('bin', name)
        
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message_cb)
        
    def add(self, el):
        self.bin.add(el)
        
    def add_pad(self, ghostpad):
        ghostpad.set_active(True)
        self.bin.add_pad(ghostpad)
        
    def on_message_cb(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("%s -> Error received : from element %s : %s ." % (self.__class__.__name__, name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
              
            self.pipe.set_state(Gst.State.NULL)
            self.file_source = ""
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("%s -> Warning received : from element %s : %s ." % (self.__class__.__name__, name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("%s -> End-Of-Stream received." % self.__class__.__name__)
        

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
    def __init__(self, name):
        super(VideoBin, self).__init__(None, name+'_video_bin')
        
        self.is_motion_start = False
        self.motion_detect_time = 0.0
        
        vid_q = Gst.ElementFactory.make('queue', None)
        self.add(vid_q)
        
        dec = Gst.ElementFactory.make('avdec_h264', None)
        self.add(dec)
        
        conv = Gst.ElementFactory.make('videoconvert', None)
        self.add(conv)
        
        vidsink = Gst.ElementFactory.make('appsink', None)
        vidsink.set_property('emit-signals', True)
        vidsink.set_property('async', False)
        vidsink.connect('new-sample', self.on_new_sample)
        self.add(vidsink)
        
        vid_q.link(dec)
        dec.link(conv)
        conv.link(vidsink)
        
        g_pad = Gst.GhostPad.new('sink', vid_q.get_static_pad('sink'))
        self.add_pad(g_pad)
        
    def on_new_sample(self, vidsink):
        sample = vidsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        Gdk.threads_enter()
        viewsrc = self.app.view.appsrc
        
        viewsrc.set_caps(caps)
        viewsrc.push_buffer(buffer)
        
        if self.app.app.config['Motion']:
            sshotsrc = self.app.snapshot.appsrc
            state = sshotsrc.get_state(Gst.CLOCK_TIME_NONE)[1]
            if state == Gst.State.PLAYING:
                if not self.is_motion_start:
                    self.is_motion_start = not self.is_motion_start
                    self.motion_detect_time = time.time()
                else:
                    after_detect_time = time.time()
                    if after_detect_time - self.motion_detect_time >= 1.5: 
                        sshotsrc.set_caps(caps)
                        sshotsrc.push_buffer(buffer)
                        sshotsrc.end_of_stream()
                    
                        self.is_motion_start = not self.is_motion_start
                        self.motion_detect_time = 0.0
                    
            
        Gdk.threads_leave()
        
        return Gst.FlowReturn.OK
        

class RecordBin(Bin):
    def __init__(self, app, name):
        super(RecordBin, self).__init__(app, name+'_rec_bin')
        
        rec_q = Gst.ElementFactory.make('queue', None)
        self.add(rec_q)
        
        dec = Gst.ElementFactory.make('avdec_h264', None)
        self.add(dec)
        
        rate = Gst.ElementFactory.make('videorate', None)
        self.add(rate)
        filter1 = Gst.ElementFactory.make('capsfilter', None)
        filter1.set_property('caps', Gst.caps_from_string("video/x-raw, framerate=(fraction)15/1"))
        self.add(filter1)
        vidconv = Gst.ElementFactory.make('videoconvert', None)
        self.add(vidconv)
        enc = Gst.ElementFactory.make('x264enc', name+'_enc')
        enc.set_property('tune', 0x00000004)
        self.add(enc)
        filter2 = Gst.ElementFactory.make('capsfilter', None)
        filter2.set_property('caps', Gst.caps_from_string('video/x-h264, profile=baseline'))
        self.add(filter2)
        recsink = Gst.ElementFactory.make('appsink', name+'_recsink')
        recsink.set_property('emit-signals', True)
        recsink.set_property('async', False)
        recsink.connect('new-sample', self.on_new_sample)
        self.add(recsink)
        
        rec_q.link(dec)
        dec.link(rate)
        rate.link(filter1)
        filter1.link(vidconv)
        vidconv.link(enc)
        enc.link(filter2)
        filter2.link(recsink)
        
        g_pad = Gst.GhostPad.new('sink', rec_q.get_static_pad('sink'))
        self.add_pad(g_pad)

    def on_new_sample(self, recsink):
        sample = recsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        Gdk.threads_enter()
        appsrc = self.app.filerec.appsrc
        state = appsrc.get_state(Gst.CLOCK_TIME_NONE)[1]
        if state == Gst.State.PLAYING:
            appsrc.set_caps(caps)
            appsrc.push_buffer(buffer)
        Gdk.threads_leave()
        
        return Gst.FlowReturn.OK
    

class MotionBin(Bin):
    def __init__(self, app, name):
        super(MotionBin, self).__init__(app, name+'_motion_bin')
        
        motion_q = Gst.ElementFactory.make('queue', name+'_motion_q')
        self.add(motion_q)
        
        dec = Gst.ElementFactory.make('avdec_h264', None)
        self.add(dec)
        
        vidcrop = Gst.ElementFactory.make('videocrop', None)
        vidcrop.set_property('left', 120)
        vidcrop.set_property('top', 160)
        vidcrop.set_property('right', 400)
        vidcrop.set_property('bottom', 100)
        self.add(vidcrop)
        
        rate = Gst.ElementFactory.make('videorate', None)
        self.add(rate)
        filter1 = Gst.ElementFactory.make('capsfilter', None)
        filter1.set_property('caps', Gst.caps_from_string("video/x-raw, framerate=(fraction)4/1"))
        self.add(filter1)
        vidconv = Gst.ElementFactory.make('videoconvert', None)
        self.add(vidconv)
        
        motioncells = Gst.ElementFactory.make('motioncells', name+'_mtncls')
        motioncells.set_property('sensitivity', 0.5)
        self.add(motioncells)
        
        motionsink = Gst.ElementFactory.make('appsink', name+'_mtnsnk')
        self.add(motionsink)
        motionsink.set_property('emit-signals', True)
        motionsink.set_property('async', False)
        motionsink.connect('new-sample', self.on_new_sample)
        
        motion_q.link(dec)
        dec.link(vidcrop)
        vidcrop.link(rate)
        rate.link(filter1)
        filter1.link(vidconv)
        vidconv.link(motioncells)
        motioncells.link(motionsink)
        
        g_pad = Gst.GhostPad.new('sink', motion_q.get_static_pad('sink'))
        self.add_pad(g_pad)
        
    def on_new_sample(self, motionsink):
        return Gst.FlowReturn.OK
    

class WebServiceBin(Bin):
    def __init__(self, dest, name):
        super(WebServiceBin, self).__init__(None, name+'_websrv')
        
        web_q = Gst.ElementFactory.make('queue', None)
        self.add(web_q)
        
        dec = Gst.ElementFactory.make('avdec_h264', None)
        self.add(dec)
        
        scale = Gst.ElementFactory.make('videoscale', None)
        self.add(scale)
        filter1 = Gst.ElementFactory.make('capsfilter', None)
        filter1.set_property('caps', Gst.caps_from_string("video/x-raw, width=320, height=180, framerate=(fraction)5/1"))
        self.add(filter1)
        vidconv = Gst.ElementFactory.make('videoconvert', None)
        self.add(vidconv)
        vp8enc = Gst.ElementFactory.make('vp8enc', None)
        self.add(vp8enc)
        
        webmmux = Gst.ElementFactory.make('webmmux', name+'_webmmux')
        self.add(webmmux)
        
        filter2 = Gst.ElementFactory.make('capsfilter', None)
        filter2.set_property('caps', Gst.caps_from_string('video/webm'))
        self.add(filter2)
        
        srvsink = Gst.ElementFactory.make('tcpserversink', None)
        srvsink.set_property('host', dest['ip'])
        srvsink.set_property('port', dest['port'])
        self.add(srvsink)
        
        web_q.link(dec)
        dec.link(scale)
        scale.link(filter1)
        filter1.link(vidconv)
        vidconv.link(vp8enc)
        
        v_pad = vp8enc.get_static_pad('src')
        v_pad.link(webmmux.get_request_pad('video_%u'))
        
        webmmux.link(filter2)
        filter2.link(srvsink)
        
        g_pad = Gst.GhostPad.new('sink', web_q.get_static_pad('sink'))
        self.add_pad(g_pad)
        

class CameraBin(Bin):
    __gsignals__ = {
            'recording' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_BOOLEAN,))
            }
    """
    @param app: Root class -> Purun NVR
    """
    def __init__(self, source, websrv_dest, app, name):
        super(CameraBin, self).__init__(app, name+'_bin')
        
        def on_recording(filerec, bRecord):
            self.emit('recording', bRecord)
         
        self.view = VideoPipeline(app, name)
           
        self.filerec = FilePipeline(app, name)
        self.filerec.connect('rec-started', on_recording)
        self.filerec.connect('rec-stopped', on_recording)
        
        self.snapshot = SnapshotPipeline(app, name)
        
        self.alertsnd = AlertPipeline(app, name) 
        
        self.src = SourceBin(source, self, name)
        self.add(self.src.bin)
        
        tee = Gst.ElementFactory.make('tee', name+'_tee')
        self.add(tee)
        
        self.src.bin.link(tee)
        
        self.video = VideoBin(name)
        self.add(self.video.bin)
        
        vid_t_pad = tee.get_request_pad('src_%u')
        vid_t_pad.link(self.video.bin.get_static_pad('sink'))
        
        self.record = RecordBin(self, name)
        self.add(self.record.bin)
        
        rec_t_pad = tee.get_request_pad('src_%u')
        rec_t_pad.link(self.record.bin.get_static_pad('sink'))
        
        self.websrv = WebServiceBin(websrv_dest, name)
        self.add(self.websrv.bin)
        
        web_t_pad = tee.get_request_pad('src_%u')
        web_t_pad.link(self.websrv.bin.get_static_pad('sink'))
        
        if self.app.config['Motion']:
            self.motion = MotionBin(self, name)
            self.add(self.motion.bin)
            mot_t_pad = tee.get_request_pad('src_%u')
            mot_t_pad.link(self.motion.bin.get_static_pad('sink'))

    def start_recording(self):
        if self.app.config['Motion']:
            self.snapshot.send_snapshot()
            self.alertsnd.play()
            
        self.filerec.start_recording()
    
    def motion_stop_recording(self):
        self.filerec.start_timer(10)
            
    def stop(self):
        if self.filerec.get_state() == Gst.State.PLAYING:
            self.filerec.stop_recording()
            
        for pp in (self.filerec, self.view, self.snapshot, self.alertsnd):
            pp.stop()
            pp.unref()

GObject.type_register(CameraBin)