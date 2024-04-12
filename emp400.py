# for RP-COM / EMP400

import serial
import string

class EMP400:

    def __init__(self):
        self.port = 'COM3'
        self.baudrate = 9600
        self.timeout = 1
        self.ser = 0
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout = self.timeout)
#            pass  # for offlie test (comment out above)
        except serial.SerialException as e:
            print("Cannot open the COM port due to the following reason. \n %s" % e)
            raise Exception("Cannot open the COM port due to the following reason. \n %s" % e)
            

    def __del__(self):
        if hasattr(self, 'ser'):
            self.ser.close()
    

    def comm(self, line):
        line += '\r'
        self.ser.write(line.encode()) # for offline test commented out

    def recv(self):
        lines = self.ser.readlines()
        if not lines:
            raise Exception("No response from EMP400.")
        return lines

    def commrecv(self, line, flagPrint = False):
        self.comm(line)     
        try:
            lines = self.recv()
        except Exception as e:
            print("%s" % e)
            raise Exception("%s" % e)
        if flagPrint:
            for line in lines:
                deLine = line.decode()
                deLine = deLine.replace('\r\n','\n')
                deLine = deLine.replace('\n\r','\n')
                print(deLine, end = "")
            print("")
        return lines
