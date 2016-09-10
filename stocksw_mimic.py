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
upperrbound = 0x1000 #exclusive
lowerwbound = 0
upperwbound = 0x0fc0 #exclusive

def mkreadcmd(a):
    return bytearray([82, (a&0xff00)>>8, (a&0x00ff), blocksize])
def mkwritecmd(a):
    return bytearray([87, (a&0xff00)>>8, (a&0x00ff), blocksize])

if len(sys.argv) == 2:
    rpath = sys.argv[1]
    if os.path.exists(rpath) and stat.S_ISCHR(os.stat(rpath).st_mode):
        mode = 'SH' # serial to hexdump
elif len(sys.argv) == 3:
    rpath = sys.argv[1]
    wpath = sys.argv[2]
    if os.path.exists(rpath):
        if stat.S_ISCHR(os.stat(rpath).st_mode) and (not os.path.exists(wpath) or stat.S_ISREG(os.stat(wpath).st_mode)):
            mode = 'SF' # serial to file
        elif stat.S_ISREG(os.stat(rpath).st_mode) and stat.S_ISCHR(os.stat(wpath).st_mode):
            mode = 'FS' # file to serial

if mode not in ['SH', 'SF', 'FS']:
    print(descr)
    exit(1)

print(">>> MODE: {}".format(mode))
f = None
s = serial.Serial([wpath,rpath][mode[0]=='S'], 9600, 8, serial.PARITY_NONE, 1)
s.write(matchoutput)
x = s.read(len(matchinput))
if x == matchinput:
    print(">>> HANDSHAKE OK")
    if mode[0] == 'S': # read from radio, write to stdout or file
        print(">>> READING...")
        if mode[1] == 'F':
            f = open(wpath, 'wb')
        for blockaddr in range(lowerrbound, upperrbound, blocksize):
            s.write(mkreadcmd(blockaddr))
            x = s.read(4)
            if x == mkwritecmd(blockaddr):
                block = s.read(blocksize)
                if mode[1] == 'H':
                    for sba in range(0, blocksize, 16):
                        if sba == 0:
                            print('{:04x} {:04x} |'.format(blockaddr, blockaddr+sba), end='')
                        else:
                            print('     {:04x} |'.format(blockaddr+sba), end='')
                        for sbo in range(16):
                            print(' {:02x}'.format(block[sba+sbo]), end='')
                        print(' | ', end='')
                        for sbo in range(16):
                            if block[sba+sbo] in range(0x20,0x7f):
                                print('{:c}'.format(block[sba+sbo]), end='')
                            else:
                                print('.', end='')
                        print(' |')
                else:
                    f.write(block)
            else:
                print(">>> BAD COMMAND STRING actual:{}, expected:{}".format(x, mkwritecmd(blockaddr)))
    else: # read from file, write to radio
        print(">>> WRITING...")
        f = open(rpath, 'rb')
        for blockaddr in range(lowerwbound, upperwbound, blocksize):
            block = f.read(blocksize)
            s.write(mkwritecmd(blockaddr))
            s.write(block)
            x = s.read(1)
            if x != b'\x06':
                print(">>> BAD FINAL ACK BYTE actual: {}, expected: {}".format(x, b'\x06'))

else:
    print(">>> BAD MATCH STRING actual:{}, expected:{}".format(x, matchinput))
s.write(b'E')
x = s.read(1)
if x != b'\x06':
    print(">>> BAD FINAL ACK BYTE actual: {}, expected: {}".format(x, b'\x06'))
s.close()
if 'F' in mode:
    f.close()
print(">>> DONE")

