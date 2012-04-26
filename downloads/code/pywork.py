import serial
import time
import subprocess
import fcntl
import os


def escalatepriv(s):
    data = ''
    # make sure we have a prompt
    s.flushInput()
    s.write('\r\n')
    data = readdata(s)
    indx = data.find('=')
    if data[indx+1:indx+3] == '>>':
        return
    s.write('''quit\r\nacc\r\nOTTER\r\n2ac\r\nTAIL\r\n''')
    time.sleep(1)
    s.flushInput()

# do not need this.  )(s)ead info from cfg.xt
def portlist(ser):
    data = ''
    escalatepriv(ser)
    ser.flushInput()
    ser.write('file dir settings\r\n')
    data = readdata(ser)
    dl = [x[5:6] for x in
            [y.strip() for y in data.split('\r\n')]
            if x.startswith('SET_P')]
    return dl


def readdata(ser):
    pc = None
    dc = None
    while True:
        time.sleep(.5)
        dc = ser.inWaiting()
        if dc == pc:
            break
        else:
            pc = dc
    return ser.read(dc)

def getfile(ser, name):
    escalatepriv(ser)
    readdata(ser)
    ser.write('file read %s\r\n' % (name))
    ser.flushInput()
    subprocess.call(['/usr/bin/rb', '-vv',],
            stdin=ser.fileno(), stdout=ser.fileno())

s = serial.Serial('/dev/ttyS1', timeout=0)

## serial port must block
fl = fcntl.fcntl(s.fileno(), fcntl.F_GETFL)

# flip the O-NONBLOCK bits
fl  &= ~os.O_NONBLOCK
fcntl.fcntl(s.fileno(), fcntl.F_SETFL, fl)
getfile(s, 'cfg.txt')



