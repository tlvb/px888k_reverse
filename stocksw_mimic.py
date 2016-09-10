import serial
import stat
import sys
import os

descr="""
You need to supply the serial device and optionally a file and access mode. Valid invocations are

{0} serial_device      (1)
{0} serial_device file (2)
{0} file serial_device (3)

In case 1 and 2, data is read from the serial device and in dumped as hex on standard out (1),
or written in binary format to the file (2).
In case 3, data is read (in binary) from the file and written to the serial device.""".format(sys.argv[0])

rpath = ''
wpath = ''
mode = ''

matchoutput = b'XONLINE'
matchinput = b'PX888D\x00\xff'
blocksize = 64
lowerrbound = 0
upperrbound = 0x1000

if len(sys.argv) == 2:
    rpath = sys.argv[1]
    if os.path.exists(rpath) and stat.S_ISCHR(os.stat(rpath).st_mode):
        mode = 'sh' # serial to hexdump
elif len(sys.argv) == 3:
    rpath = sys.argv[1]
    wpath = sys.argv[2]
    if os.path.exists(rpath):
        if stat.S_ISCHR(os.stat(rpath).st_mode) and (not os.path.exists(wpath) or stat.S_ISREG(os.stat(wpath).st_mode)):
            mode = 'sf' # serial to file
        elif stat.S_ISREG(os.stat(rpath).st_mode) and stat.S_ISCHR(os.stat(wpath).st_mode):
            mode = 'fs' # file to serial

if mode not in ['sh', 'sf', 'fs']:
    print(descr)
    exit(1)

print(">>> mode: {}".format(mode))
if mode[0] == 's': # read from radio
    print("foo")
    s = serial.Serial(rpath, 9600, 8, serial.PARITY_NONE, 1)
    print("bar")
    f = sys.stdout
    if mode[1] == 'f':
        f = open(wpath, 'wb')
    s.write(matchoutput)
    x = s.read(len(matchinput))
    if x == matchinput:
        for blockaddr in range(lowerrbound, upperrbound, blocksize):
            print("{:04x}|".format(blockaddr))
    else:
        print(">>> BAD MATCH STRING actual:{}, expected:{}".format(x, matchinput))
    s.close()
    if mode[1] == 'f':
        f.close()

