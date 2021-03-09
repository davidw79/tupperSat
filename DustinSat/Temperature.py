# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 10:44:23 2020

@author: david
"""
import logging
LOG = logging.getLogger(__name__)
from tuppersat.sensor import SensorBase
            
class TemperatureSensor(SensorBase):
    """
    This class takes in a port address and outputs the temperature in celcius
    """
    def __init__(self,path):
        """
        The path and temperature is defined 
        """
        self.path=path
        self.temperature=None
        super().__init__(log=LOG)        
        
    def read_temperature(self):
        """Read temperature from 1-wire file as a float in celsius."""
        with open(self.path, 'r') as file:
            lines = file.readlines()            
            line=lines[1].find('t=')
            t_string=lines[1][line+2:]
            self.temperature=(float(t_string)/(1000.0)) 

    def read(self):
        """
        The loop function, which repeatedly reads data from the 
        read_temperature() and returns the temperature to __main__.py
        """
        self.read_temperature()        
        return (self.temperature)

