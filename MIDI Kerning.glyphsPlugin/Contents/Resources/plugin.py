import objc

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
        newMenuItem = NSMenuItem(self.name, self.updateKerning_)
        Glyphs.menu[GLYPH_MENU].append(newMenuItem)

    
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


    def updateKerning_(self, _):
        font = Glyphs.font
        if len(font.selectedLayers) != 1:
            return

        active_glyph, next_glyph = self.getAdjacentGlyphs()
        curr_kerning = font.kerningForPair(font.selectedFontMaster.id, active_glyph.name, next_glyph.name)

        Glyphs.showNotification('Test', active_glyph.name + next_glyph.name + str(curr_kerning)) # .string, .id, .name
