#!/usr/bin/python3
from airborne import set_airborne
from Temperature import TemperatureSensor
from Pressure import PressureSensor
from UVSensor import UVSensor
from GPS import GPS
from tuppersat.sensor import SensorBase
from datetime import datetime as dt 
from satradio import SatRadio
import logging
import time

""" 
Setting the logging, including file name format, the type of data collected etc
"""
LOG = logging.getLogger(__name__)
"""
File directory where data is saved
"""
LOGDIR="/home/pi/MyTupperSatCode/"
filename=LOGDIR+'logs/DUSTNSAT_{now:%Y-%m-%d_%H-%M-%S}.log'.format(now=dt.now())
logging.basicConfig(filename=filename,level=logging.DEBUG,format='%(asctime)s %(name)s %(levelname)s : %(message)s')
gps_path=r'/dev/ttyACM0'
set_airborne(gps_path)

class RUN(SensorBase):
    def __init__(self):
        super().__init__(log=LOG)         
        
    def run(self):
        """Loops a function indefinitely with optional setup and teardown step."""
        self.setup()
        try:
            while True:
                self.loop()
        finally:
                self.teardown()    
    """
    starting the SatRadio at the start to ensure the path remains open    
    """ 
    def setup(self):
        """ 
        Initialising satellite radio
        """
        self.myradio=SatRadio(r"/dev/ttyAMA0", 0x53,'DUSTNSAT1') 
        self.myradio.start() 
        print("Starting SatRadio")
        
        """ 
        Starting all of the sensors
        """
        self.sensors = {'gps'  :GPS(gps_path),
        'temperature_internal' : TemperatureSensor(r'/sys/bus/w1/devices/28-0300a2796d64/w1_slave'),
        'temperature_external' : TemperatureSensor(r'/sys/bus/w1/devices/28-0517c41b75ff/w1_slave'),
        'pressure'             : PressureSensor(0x77),
        'uv_sensor'             :UVSensor(0x10)    
        }
        
        """ 
        Start timers to save data, save logs, send telemetry, send data packets  
        """
        self.sensorDataStartTime=time.perf_counter()
        self.logStartTime=time.perf_counter()        
        self.telemetryStartTime=time.perf_counter()        
        self.dataStartTime=time.perf_counter()
        
        """ 
        Opening the new files to be written. A seperate file is created for every sensor. On the tuppersat
        the sensor data is kept in the folder ~/home/pi/MyTupperSatCode/data while the logs are kept in 
        ~/home/pi/MyTupperSatCode/logs
        NB. There has to be a more eloquent way to do this.....
        """        
        self.temp1_data=open(LOGDIR+"data/TEMP1_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.temp2_data=open(LOGDIR+"data/TEMP2_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.temp3_data=open(LOGDIR+"data/TEMP3_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.pressure_data=open(LOGDIR+"data/PRESSURE_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.altitude1_data=open(LOGDIR+"data/ALTITUDE1_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.altitude2_data=open(LOGDIR+"data/ALTITUDE2_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.latitude_data=open(LOGDIR+"data/LATITUDE_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.longitude_data=open(LOGDIR+"data/LONGITUDE_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.latdilution_data=open(LOGDIR+"data/latdilution_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.uva_data=open(LOGDIR+"data/UVA_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        self.uvb_data=open(LOGDIR+"data/UVB_{now:%Y-%m-%d_%H-%M-%S}.log".format(now=dt.now()),"wb")
        
        for sensor in self.sensors:
            self.sensors[sensor].start()
            print("{} is starting....".format(sensor))
        
        
    def loop(self):
        """ 
        The inital telemetry_dict is declared so that if sensors are not outputting data, it defaults to the initial values
        """
        telemetry_dict={"hhmmss":dt.now(),"lat_dec_deg":None,"lon_dec_deg":None,"lat_dil":None,"alt":None,"temp1":None,"temp2":None,"pressure":None}
        try:
            """
            The following code retrieves the GPS/GLASNOSS location data
            """
            try:
                """
                Retrieve GPS data from sensors, if data type is None, pass. 
                This allows for the code to keep running if no data is available at the time
                """
                gpsdata=self.sensors['gps'].data
                if gpsdata==None:
                   pass
                else:
                    lat, lon, hzdil, alt=gpsdata  
                    telemetry_dict["lat_dec_deg"]=lat
                    if lat==None:
                        pass
                    else:
                        lat="{:8.5f}".format(lat)
                    telemetry_dict["lon_dec_deg"]=lon
                    if lon==None:
                        pass
                    else:
                        lon="{:9.5f}".format(lon)
                    telemetry_dict["lat_dil"]=hzdil
                    if hzdil==None:
                        pass
                    else:
                        hzdil="{:5.2f}".format(hzdil)
                    telemetry_dict["alt"]=alt
                    if alt==None:
                        pass
                    else:
                        alt="{:8.5f}".format(alt)
                   
            except Exception:
                logging.exception("Error obtaining GPS data in loop()")
            """
            The following code retrieves temp1 sensor data
            """ 
            try:
                """
                Retrieve external temperature sensor data. IF data type is None, pass. 
                This allow for the pre-defined telemetry_dict to keep values as None. 
                """
                temp1=self.sensors['temperature_internal'].data
                if temp1==None:
                    pass    
                else:
                    telemetry_dict["temp2"]=temp1
                    temp1="{:7.3f}".format(temp1)
                    
            except Exception:
                logging.exception("Error obtaining temp1 data in loop()")
            """
            The following code retrieves temp2 sensor data
            """   
            try:
                """
                Retrieve external temperature sensor data. Same as above
                """
                temp2=self.sensors['temperature_external'].data
                if temp2==None:
                   pass    
                else:
                    telemetry_dict["temp2"]=temp2 
                    temp2="{:7.3f}".format(temp2)
                    
            except Exception:
                logging.exception("Error obtaining temp2 data in loop()")
            """
            The following code retrieves the pressure data
            """   
            try:
                """
                Retrieve pressure sensor data. If data type is None pass
                """
                pressureData=self.sensors['pressure'].data
                if pressureData==None:
                    altitude2=None
                    pass                       
                else:
                    pressure, temp3=pressureData
                    if pressure==None:
                        pass
                    else:
                        """
                        Altitude data can be calculated from pressure and temperature data. 
                        It is less accurate than from the GPS module, 
                        but can be of use if the GPS module fails.
                        """
                        altitude2=((((1021/pressure)**(1.0/5.257))-1.0)*(temp3+273.15))/0.0065
                        altitude2="{:5.2f}".format(abs(altitude2))                        
                       
                        temp3="{:7.3f}".format(temp3)
                        
                        pressure="{:7.2f}".format(pressure)
                                                   
            except Exception:
                logging.exception("Error reading Pressure Sensor")
            """
            The following code retrieves the UV sensor data
            """
            try:
                """
                Retrieve UV sensor data. If data type is None pass
                """
                uvdata=self.sensors['uv_sensor'].data       
                if uvdata==None:
                    uva=None
                    uvb=None
                else:
                     uva, uvb=uvdata
                     if uva==None:
                         pass
                     else:
                         """
                         The UV sensor needs to be tested to find its upper performance limit, 
                         so we can fix the bit size that is saved.
                         """
                         uva=round(uva,4)
                         uvb=round(uvb,4)
                         
            except Exception:
                logging.exception("Error reading UV Sensor")
            """
            The code now specifies if 2 seconds or more has passed since the timer started, 
            format & save the sensor data in their respective folders
            """
            try:
                if (time.perf_counter()-self.sensorDataStartTime)>=2:
                    try:
                        """
                        Save temp1 data to 
                        """
                        logtemp1="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), temp1)
                        self.temp1_data.write(logtemp1.encode())
                        
                        """ 
                        Save temp2 data to file
                        """
                        logtemp2="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), temp2)
                        self.temp2_data.write(logtemp2.encode())
                        
                        """
                        Save altitude data to file
                        """
                        logalt1="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), alt)
                        self.altitude1_data.write(logalt1.encode())
                        
                        """
                        Save latitude data to file
                        """
                        loglat="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), lat)
                        self.latitude_data.write(loglat.encode())
                        
                        """
                        Save longitude data to file
                        """
                        loglon="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), lon)
                        self.longitude_data.write(loglon.encode())
                        
                        """
                        Save latitude dilution data to file
                        """
                        loghzdil="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), hzdil)
                        self.latdilution_data.write(loghzdil.encode())
                        
                        """
                        Save altitude (calculated from pressure sensor) data to file
                        """
                        logalt2="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), altitude2)
                        self.altitude2_data.write(logalt2.encode())
                        
                        """
                        Save temperature 3 (from pressure sensor) data to file
                        """
                        logtemp3="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), temp3)
                        self.temp3_data.write(logtemp3.encode())
                        
                        """
                        Save pressure data to file
                        """
                        logpressure="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), pressure)
                        self.pressure_data.write(logpressure.encode())
                        
                        """
                        Save uva data to file
                        """
                        loguva="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), uva)
                        self.uva_data.write(loguva.encode())
                        
                        """
                        Save uvb data to file
                        """
                        loguvb="{}|{}\n".format(dt.now().strftime("%H:%M:%S.%fZ"), uvb)
                        self.uvb_data.write(loguvb.encode())
                        
                        """
                        Reset data timer
                        """
                        self.sensorDataStartTime=time.perf_counter()
                        
                        """
                        The following code specifies if 5 seconds or more have passed 
                        since the timer was started/reset save all relevant data to the logs
                        """
                        if (time.perf_counter()-self.logStartTime)>=5:
                            try:
                                """
                                The following few lines create the strings that will be saved in the logfiles, 
                                and then writes them to file.
                                """
                                telemetry='Latitude: {}|Longitude: {}|Lat Dilution: {}|Altitude: {}|Internal Temperature: {}|External Temperature: {}|Pressure: {}'.format(lat,lon,hzdil,alt,temp1,temp2,pressure)
                                sciencetelem='Altitude: {}|Altitude2: {}|External Temperature: {}|Auxiliary Temperature: {}|Pressure: {}|UVA: {}|UVB: {}'.format(alt,altitude2,temp2,temp3,pressure,uva,uvb)
                                """
                                The D & T added to the strings make it easier for the reader to descern telemetry from data packets.
                                """
                                science='D|'+sciencetelem
                                telemlog="T|"+telemetry
                                logging.info(telemetry.encode("ascii"))
                                logging.info(science.encode("ascii"))
                                # Reset log timer
                                self.logStartTime=time.perf_counter()
                                """
                                The following script specifies that if 17 or more seconds have passed since the timer was started/reset, 
                                it will attempt to transmit the telemetry using the satellite radio
                                """
                                if (time.perf_counter()-self.telemetryStartTime)>=17:
                                    try:
                                        telemetry_dict["hhmmss"]=dt.now()
                                        self.myradio.send_telemetry(**telemetry_dict)
                                        print(telemlog.encode("ascii"))
                                        """
                                        Reset timer
                                        """
                                        self.telemetryStartTime=time.perf_counter()
                                        """
                                        The following script specifies that if 27 or more seconds have passed since the timer was started/reset, 
                                        it will attempt to transmit the science data packet using the satellite radio
                                        """
                                        if (time.perf_counter()-self.dataStartTime)>=27:
                                            time.sleep(3)
                                            try:                    
                                                self.myradio.send_data_packet(sciencetelem.encode("ascii"))
                                                print(science.encode("ascii"))
                                                """
                                                Reset  data timer
                                                """
                                                self.dataStartTime=time.perf_counter()
                                                
                                            except Exception:
                                                logging.exception("Error sending science data")
                                        else:
                                            pass
                                    except Exception:
                                        logging.exception("Error sending telemtry")                                
                                else:
                                    pass
                            except Exception:
                                logging.exception("Log start time issue")
                        else:
                            pass
                    except Exception:
                        logging.exception("data logging error")
                else:
                    pass
            except Exception:
                logging.exception("Not sure of the issue")
            else:
                pass
        except Exception:
            logging.exception("Exception in loop()")
        
    def teardown(self):
        """ 
        shutdown sensors
        """
        for sensor in self.sensors:
            self.sensors[sensor].stop()
            print("{} is shutting down....".format(sensor))
        """ 
        Close all files.
        """
        self.temp1_data.close()
        self.temp2_data.close()
        self.temp3_data.close()
        self.pressure_data.close()
        self.altitude1_data.close()
        self.altitude2_data.close()
        self.latitude_data.close()
        self.longitude_data.close()
        self.latdilution_data.close()
        self.uva_data.close()
        self.uvb_data.close()
        
        """ 
        shutdown radio
        """
        self.myradio.stop()   
        print("myradio is shutting down....")
                 
        
if __name__=="__main__":
    RUN().run()
