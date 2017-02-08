    # -*- coding: utf-8 -*-
"""
Created on Sun Feb  5 10:56:12 2017

@author: Dr.Esi (Dr.Esi@outlook.com)

This plugin allows to read out a DHT11 temperature and hunidity sensor. 
http://www.uugear.com/portfolio/dht11-humidity-temperature-sensor-module/ 

It can wright out temperature and humidity (frequency = 1/30) into a text file.


"""

import xbmcaddon
import xbmc
import sys
import time
sys.path.append('storage/.kodi/addons/python.RPi.GPIO/lib')
import RPi.GPIO as GPIO # Signal DHT 11 on GPIO 4

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')

Textfilename = 'Data_stor.txt'
MaxTextFileLength = 35000 # 35'000 lines is equivalent to roughly 1 MByte


def file_len(Textfilename):
    with open(Textfilename) as f:
        for i, l in enumerate(f):
            pass
    try:
        return i + 1
    except:
        return 0    

def deleteLines(Textfilename,numlines):
    txt = open(Textfilename,'r')
    lines = txt.readlines()
    txt.close()
    newlines = lines[0:2] + lines[1+numlines:-1]
    txt = open(Textfilename,'w')
    for i in range(0,len(newlines)):
        txt.write(newlines[i])
    txt.close()

def readBinaryTemp(GPIO_Nr): #reads out the binary data from the sensor
    data = []
    # Prepare the pin and set to output mode
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_Nr,GPIO.OUT)
    # Set the pin on high for 25ms
    GPIO.output(GPIO_Nr,GPIO.HIGH)
    time.sleep(0.025)
    # Set the pin on low for 20ms
    GPIO.output(GPIO_Nr,GPIO.LOW)
    time.sleep(0.02)
    # Switch the pin to read mode and listen, put the sequence into data
    GPIO.setup(GPIO_Nr, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for i in range(0,1000):
        data.append(GPIO.input(GPIO_Nr))
    return data
        
def write2File(Textfilename, string): #writes string into Textfile 
    TARGETFOLDER = xbmc.translatePath('special://home/addons')
    txt = open(TARGETFOLDER + '/script.service.Temperature-Control/' + Textfilename,'a')
    txt.write(string.__str__())
    txt.close()
    
def readBitsAndBytes(data): # Bitwise reads out the values  from data
    pos = 0
    EOF =-1
    Bit = []
    Bit_anouncer_length = []
    Bit_length = []
    
    #find end of file 
    while data[EOF] == 1:
        EOF = EOF - 1
        
    # find the first bit. Each bit starts with a ~50 microsecond low sequence
    while data[pos] == 1:
        pos = pos + 1
    #read out the 5 bytes, bit by bit:
    while pos < len(data) + EOF + 1:
        #read out and measure length of bit announcer, a ~50 microseconds low
        while data[pos] == 0:
            Bit.append(data[pos])
            pos = pos + 1
        Bit_anouncer_length.append(len(Bit))
        Bit = []
        
        #read out and measure length of bit, long high for 1, short for 0
        while data[pos] == 1 and pos < len(data) + EOF:
            Bit.append(data[pos])
            pos = pos + 1
        if pos < len(data) + EOF:
            Bit_length.append(len(Bit))
        Bit = []
    
    Bit_counter = len(Bit_length)
    average_bit = sum(Bit_length)/Bit_counter
    Temp_byte = ''
    Humidity_byte = ''
    Checksum_byte = ''
    #in case too many or too few bits have been read out, return impossible values
    if Bit_counter < 40:
        return '-1','-274'
    
    if Bit_counter > 40:
        return '-1','-274'
        
    #read out temperature, humidity and checksum
    for i in range(0, 40):
        if Bit_length[i] > average_bit+1:
            if i < 8:
                Humidity_byte = Humidity_byte + '1'
            elif i > 15 and i < 24:
                Temp_byte = Temp_byte + '1'
            elif i > 31:
                Checksum_byte = Checksum_byte + '1'
        else:
            if i < 8:
                Humidity_byte = Humidity_byte + '0'
            elif i > 15 and i < 24:
                Temp_byte = Temp_byte + '0'
            elif i > 31:
                Checksum_byte = Checksum_byte + '0'
    
    Temp = int(Temp_byte, 2)
    Humidity = int(Humidity_byte, 2)
    Checksum = int(Checksum_byte, 2)
    
    if Temp + Humidity == Checksum:
        return Humidity.__str__(), Temp.__str__(), Temp
    else:
        return '-1','-274'

ReadOutPin = 4
Write_out = 1
Fan_on = 1
monitor = xbmc.Monitor()
GPIO.setmode(GPIO.BCM)
GPIO.setup(17,GPIO.OUT)

while not monitor.abortRequested():
    # Sleep/wait for abort for 30 seconds
    if monitor.waitForAbort(28):
        # Abort was requested while waiting. We should exit
        break
    Temperature = '-274'
    Humidity = '-1'
    while Temperature == '-274' or Humidity == '-1':
        try:
            data = readBinaryTemp(ReadOutPin)
            Humidity, Temperature, Temp = readBitsAndBytes(data)
            if Temp>40 and Fan_on == 0:
                GPIO.output(17,GPIO.HIGH)
                Fan_on = 1
            elif Temp<35 and Fan_on == 1:
                GPIO.output(17,GPIO.LOW)
                Fan_on = 0
        except:
            pass
    if Write_out == 1:
        write2File(Textfilename, time.strftime('%x, %X, ')+Temperature+', '+Humidity+', '+Fan_on.__str__()+', \n')
        
        #if file_len(Textfilename) > MaxTextFileLength:
            #deleteLines(file_len(Textfilename)-MaxTextFileLength)
        