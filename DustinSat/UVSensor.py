from time import sleep
from smbus import SMBus
from tuppersat.sensor import SensorBase
import logging
LOG = logging.getLogger(__name__)
            
class UVSensor(SensorBase):
    
    def __init__(self, address):
        self.address = address
        self.integTimeSelect = 0x00
        self.dynamicSelect = 0x00
        self.waitTime = 0.0
        self.divisor = 0
        super().__init__(log=LOG)
        
    def setup(self):
        self.bus = SMBus(1)
        self.regUVConf = 0x00
        self.regUVA = 0x07
        self.regUVB = 0x09
        self.regUVComp1 = 0x0A
        self.regUVComp2 = 0x0B
     
        self.powerOn = 0x00
        self.powerOff = 0x01
     
        self.highDynamic = 0x08
        
        self.integTime800 = 0x40
        """
        Calibration constants from Calibration report provided to us from Robert.
        
        """
        self.A = 2.22   # UVA visible
        self.B = 1.33   # UVA infrared
        self.C = 3.66   # UVB visible
        self.D = 1.75   # UVB infrared
        
        self.UVAresp = 0.001461
        self.UVBresp = 0.002591
        """
        Conversion Factors (VEML6075 Datasheet Rev. 1.2, 23-Nov-16)
        """
        self.UVACountsPeruWcm = 0.93
        self.UVBCountsPeruWcm = 2.10
        
        self.integTimeSelect = self.integTime800  
        
        self.dynamicSelect = self.highDynamic
        self.waitTime = 1.920
        self.divisor = 16
        
    def readUV(self):
        """
        This method calculates the UVA and UVB levels detectoed by the sensors, 
        using calibration constants and other data from the setup(). 
        """
        self.bus.write_byte_data(self.address, self.regUVConf, self.integTimeSelect|self.dynamicSelect|self.powerOn)  # Write Dynamic and Integration Time Settings to Sensor
        sleep(self.waitTime)  # Wait for ADC to finish first and second conversions, discarding the first
        self.bus.write_byte_data(self.address, self.regUVConf, self.powerOff)  # Power OFF
        
        rawDataUVA = self.bus.read_word_data(self.address,self.regUVA)
        rawDataUVB = self.bus.read_word_data(self.address,self.regUVB)
        rawDataUVComp1 = self.bus.read_word_data(self.address,self.regUVComp1)  # visible noise
        rawDataUVComp2 = self.bus.read_word_data(self.address,self.regUVComp2)  # infrared noise
        
        scaledDataUVA = rawDataUVA / self.divisor
        scaledDataUVB = rawDataUVB / self.divisor
        scaledDataUVComp1 = rawDataUVComp1 / self.divisor
        scaledDataUVComp2 = rawDataUVComp2 / self.divisor
        
        compensatedUVA = scaledDataUVA - (self.A*scaledDataUVComp1) - (self.B*scaledDataUVComp2)
        compensatedUVB = scaledDataUVB - (self.C*scaledDataUVComp1) - (self.D*scaledDataUVComp2)
        """
        Do not allow negative readings which can occur in no UV light environments e.g. indoors
        """
        if compensatedUVA < 0:  
            compensatedUVA = 0
        if compensatedUVB < 0:
            compensatedUVB = 0
        """
        convert ADC counts to uWcm^2
        """
        UVAuWcm = compensatedUVA/ self.UVACountsPeruWcm  
        UVBuWcm = compensatedUVB / self.UVBCountsPeruWcm        
    
        return UVAuWcm,UVBuWcm
        
    def read(self):
        return(self.readUV())
