'''
Created on 2016. 4. 18.

@author: zia

'''
import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

DEFAULT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_PREF = '''<preferences>
    <general>
        
    </general>
    <>
    <>
</preferences>'''

 
class Preferences(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self._prefdlg = None