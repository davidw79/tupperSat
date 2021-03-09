# -*- coding: utf-8 -*-
"""

Spyder Editor

Created on Tue Feb 28 2020 12:26:54 

@author: Bill

This is an initial code to extract the pressure and temperature data.

"""
import smbus 
import time 
from tuppersat.sensor import SensorBase
import logging
LOG = logging.getLogger(__name__)
      
class PressureSensor(SensorBase):
    """
    This class is designed to extract the raw pressure/temperature & coefficient data and calculate 
    the actual pressure and temperature using from them. 
    """
    def __init__(self, addr):
        self._bus = None
        self._addr =addr
        super().__init__(log=LOG)  
        
    def setup(self):
        self._bus=smbus.SMBus(1)
    
    def calibration_constants(self):
        """
        This method extracts the calibration constants used to calcuate the temperature and pressure
        """
        C1bytes = self._bus.read_i2c_block_data(self._addr, 0xA2) 
        C_1 = (C1bytes[0] << 8) + C1bytes[1] 

        C2bytes = self._bus.read_i2c_block_data(self._addr, 0xA4) 
        C_2 = (C2bytes[0] << 8) + C2bytes[1]

        C3bytes = self._bus.read_i2c_block_data(self._addr, 0xA6) 
        C_3 = (C3bytes[0] << 8) + C3bytes[1]

        C4bytes = self._bus.read_i2c_block_data(self._addr, 0xA8) 
        C_4 = (C4bytes[0] << 8) + C4bytes[1]

        C5bytes = self._bus.read_i2c_block_data(self._addr, 0xAA) 
        C_5 = (C5bytes[0] << 8) + C5bytes[1]

        C6bytes = self._bus.read_i2c_block_data(self._addr, 0xAC) 
        C_6 = (C6bytes[0] << 8) + C6bytes[1]
        return C_1, C_2, C_3, C_4, C_5, C_6
     

    def digital_temp_data(self):  # This function will give the initial digital format for temperature data
        """
        Extracts the digital temperature value as bytes
        """        
        self._bus.write_byte(self._addr, 0x58) 
        time.sleep(0.05) 
        tempadcbytes = self._bus.read_i2c_block_data(self._addr, 0x00) 
        time.sleep(0.05) 
        self.tempadc=tempadcbytes[0]*65536.0+tempadcbytes[1]*256.0+tempadcbytes[2] 

    def digital_pressure_data(self): # This function will give the initial digital format for pressure data
        """
        Extracts the digital pressure value as bytes
        """
        self._bus.write_byte(self._addr,0x48) 
        time.sleep(0.05) 
        presadcbytes=self._bus.read_i2c_block_data(self._addr,0x00) 
        time.sleep(0.05) 
        self.presadc=(presadcbytes[0]<<16)+(presadcbytes[1]<<8)+presadcbytes[2]

    def get_temperature(self): # This function implements the equations needed to convert the digital data to degrees celsius
        """
        calulates and returns the actual temperature 
        using the temp and calibration constants from above
        """
        C_1, C_2, C_3, C_4, C_5, C_6=self.calibration_constants()
        self.digital_temp_data()        
        dT = self.tempadc-(C_5*(2**8))
        temperature=(2000+(dT*(C_6/(2**23))))/100
        return temperature, dT
        
    def get_pressure(self): # This function implements the equations needed to convert the digital data into mbars    
        """
        calulates and returns the actual pressure 
        using the pressure and calibration constants from above
        """
        self.digital_pressure_data()
        C_1, C_2, C_3, C_4, C_5, C_6=self.calibration_constants()
        temperature, dT=self.get_temperature()
        OFF = ((C_2 * (2**16)) + ((C_4 * dT)/2**7))
        SENS = (C_1 * (2**15)) + ((C_3 * dT)/(2**8))
        pressure=(((self.presadc*(SENS/(2**21)))-OFF)/(2**15))/100
        return pressure, temperature     
    
    def read(self):
        """
        The loop function, which calls the get pressure method and returns temperature and pressure
        """
        try:
            pressure, temperature=self.get_pressure()
            return pressure,temperature
        except Exception:
            logging.exception("Pressure Sensor Error")
            
    