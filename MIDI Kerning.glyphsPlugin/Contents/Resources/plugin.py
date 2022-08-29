import sys
import time
from threading import Thread

# Temporary fix
sys.path.append('/Users/george/miniforge3/envs/3type/lib/python3.9/site-packages')
# Maybe?
# import pip
# pip.main(['install', 'mido', '--user'])
# pip.main(['install', 'python-rtmidi', '--user'])

import objc
import mido
from GlyphsApp import *
from GlyphsApp.plugins import *


class MidiKerning(GeneralPlugin):

    @objc.python_method
    def __file__(self):
        return __file__

    @objc.python_method
    def settings(self):
        self.name = 'MIDI Kerning'
        # self.name = Glyphs.localize({
        # 	'en': 'My General Plug-in',
        # 	'de': 'Mein allgemeines Plug-in',
        # 	'fr': 'Ma extension générale',
        # 	'es': 'Mi plugin general',
        # 	'pt': 'Meu plug-in geral',
        # 	})

    @objc.python_method
    def start(self):
        self.device_name = 'MPK mini 3'
        assert self.device_name in mido.get_input_names()
        self.cc = 23

        self.thread = Thread(target=self.listenThread)
        self.thread.daemon = True
        self.thread.start()

        # Glyphs.showNotification('Test', str(sys.path[::-1]))

        print('Started')
    
    
    def listenThread(self):
        sign = lambda n: 1 if n > 0 else (-1 if n < 0 else 0)
        with mido.open_input(self.device_name) as inport:
            for msg in inport:
                if msg.type != 'control_change':
                    continue
                if msg.control != self.cc:
                    continue
                self.updateKerning_(sign(64 - msg.value))

    
    def getAdjacentGlyphs(self, direction='right'):
        '''Returns either the previous and current glyphs,
        or the current and next glyphs, depending on the direction.'''

        assert direction in ('left', 'right')
        increment = 1 if direction == 'right' else -1

        # Method 1
        # View = Glyphs.currentDocument.windowController().activeEditViewController().graphicView()
        # active_layer = View.activeLayer()
        # adjacent_layer = View.cachedGlyphAtIndex_(View.activeIndex() + increment)
    
        # Method 2
        curr_tab = Glyphs.font.currentTab
        active_layer = curr_tab.layers[curr_tab.layersCursor]
        adjacent_layer = curr_tab.layers[curr_tab.layersCursor + increment]
        
        # Return final result
        if direction == 'right':
            return active_layer.parent, adjacent_layer.parent
        else:
            return adjacent_layer.parent, active_layer.parent


    def updateKerning_(self, diff):
        start1 = time.time()
        font = Glyphs.font
        if len(font.selectedLayers) != 1:
            return
        end1 = time.time()

        start2 = time.time()
        active_glyph, next_glyph = self.getAdjacentGlyphs()
        end2 = time.time()
        start3 = time.time()
        curr_kerning = font.kerningForPair(font.selectedFontMaster.id, active_glyph.name, next_glyph.name)
        end3 = time.time()
        if curr_kerning is None:
            curr_kerning = 0
        start4 = time.time()
        # active_glyph.beginUndo()
        font.setKerningForPair(font.selectedFontMaster.id, active_glyph.name, next_glyph.name, curr_kerning + diff)
        # active_glyph.endUndo()
        end4 = time.time()

        Glyphs.showNotification('Test', f'{end1-start1}, {end2-start2}, {end3-start3}, {end4-start4}') # .string, .id, .name
