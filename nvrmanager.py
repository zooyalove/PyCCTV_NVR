import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, Gtk, Gdk

"""
@param app: Root class -> Purun NVR
"""
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
            self.player.add(camera.get_bin().bin)
            
        camera.set_popup_menu(self.on_popup_menu, camera_name)
            
        
    def on_popup_menu(self, widget, evt, data):
        if evt.type == Gdk.EventType.BUTTON_RELEASE and evt.button == 3:
            print(widget.get_parent().get_parent())
            print(data)
            m = Gtk.Menu()
            title = Gtk.MenuItem(data.upper())
            title.set_sensitive(False)
            m.append(title)
            
            m.append(Gtk.SeparatorMenuItem())
            
            m2 = Gtk.Menu()
            day_view = Gtk.MenuItem('일자별 보기')
            day_view.connect('activated', self.on_dayview_activated, data)
            m2.append(day_view)
            
            time_view = Gtk.MenuItem('시간대별 보기')
            time_view.connect('activated', self.on_timeview_activated, data)
            m2.append(time_view)
            
            video_menu = Gtk.MenuItem('영상')
            video_menu.set_submenu(m2)
            m.append(video_menu)
            
            img_view = Gtk.MenuItem('촬영된 사진보기')
            img_view.connect('activated', self.on_imgview_activate, data)
            m.append(img_view)
            
            m.show_all()
            
            m.attach_to_widget(widget)
            m.popup(None, None, None, None, evt.button, evt.time)
            
            return True
        
        return False
    
    def player_configure(self):    
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        
        def sync_msg_handler(bus, msg):
            if msg.get_structure().get_name() == "prepare-window-handle":
                sink = msg.src
                sink_name = sink.get_name()[:sink.get_name().find('_')]
                print("Sink name : %s" % sink_name)
                self.cameras[sink_name].video_widget.set_sink(sink)
                
        self.bus.connect('sync-message::element', sync_msg_handler)

    def on_dayview_activated(self, widget, data):
        pass
    
    def on_timeview_activated(self, widget, data):
        pass
    
    def on_imgview_activated(self, widget, data):
        pass
    
    def on_message(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            name = msg.src.get_path_string()
            err, debug = msg.parse_error()
            print("Main pipeline -> Error received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
            self.app.quit(None)
            
        elif t == Gst.MessageType.WARNING:
            name = msg.src.get_path_string()
            err, debug = msg.parse_warning()
            print("Main pipeline -> Warning received : from element %s : %s ." % (name, err.message))
            if debug is not None:
                print("Additional debug info:\n%s" % debug)
            
        elif t == Gst.MessageType.EOS:
            print("Main pipeline : End-Of-Stream received")
            
            self.app.quit(None)
            
        elif t == Gst.MessageType.ELEMENT:
            if self.app.config['MOTION']:
                s = msg.get_structure()
                if s.has_name("motion"):
                    el = msg.src
                    deviceID = el.get_name().split('_')[0]
                    
                    if s.has_field("motion_begin"):
                        indices = s.get_string('motion_cells_indices')
                        print("Motion detected in area(s) : %s" % indices)
                        self.cameras[deviceID].start_recording()
                    elif s.has_field("motion_finished"):
                        print("Motion end")
                        self.cameras[deviceID].motion_stop_recording()
    
       
    def start(self):
        self.player.set_state(Gst.State.PLAYING)
        
    def stop(self):
        for cam in self.cameras.keys():
            if self.cameras[cam].get_bin() is not None:
                self.cameras[cam].get_bin().stop()
        
        self.bus.unref()
        self.player.set_state(Gst.State.NULL)
        self.player.unref()
