import gi
gi.require_version('Gst', '1.0')

from gi.repository import GObject, Gst, Gtk, Gdk, GLib
from gi.repository import GstVideo, GstApp

GObject.threads_init()
Gst.init(None)

FileBin = {'recsrc':None,
           'filebin':None,
           'filesink':None,
           'rec_mutex':GLib.Mutex(),
           'timer_id':0}

SnapshotBin = {'snapshotbin':None,
               'snapshotsrc':None,
               'smtpsink':None,
               'filesink':None,
               'enc':None}

MotionBin = {'motionbin':None,
             'motionsink':None}

MainPipeline = {'pipeline':None,
                'src':None,
                'tee':None,
                'motion_bin':MotionBin}

RecBin = {'recbin':None,
          'recsink':None}

App = {'loop':None,
       'main_pipeline':MainPipeline,
       'snapshot_bin':SnapshotBin,
       'rec_bin':RecBin,
       'file_bin':FileBin,
       'want_snapshot':False,
       'snapshot_mutex':GLib.Mutex()}


def send_snapshot(app):
    dt = GLib.DateTime.new_local()
    timestamp = dt.format("%F %H:%M:%S")
    filename = "snapshot-" + timestamp + ".jpg"
    filepath = "snapshot_location" + filename
    
    app['snapshot_mutex'].lock()
    
    if app['snapshot_bin']['snapshotbin'] is not None:
        app['snapshot_bin']['snapshotbin'].set_state(Gst.State.NULL)
        app['snapshot_bin']['snapshotbin'].unref()
        app['snapshot_bin']['snapshotbin'] = None
        
    create_snapshot_bin(app['snapshot_bin'])
    app['snapshot_bin']['filesink'].set_property('location', filepath)
    app['snapshot_bin']['filesink'].set_property('async', False)
    
    timestamp = filename = filepath = None
    dt.unref()
    
    app['snapshot_bin']['snapshotbin'].set_state(Gst.State.PLAYING)
    app['want_snapshot'] = True
    app['snapshot_mutex'].unlock()
    
    
def create_snapshot_bin(snapshot_bin):
    snapshot_bin['snapshotbin'] = Gst.ElementFactory.make('pipeline', 'snapshotbin')
    snapshot_bin['snapshotsrc'] = Gst.ElementFactory.make('appsrc', None)
    snapshot_bin['enc'] = Gst.ElementFactory.make('jpegenc', None)
    snapshot_bin['filesink'] = Gst.ElementFactory.make('filesink', 'filesink')
    tee = Gst.ElementFactory.make('tee', None)
    
    if not snapshot_bin['snapshotbin'] or not snapshot_bin['snapshotsrc'] or not snapshot_bin['enc'] \
        or not tee or not snapshot_bin['filesink'] :
        print("Failed to create elements")
        
    for ele in (snapshot_bin['snapshotsrc'], snapshot_bin['enc'], tee, snapshot_bin['filesink']):
        snapshot_bin['snapshotbin'].add(ele)
        
    snapshot_bin['snapshotsrc'].link(snapshot_bin['enc'])
    snapshot_bin['enc'].link(tee)
    
    srcpad = tee.get_request_pad('src_%u')
    sinkpad = snapshot_bin['filesink'].get_static_pad('sink')
    srcpad.link(sinkpad)
    srcpad.unref()
    sinkpad.unref()
    
    bus = snapshot_bin['snapshotbin'].get_bus()
    bus.add_signal_watch()
    bus.connect('message', snapshot_message_cb, snapshot_bin)
    bus.unref()


""" SnapshotBin Callback """    
def snapshot_message_cb(bus, msg, data):
    snapshot_bin = data
    t = msg.type
    
    if t == Gst.MessageType.ERROR:
        name = msg.src.get_path_string()
        err, debug = msg.parse_error()
        print("ERROR: from element %s: %s" %(name, err.message))
        if debug is not None:
            print("Additional debug info:\n%s" % debug)
            
        snapshot_bin['snapshotbin'].set_state(Gst.State.NULL)
        GLib.free(err)
        GLib.free(debug)
        GLib.free(name)
        
    elif t == Gst.MessageType.WARNING:
        name = msg.src.get_path_string()
        err, debug = msg.parse_warning()
        print("ERROR: from element %s: %s" %(name, err.message))
        if debug is not None:
            print("Additional debug info:\n%s" % debug)
            
        GLib.free(err)
        GLib.free(debug)
        GLib.free(name)
        
    elif t == Gst.MessageType.EOS:
        snapshot_bin['snapshotbin'].set_state(Gst.State.NULL)
        snapshot_bin['snapshotbin'].unref()
        snapshot_bin['snapshotbin'] = None
        
    else :
        pass
    
    return True


def create_file_bin(file_bin):
    file_bin['filebin'] = Gst.ElementFactory.make('pipeline', 'filebin')
    file_bin['recsrc'] = Gst.ElementFactory.make('appsrc', None)
    parse = Gst.ElementFactory.make('h264parse', None)
    mux = Gst.ElementFactory.make('mp4mux', None)
    file_bin['filesink'] = Gst.ElementFactory.make('filesink', None)
    
    if not file_bin['filebin'] or not file_bin['recsrc'] or not parse or not mux or not file_bin['filesink']:
        print("Failed to create elements")
        
    file_bin['filesink'].set_property('async', False)
    
    for ele in (file_bin['recsrc'], parse, mux, file_bin['filesink']):
        file_bin['filebin'].add(ele)
        
    file_bin['recsrc'].link(parse)
    parse.link(mux)
    mux.link(file_bin['filesink'])
    
    bus = file_bin['filebin'].get_bus()
    bus.add_signal_watch()
    bus.connect('message', file_message_cb, file_bin)
    bus.unref()
    
""" FileBin Callback """
def file_message_cb(bus, msg, data):
    file_bin = data
    t = msg.type
    
    if t == Gst.MessageType.ERROR:
        name = msg.src.get_path_string()
        err, debug = msg.parse_error()
        print("ERROR: from element %s: %s" %(name, err.message))
        if debug is not None:
            print("Additional debug info:\n%s" % debug)
            
        file_bin['rec_mutex'].lock()
        GLib.source_remove(file_bin['timer_id'])
        file_bin['timer_id'] = 0
        file_bin['filebin'].set_state(Gst.State.NULL)
        file_bin['rec_mutex'].unlock()
        GLib.free(err)
        GLib.free(debug)
        GLib.free(name)
        
    elif t == Gst.MessageType.WARNING:
        name = msg.src.get_path_string()
        err, debug = msg.parse_error()
        print("ERROR: from element %s: %s" %(name, err.message))
        if debug is not None:
            print("Additional debug info:\n%s" % debug)
            
        GLib.free(err)
        GLib.free(debug)
        GLib.free(name)
        
    elif t == Gst.MessageType.EOS:
        file_bin['rec_mutex'].lock()
        file_bin['filebin'].set_state(Gst.State.NULL)
        file_bin['rec_mutex'].unlock()
        
    else:
        pass
    
    return True

    