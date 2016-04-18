'''
Created on 2016. 4. 18.

@author: Administrator
'''
import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk


class Splashscreen(Gtk.Window):
    '''
    classdocs
    '''


    def __init__(self, splimage):
        '''
        Constructor
        '''
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_skip_pager_hint(False)
        self.set_skip_taskbar_hint(False)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)
        
        if isinstance(splimage, str):
            splimage = Gtk.Image.new_from_file(os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources', splimage)))
        elif isinstance(splimage, Gtk.Image):
            pass 
        
        vbox = Gtk.VBox()
        vbox.add(splimage)
        self.add(vbox)
        
        self.show_all()
        
        
if __name__ == '__main__':
    win = Splashscreen('purun_nvr.png')
    win.connect('delete-event', Gtk.main_quit)
    win.show_all()
    Gtk.main()