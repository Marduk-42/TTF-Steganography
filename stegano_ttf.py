"""
A module for storing data in TrueType Font files.
It does not support color glyphs.

Some fonts with an enourmous capacity can be found here:
https://www.google.com/get/noto/ (Up to over 3500 glyphs and >12kB capacity (when change = 1, else higher))
And here:
http://www.unifoundry.com/unifont/index.html (Up to over 55000 glyphs and >1MB capacity (when change = 1, else higher))
"""
import xml.etree.ElementTree as ET
import os
import warnings

try:
    from fontTools.ttLib import TTFont
except:
    raise Exception("Please install fontTools (pip install fontTools) to use this module!")


supported = ['ttf']

META_DATA_LENGTH = 23 #If you need to store more than 2^23 bits (~1MB), set this higher

__all__ = ['LSB', 'supported']
__author__ = 'Maximilian Koch'
__version__ = '0.3'

class LSB:
    """Least Significant Bit(s)
       Store data in the Least Significant Bit(s) of every glyph coordinate
       :hide Hide data
       :recover Recover data
       :capacity Maximum capacity (bits)
    """
    def __init__(self, path):
        self.path = path
        self.font = TTFont(self.path)
        if self.path.split(".")[-1].lower() not in supported:
            raise Exception("Unsupported file type. For now only .ttf is supported!")
    def _bin_add(self, number, binary):
        """Replace the last n bits of a number by a given binary"""
        n = bin(number)
        n = n[:-len(binary)]+binary
        d = int(n,2)
        return d
    def _xml_read(self):
        """Read XML from self.font"""
        xml_path = '$TMPx.xml'
        while os.path.exists(xml_path):
            xml_path = '$'+xml_path
        try:
            self.font.saveXML(xml_path)
        except KeyboardInterrupt:
            os.remove(xml_path)
            return False
        tree = ET.parse(xml_path)
        try:
            os.remove(xml_path)
        except KeyboardInterrupt:
            os.remove(xml_path)
            return False
        self.tree = tree
        return tree
    def capacity(self, change=1):
        """Returns the capacity of a TTF File in bits
           :change Bits per coordinate that will be changed
        """
        return len(self.font.getGlyphSet())*change*2-META_DATA_LENGTH
    def hide(self, data, path, change=1):
        """Hide binary data
           :data Data to be hidden
           :path Path to save to
           :change Number of bits change per value
        """
        if change>=6:
            warnings.warn("Depending on the font, change will probably be detectable to the human eye!")
        if hasattr(self, 'tree'):
            tree = self.tree
        else:
            tree = self._xml_read()
        meta_data = bin(len(data))[2:].zfill(META_DATA_LENGTH)
        #Split binary data
        data = meta_data + data
        bin_dat = [data[i:i+2*change]
                   for i in range(0, len(data), 2*change)]
        
        for dat, element in zip(bin_dat, tree.iter(tag='pt')):
            x = int(element.get('x'))
            y = int(element.get('y'))
            try:        
                x = self._bin_add(x, dat[:change])
                element.set('x', str(x))
                y = self._bin_add(y, dat[change:])
                element.set('y', str(y))
            except ValueError:
                break
            
        #Write edited XML file
        temp_path = '$TMPRes.xml'
        while os.path.exists(temp_path):
            temp_path = '$' + temp_path
        try:
            tree.write(temp_path, 'iso-8859-15')
        except KeyboardInterrupt:
            os.remove(temp_path)
            return False

        #XML file to TTF
        self.font.importXML(temp_path)
        try:
            os.remove(temp_path)
        except KeyboardInterrupt:
            os.remove(temp_path)
            return False
        self.font.save(path)
        return True
    def _read(self, element, change):
        """Read binary data from single element"""
        #If coordinate is negative, bin(coord) will be -0b...
        #So the first three chars have to be cut instead of only two
        p,q = 2,2
        x = bin(int(element.get('x')))
        if x[0]=='-': p = 3
        y = bin(int(element.get('y')))
        if y[0]=='-': q = 3
        x = x[p:].zfill(change+1)
        y = y[q:].zfill(change+1)
        return x[-change:]+y[-change:]
    def recover(self, change=1):
        """Recover binary data
           :change Number of bits per coordinate to read
        """
        output = ''
        tree = self._xml_read()
        iterator = tree.iter(tag='pt')

        #Read metadata
        meta_data = ''
        while len(meta_data) < META_DATA_LENGTH:
            element = next(iterator)
            meta_data += self._read(element, change)
        
        data_length = int(meta_data[:META_DATA_LENGTH], 2)
        output = meta_data[META_DATA_LENGTH:]

        while len(output) <  data_length:
            element = next(iterator)
            output += self._read(element, change)

        return output[:data_length]
        
        data_length = float('inf')
        meta_read = 0
        while len(output)<data_length:
            try:
                element = next(iterator)
            except StopIteration:
                return output
            if not meta_read:
                if len(output)>=META_DATA_LENGTH:
                    data_length = int(output[:META_DATA_LENGTH])
                    meta_read = 1
            #If coordinate is negative, bin() will be -0b...
            #So the first three chars have to be cut instead of only two
            p,q=2,2
            x = bin(int(element.get('x')))
            if x[0]=='-':
                p = 3
            y = bin(int(element.get('y')))
            if y[0]=='-':
                q = 3
            x = x[p:].zfill(change+1)
            y = y[q:].zfill(change+1)
            output += x[-change:]
            output += y[-change:]
        return output
    def __repr__(self):
        return "LSB(path={})".format(self.path)
