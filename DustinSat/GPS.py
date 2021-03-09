# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 11:34:15 2020
@author: david
"""
import serial
from tuppersat.sensor import SensorBase
import logging
LOG = logging.getLogger(__name__)

class GPS(SensorBase):
    def __init__(self, path):
        self.path=path
        """
        Variables that are required are redefined as None
        """
        self.lat=None
        self.lon=None
        self.hzdil=None
        self.alt=None
        super().__init__()
        
    def setup(self):
        """
        The setup function open the serial port for the U-Blox7 GPS dongle
        """
        try:
            self.ser = serial.Serial(self.path)
        except Exception:
            logging.exception("Serial Error")
                
    def convert(self, LatLon):
        """
        Converts dd:mm:ss.sss to dd.ddddd
        """
        degrees=int(LatLon)//100.00
        minutes=LatLon-100*degrees
        decdegrees=degrees+minutes/60
        return decdegrees
        
    def parseGGA(self, sentence):
        """ The GGA string is split into the various variables
         and the necessary ones are then processed and returned"""
        nmeaID, time, lat, latd, lon,lond, gpsQual, satNum, hzdil, alt, altu, geosep,geosepu, agegps, refstat=sentence.split(',')
        try:
            if lat=="":
                lat=self.lat
            else:
                """
                latitude data is converted to float and sent to the convert()
                """
                if latd=="N":
                    self.lat=self.convert(float(lat))
                else:
                    """
                    If the latitude is 'S', the latitude will be prefixed with '-'
                    """
                    self.lat=self.convert(float(lat))*-1
            if lon=="":
                lon=self.lon
            else:
                """
                longitude data is converted to float and sent to the convert()
                """
                if lond=="E":
                    self.lon=self.convert(float(lon))
                else:
                    """
                    If the latitude is 'W', the latitude will be prefixed with '-'
                    """
                    self.lon=self.convert(float(lon))*-1
            
            if hzdil=="":
                """
                If there is no data available, it falls back to the preset value from __init__(), 
                or to the last known value. This occurs for all four variables.
                """
                hzdil=self.hzdil
            else:
                self.hzdil=float(hzdil)
            
            if alt=="":
                self.alt=self.alt
            else:
                self.alt=float(alt)
                       
        except Exception:
            logging.exception("Exception at parseGGA()")
            pass
    
    def readGPS(self):
        """
        Reads the lines of data from the GPS module, 
        and sends any containing GGA to the parseGGA() method
        """
        lines=self.ser.readline().decode()
        if 'GGA' in lines:
            self.parseGGA(lines)
                             
        
    def read(self):
        """
        This is the loop function. It continually calls for data from the readGPS() 
        method and return the relevant data
        """
        self.readGPS()
        return (self.lat,self.lon,self.hzdil,self.alt)
        
                
    def teardown(self):
        """
        The teardown function closes the serial port 
        """
        try:
            self.ser.close()
        except Exception:
            logging.exception("Serial Disconnection Error")