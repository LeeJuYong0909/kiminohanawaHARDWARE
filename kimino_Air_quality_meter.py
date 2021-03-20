# -*- coding: utf-8 -*-

from sds011 import SDS011 #SDS011 module.. dust(pm10, pm2.5) sensor
import Adafruit_DHT       #DHT22 module.. temperature and humidity sensor
import serial             #For connecting nextion display and mz-z19(co2 sensor)..
import struct             #For send adress to nextion
import pymysql            #For control to DB
import datetime           #For get real time From os
import socket             #For get WanIP
import time
import signal
from rpi_ws281x import *

#get co2 value..
def mh_z19(port):
    ser = serial.Serial(port,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1.0)
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)
      if len(s) >= 4 and s[0] == 0xff and s[1] == 0x86:
        return s[2]*256 + s[3]
        break

#get dust value..
def sds_011(port):
    #[0]-> pm2.5 value, [1] -> pm10 value
    return  SDS011(port).query()

def dht22(pin):
    RH, T = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
    return round(RH, 1), round(T, 1)
    
def handler(signum, frame):
    print('It takes too long!')
    raise Exception('end of time')

#get WanIP
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    
    return s.getsockname()[0]

#get Time...
def realtime():
    year    = datetime.datetime.now().year
    month   = datetime.datetime.now().month
    day     = datetime.datetime.now().day
    hour    = datetime.datetime.now().hour
    minute  = datetime.datetime.now().minute
    second  = datetime.datetime.now().second
    
    date = str(year) + "-" + str(month) + "-" + str(day) + " " + str(hour) + ":" + str(minute) + ":" + str(second)
    
    return date
def nextionSendIP(port):
    k     = struct.pack('B', 0xff)
    wanIP = get_ip_address()
    
    port.write(("ip.txt="+"\""+ str(wanIP)+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
def nextionSendTime(port):
    
    year    = datetime.datetime.now().year
    month   = datetime.datetime.now().month
    day     = datetime.datetime.now().day
    hour    = datetime.datetime.now().hour
    minute  = datetime.datetime.now().minute
    
    k=struct.pack('B', 0xff)
    week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    month_eng = ["jan", "feb", "mar", "ari", "may", "jun", "july", "agu", "sep", "oct","nov","dec"]
    am_pm = "am"
    
    if hour < 10:
        nex_hour = " " + str(hour)
        am_pm = "am"
    elif hour <= 12:
        nex_hour = str(hour)
        am_pm = "am"
        
    elif hour <22:
        nex_hour=" " + str(hour-12)
        am_pm="pm"
    
    else:
        nex_hour= str(hour-12)
        am_pm="pm"
        
    if minute < 10:
        nex_minute ="0" + str(minute)
    else:
        nex_minute = str(minute)
        
    now = time.localtime()
    nex_date = week[now.tm_wday] + " " + month_eng[now.tm_mon-1] + " " + str(day) + " " + str(year)
    hour_minute1 = str(nex_hour) + ' ' + str(nex_minute)
    hour_minute2 = str(nex_hour) + ':' + str(nex_minute)
    
    port.write(("time.txt="+"\""+ hour_minute1+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
    port.write(("realTime.txt="+"\""+ hour_minute2+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)

    port.write(("timeDate.txt="+ "\""+nex_date+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
    port.write(("pmam.txt="+ "\""+am_pm+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
    port.write(("month.txt="+ "\""+str(month)+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)

    port.write(("date.txt="+ "\""+str(day)+"\"").encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
    port.write(("n0.val="+ str(now.tm_wday)).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    

def nextionSendDHT(port, array):
    k=struct.pack('B', 0xff)
    
    port.write(("temp.val="+str(int(round(array[1],0)))).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
                    
    port.write(("humi.val="+str(int(round(array[0],0)))).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
def nextionSendDustAndCO2(port, array, value):
    k=struct.pack('B', 0xff)
    
    port.write(("pm10.val="+str(int(round(array[0],0)))).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
                    
    port.write(("pm2_5.val="+str(int(round(array[1],0)))).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
    port.write(("co2.val="+str(value)).encode())
    port.write(k)
    port.write(k) 
    port.write(k)


def nextionRemote(port, last_command, second):
    mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
    mysock.connect(('39.127.9.114', 80))
    cmd = 'GET http://39.127.9.114/php/remote.txt HTTP/1.0\r\n\r\n'.encode()
    
    mysock.send(cmd)
    data = mysock.recv(512).decode()               
    command = str(data)[(len(data)-1)]
    mysock.close()
    
    
    if last_command != command:
        k=struct.pack('B', 0xff)
        
        if(command == '0'):
            port.write(("page timePage").encode())
            port.write(k)
            port.write(k)
            port.write(k)
                 
        elif(command == '1'):
            port.write(("page co2Page").encode())
            port.write(k)
            port.write(k)
            port.write(k)
            
        elif(command == '2'):
            port.write(("page pm2_5Page").encode())
            port.write(k)
            port.write(k)
            port.write(k)
                
        elif(command == '3'):
            port.write(("page pm10Page").encode())
            port.write(k)
            port.write(k)
            port.write(k)
    return command

def sendValueToDB(array, count):
    date = realtime()
    
    db = pymysql.connect(
            host = "Host Address",
            port = "Port Number",
            user = "[User Name]",
            password = "[password]",
            database = "[DataBase name]",
            autocommit = True
        )
    
    cursor = db.cursor()

    sql = "INSERT INTO measure_data(fine_dust, ultrafine_dust, co2, date_time, date_month, date_week) VALUES(" + str(array[0]/count) + ", " + str(array[1]/count) + ", " + str(array[2]/count) + ", " + "'" + date  + "'" + ", (SELECT MONTH("+"'"+date + "'" + ")), (SELECT WEEKOFYEAR("+"'"+date + "'" + ")));"               
    cursor.execute(sql)
    
    print('########Successfully put the value into DB!#########')
        
    # db.commit()
    cursor.close()
    db.close()

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        
def LEDcolor(array, value):
    color = 0
    
    if array[1] >= 80 or array[0] >= 35 or value >= 1000:
        color = 1
    
    return color
    
def LED(strip, dust, co2):
    color = LEDcolor(dust, co2)
    
    for x in range(0,LED_COUNT):    
        if color:
            strip.setPixelColor(x,Color(255,0,0))
        else:
            strip.setPixelColor(x,Color(0,255,0))
        
    strip.show()    
    
#-----------------------start!-----------------------#

dht22_pin = 4                #dht22 pin number..   GPIO
sds_011_port = '/dev/ttyUSB0' #sds_011 port value.. USB
mh_z19_port  = '/dev/ttyUSB1' #mh_z19 port value..  USB
nextion_port = '/dev/ttyAMA0' #nextion display port value.. UART

second         = 0
minute         = 0
last_second    = 60
last_minute    = 60
time_to_excute = 0

db_array  = [0, 0, 0] #pm10, pm2.5, co2
db_count = 0

delay = 5

command      = 0
last_command = 5

error = 0


# LED strip configuration:
LED_COUNT      = 9      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,LED_DMA,LED_INVERT,LED_BRIGHTNESS,LED_CHANNEL)
strip.begin()

while True:
    try:
        while True:
            try:
                #current_time = CurrentDateTime()
                dust_value      = sds_011(sds_011_port)
                co2_value       = mh_z19(mh_z19_port)
                humi_temp_value = dht22(dht22_pin)
                
                nextion = serial.Serial(nextion_port, 9600)
                
                nextionSendDustAndCO2(nextion, dust_value, co2_value)
                nextionSendDHT(nextion, humi_temp_value)
                
                db_count+= 1
                db_array[0] += dust_value[0]
                db_array[1] += dust_value[1]
                db_array[2] += co2_value
                    
                    
                print('----------------Dust and CO2----------------------')
                print('Currnet dust and co2:', dust_value[1], dust_value[0], co2_value)
                print('Accumulated dust and co2 :', db_array[0], db_array[1], db_array[2])
                print('Cumulative number of times(dust, co2) :', db_count)
                print('--------------------------------------------------')
                
                #after 1 minute..
                break
                
            except:
                print("Connection failed!")
                time.sleep(3)
                
    
        while True:
            second = datetime.datetime.now().second
            minute = datetime.datetime.now().minute
        
            if __name__=="__main__": #
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(60-second)
                
                try:
#                     last_command = nextionRemote(nextion, last_command, second)
                    last_command = 0
    
                except Exception as exc:
                    print(exc)

            if second == 0 and db_count > 3: #Run in 0sec
                    print('Current minute and second >>', minute, ':', second)
                    print('#######Time to send the sensors value to DB..#######')
                    
#                     sendValueToDB(db_array, db_count)
                    
                    db_array  = [0, 0, 0]
                    db_count = 0
                    
                    last_minute = minute
            
            if second != last_second: #Run every 1sec
                print('second : ', second)
                LED(strip, dust_value, co2_value)
                
                nextionSendTime(nextion)
            
                last_second = second
                
                nextionSendIP(nextion)
                    
                if second % delay == 0: #Run every 5sec
                    dust_value      = sds_011(sds_011_port)
                    co2_value       = mh_z19(mh_z19_port)
                    
                   
                    nextionSendDustAndCO2(nextion, dust_value, co2_value)
                     
                    db_count+= 1
                    db_array[0] += dust_value[0]
                    db_array[1] += dust_value[1]
                    db_array[2] += co2_value
                    
                    
                    print('----------------Dust and CO2----------------------')
                    print('Currnet dust and co2:', dust_value[1], dust_value[0], co2_value)
                    print('Accumulated dust and co2 :', db_array[0], db_array[1], db_array[2])
                    print('Cumulative number of times(dust, co2) :', db_count)
                    print('--------------------------------------------------')
                    
                
                if second % 10 == 0:#Repeat every 10sec
                    
                    if __name__=="__main__": #time out is 10sec!
                        signal.signal(signal.SIGALRM, handler)
                        signal.alarm(9)
                        
                        in_time = 0
                        
                        try:
                            while True:
                                humi_temp_value = dht22(dht22_pin)
                                    
                                if humi_temp_value[0] < 100 and  humi_temp_value[0] > 0:
                                    break
                            second = datetime.datetime.now().second
                            if db_count > 12:
                                print("System will die..")
                                break
                            in_time = 1
                            signal.alarm(10000)
            
                        except Exception as exc:
                            print(exc)
                        
                        if in_time:
                            nextionSendDHT(nextion, humi_temp_value)
                            
                            print('-----------------Temp and Humi--------------------')
                            print('Currnet tmep and humi :', humi_temp_value)
                            print('--------------------------------------------------')
                
                
    except:
        print('@@@@@@@@ System error! restart! program.. @@@@@@@@@')
        error+=1
        time.sleep(1)
from sds011 import SDS011
import time

def sds_011(port):
    #[0]-> pm2.5 value, [1] -> pm10 value
    return  SDS011(port).query()

port = '/dev/ttyUSB0'

while 1:
    print(sds_011(port))
    time.sleep(1)    import Adafruit_DHT

def dht22(pin):
    RH, T = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
    return round(RH, 1), round(T, 1)


pin = 4

while True:
    print(dht22(pin))import Adafruit_DHT

Adafruit_DHT(123)
import serial             #For connecting nextion display and mz-z19(co2 sensor)..
import struct             #For send adress to nextion
import argparse

nextion_port = '/dev/ttyAMA0'
nextion = serial.Serial(nextion_port, 9600)

array = [59, 20]
def nextionSendDHT(port, array):
    k=struct.pack('B', 0xff)
    
    port.write(("temp.val="+str(int(round(array[1],0)))).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
                    
    port.write(("humi.val="+str(int(round(array[0],0)))).encode())
    port.write(k)
    port.write(k) 
    port.write(k)
    
nextionSendDHT(nextion, array)import serial 

def mh_z19(port):
    ser = serial.Serial(port,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1.0)
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)
      if len(s) >= 4 and s[0] == 0xff and s[1] == 0x86:
        return s[2]*256 + s[3]
        break

port = '/dev/ttyUSB0'

print(mh_z19(port))import socket

def nextionRemote():
    mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
    mysock.connect(('13.124.189.186', 80))
    cmd = 'GET http://13.124.189.186/php/remote.txt HTTP/1.0\r\n\r\n'.encode()
    
    mysock.send(cmd)
    data = mysock.recv(512).decode()               
    command = str(data)[(len(data)-1)]
    mysock.close()
    
    print(command)
    
nextionRemote()from rpi_ws281x import *
import time
# LED strip configuration:
LED_COUNT      = 43      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

while 1:
    
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,LED_DMA,LED_INVERT,LED_BRIGHTNESS,LED_CHANNEL)
    strip.begin()

    for x in range(0,LED_COUNT):
        strip.setPixelColor(x,Color(0,255,0))

    strip.show()
    time.sleep(1)
    
B

