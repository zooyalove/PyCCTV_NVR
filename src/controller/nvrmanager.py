import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, Gtk, Gdk

class NvrManager(Gtk.VBox):
    def __init__(self, app):
        super(NvrManager, self).__init__()
        
        self.app = app
        
        self.cameras = dict()
        self.player = Gst.ElementFactory.make('pipeline', 'CCTV_NVR')
        self.player_configure()

    def add_camera(self, camera):
        # 카메라화면 추가
        self.add(camera)
        
        camera_name = camera.get_camera_name().lower()
        print("Camera name : %s" % camera_name)
        self.cameras[camera_name] = camera
    
        if camera.get_source() is not None:
            self.player.add(camera.get_bin())
        
    def player_configure(self):    
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        
        def sync_msg_handler(bus, msg):
            if msg.get_structure().get_name() == "prepare-window-handle":
                sink = msg.src
                sink_name = sink.get_name()[:sink.get_name().find('_')]
                print("Sink name : %s" % sink_name)
                self.cameras[sink_name].video_widget.set_sink(sink)
                
        bus.connect('sync-message::element', sync_msg_handler)
        
    def on_message(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Main pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
            self.app.quit()
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Main pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("Main pipeline : End-Of-Stream received")
            
            self.app.quit()
            
       
    def start(self):
        self.player.set_state(Gst.State.PLAYING)
        
    def stop(self):
        self.player.set_state(Gst.State.NULL)