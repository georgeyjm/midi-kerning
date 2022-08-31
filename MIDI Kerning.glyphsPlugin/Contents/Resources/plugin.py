import sys
import time
import copy
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
        # Initialize MIDI device and ports
        self.device_name = 'MPK mini 3'
        self.knobs = {
            22: 'left',
            23: 'right',
        }
        assert self.device_name in mido.get_input_names()

        # Initialize kerning data
        self.glyphs = (None, None, None) # The active glyph along with two adjacent glyphs
        self.data = {
            'left': {
                'direction': 'left',
                'listening': False,
                'change': 0,
                'cached': {},
            }
        }
        self.data['right'] = copy.copy(self.data['left'])
        self.data['right'].update({'direction': 'right'})
        
        Glyphs.addCallback(self.updateAdjacentGlyphs_, UPDATEINTERFACE)

        self.thread = Thread(target=self.listenThread)
        self.thread.daemon = True
        self.thread.start()
    
    
    def listenThread(self):
        sign = lambda n: 1 if n > 0 else (-1 if n < 0 else 0)
        with mido.open_input(self.device_name) as inport:
            for msg in inport:
                if msg.type != 'control_change' or msg.control not in self.knobs:
                    continue
                data = self.data[self.knobs[msg.control]]
                data['change'] += sign(64 - msg.value)
                if not data['listening']:
                    data['listening'] = True
                    update_thread = Thread(target=self.updateThread_, args=(data,))
                    update_thread.daemon = True
                    update_thread.start()
    
    
    def updateThread_(self, data):
        time.sleep(0.02)
        change = data['change']
        data['change'] = 0
        data['listening'] = False
        self.updateKerning__(change, data)
        return

    
    def updateAdjacentGlyphs_(self, _):
        '''Returns either the previous and current glyphs,
        or the current and next glyphs, depending on the direction.'''

        # Method 1
        # View = Glyphs.currentDocument.windowController().activeEditViewController().graphicView()
        # active_layer = View.activeLayer()
        # adjacent_layer = View.cachedGlyphAtIndex_(View.activeIndex() + increment)
    
        # Method 2
        curr_tab = Glyphs.font.currentTab
        if curr_tab is None:
            return
        cursor = curr_tab.layersCursor

        self.glyphs[1] = curr_tab.layers[cursor].parent.name
        if cursor == 0:
            self.glyphs[0] = None
        else:
            self.glyphs[0] = curr_tab.layers[cursor - 1].parent.name
        if cursor == len(curr_tab.layers) - 1:
            self.glyphs[2] = None
        else:
            self.glyphs[2] = curr_tab.layers[cursor + 1].parent.name
        
        # print(self.glyphs)
        return


    def updateKerning__(self, diff, data, round_to=1):
        if data['direction'] == 'left':
            glyphs = self.glyphs[:2]
        else:
            glyphs = self.glyphs[1:]
        master_id = Glyphs.font.selectedFontMaster.id
        cache_key = master_id + '_' + '_'.join(glyphs)
        cached = data['cached'].get(cache_key, None)
        now = time.time()
        if cached is None or cached['ts'] - now > 2:
            current_kerning = Glyphs.font.kerningForPair(master_id, *glyphs)
            if current_kerning is None:
                current_kerning = 0
        else:
            current_kerning = cached['val']
        new_kerning = current_kerning + diff
        if round_to != 1:
            # TODO: optimize rounding mechanism
            new_kerning = round_to * round(new_kerning / round_to)
        data['cached'][cache_key] = {'ts': now, 'val': new_kerning}

        Glyphs.font.setKerningForPair(master_id, *glyphs, new_kerning)
