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

        self.cached_kernings = {}
        self.glyphs = [None, None]
        Glyphs.addCallback(self.updateAdjacentGlyphs_, UPDATEINTERFACE)

        self.thread = Thread(target=self.listenThread)
        self.thread.daemon = True
        self.thread.start()

        # Glyphs.showNotification('Test', str(sys.path[::-1]))

        print('Started')
    
    
    def listenThread(self):
        sign = lambda n: 1 if n > 0 else (-1 if n < 0 else 0)
        with mido.open_input(self.device_name) as inport:
            for msg in inport:
                if msg.type != 'control_change' or msg.control != self.cc:
                    continue
                self.updateKerning_(sign(64 - msg.value))

    
    def updateAdjacentGlyphs_(self, _, direction='right'):
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
        if curr_tab is None:
            return
        active_layer = curr_tab.layers[curr_tab.layersCursor]
        adjacent_layer = curr_tab.layers[curr_tab.layersCursor + increment]
        
        # Return final result
        if direction == 'right':
            self.glyphs = active_layer.parent.name, adjacent_layer.parent.name
        else:
            self.glyphs = adjacent_layer.parent.name, active_layer.parent.name
        return


    def updateKerning_(self, diff):
        start = time.time()

        start1 = time.time()
        if len(Glyphs.font.selectedLayers) != 1:
            return
        end1 = time.time()

        start3 = time.time()
        cache_key = '_'.join(self.glyphs)
        cached = self.cached_kernings.get(cache_key, None)
        now = time.time()
        if cached is None or cached['ts'] - now > 2:
            current_kerning = Glyphs.font.kerningForPair(Glyphs.font.selectedFontMaster.id, *self.glyphs)
            if current_kerning is None:
                current_kerning = 0
        else:
            current_kerning = cached['val']
        new_kerning = current_kerning + diff
        self.cached_kernings[cache_key] = {'ts': now, 'val': new_kerning}
        end3 = time.time()
        start4 = time.time()
        # active_glyph.beginUndo()
        Glyphs.font.setKerningForPair(Glyphs.font.selectedFontMaster.id, *self.glyphs, new_kerning)
        # active_glyph.endUndo()
        end4 = time.time()

        end = time.time()

        Glyphs.showNotification('Test', f'{end1-start1}, {end3-start3}, {end4-start4}, {end-start}') # .string, .id, .name
