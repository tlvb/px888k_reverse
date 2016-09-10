# This script acts as a fake Puxing PX888K radio from the perspective of the
# stock programming software.
# It needs to be supplied with a serial port, which is to be connected to the
# serial port used by the stock software, by e.g. a null modem cable.
# A file name may be supplied as a second parameter, which will then be used
# to represent the radio's memory bank which the stock software either reads
# or writes. If no file is suppled, a simple hexdump of the written data
# will be produced on stock software write operations, and read operations
# will fail with an error

import serial
import sys

if len(sys.argv) not in [2,3]:
    print("you need to supply the serial device and a optionally a filename")
    print("if no filename is supplied read operations will fail")
    print("and write operations will be dumped to standard out in hex")
    exit(1)

s = serial.Serial(sys.argv[1], 9600, 8, serial.PARITY_NONE, 1)

# When transferring from radio to computer an extra block needs to be sent.
# I'm not sure what the contents signify, it is at least not a checksum of
# data sent so far, since it can be zeroed out without the host program
# deeming the transmission a failure. It could possibly be firmware and/or
# board revision information. It does not seem to directly contain the
# radio serial number as written on the label.
magic_last_block = bytearray([0 for i in range(64)])

matchinput = b'XONLINE'
matchoutput = b'PX888D\x00\xff'

matched = False
matchindex = 0

print(">>> init")
# the initial match sequence is retried until success, since connection
# and disconnection, etc. often results in one or more garbage bytes
# being picked up
while not matched:
    c = ord(s.read(1))
    if c == matchinput[matchindex]:
        matchindex += 1
        if matchindex == len(matchstring):
            matched = True
    else:
        matchindex = 0

s.write(matchoutput)

running = True
binaryblob = [0 for i in range(63*64)]
mode = ''

while running:
    # request
    command = s.read(1) # E W or R
    if command == b'E': # exit
        print("[E]")
        s.write(b'\x06')
        running = False
    else: # W or R, the command always contains a two byte address, and a length (always 64)
        baseh = ord(s.read(1)) # most significant byte first
        basel = ord(s.read(1))
        base = (baseh<<8)|basel
        length  = ord(s.read(1))
        if command == b'W': # write operation
            mode = 'dump'
            print("[W] receiving block {:04x}".format(base))
            block = s.read(length)
            binaryblob[base] = block
            for i in range(length):
                binaryblob[base+i] = block[i]
            s.write(b'\x06')
        if command == b'R': # read operation
            if mode != 'load':
                mode = 'load'
                if len(sys.argv) != 3:
                    print("no file supplied and reading from standard in is not implemented")
                    exit(2)
                f = open(sys.argv[2], "rb")
                binaryblob = f.read(63*64)
                f.close()
            s.write(bytearray([ord('W'), baseh, basel, length]))
            if base < 0x0fc0:
                print("[R] sending block {:04x}".format(base))
                s.write(binaryblob[base:base+length])
            else:
                print("[R] sending magic block")
                s.write(magic_last_block)
                s.write(b'\x06')
s.close()

if mode == 'dump':
    f = open(sys.argv[2], "wb")
    f.write(bytearray(binaryblob))
    f.close()
