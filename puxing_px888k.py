# Copyright 2016 Leo Barring <leo.barring@protonmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from chirp import chirp_common, directory, memmap, bitwise, settings, errors, util
from struct import pack
import logging

LOG = logging.getLogger(__name__)

####################################################################################################
####################################################################################################
#
#
ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES = False
#
# With this setting enabled, some CHIRP settings are stored in thought-to-be junk/padding
# data of the channel memories. Enabling this feature while using CHIRP with an actual radio
# and any effects thereof is entirely the responsibility of the user.
#
####################################################################################################
####################################################################################################

SUPPORT_NONSPLIT_DUPLEX_ONLY = False
SUPPORT_SPLIT_BUT_DEFAULT_TO_NONSPLIT_ALWAYS = True
UNAMBIGUOUS_CROSS_MODES_ONLY = True

MEM_FORMAT = """ // {{{
struct {
#seekto 0x0000;
    struct { // {{{
        struct { // {{{

            // 0-3
            bbcd rx_freq[4]; // actually bbcd, but may also be ff.. if unset

            // 4-7
            bbcd tx_freq[4];

            // 8-9 A-B
            struct {
                u8 digital:1,
                   invert:1,
                   high:6;
                u8 low;
            } tone[2]; // tx_squelch on 0, rx_squelch on 1

            // C
            u8 duplex_sign:2, // not used for memories, but kept for name consistency
               compander:1,
               txpower:1,
               modulation_width:1,
               txrx_reverse:1,
               bcl:2;

            // D
            u8 scrambler_type:3,
               use_scrambler:1,
               opt_signal:2,
               ptt_id_edge:2;

            // E-F
            // u8 _unknown_000E[2];
            %s

        } data[128]; // }}}
        struct { // {{{

            // 0-5, alt 8-D
            char entry[6];

            // 6-8, alt E-F
            char _unknown_0806[2];

        } names[128]; // }}}
#seekto 0x0c20;
        bit present[128];
#seekto 0x0c30;
        bit priority[128];
    } channel_memory; // }}}
#seekto 0x0c00;
    struct { // {{{

        // 0-3
        bbcd rx_freq[4];

        // 4-7
        bbcd tx_freq[4]; // actually offset, but kept for name consistency

        // 8
        struct {
            u8 digital:1,
               invert:1,
               high:6;
            u8 low;
        } tone[2]; // tx_squelch on 0, rx_squelch on 1

        // C
        u8 duplex_sign:2,
           compander:1,
           txpower:1,
           modulation_width:1,
           txrx_reverse:1,
           bcl:2;

        // D
        u8 scrambler_type:3,
           use_scrambler:1,
           opt_signal:2,
           ptt_id_edge:2;

        // E-F
        // u8 _unknown_0C0E[2];
        %s

    } vfo_data[2]; // }}}
#seekto 0xc40;
    struct { // {{{
        // 0-5
        char model_string[6];     // typically PX888D, unknown if rw or ro
        // 6-7
        u8 _unknown_0C46[2];
        // 8-9
        struct {
            bbcd lower_freq[2];
            bbcd upper_freq[2];
        } band_limits[2];
    } model_information; // }}}
#seekto 0x0c50;
    char radio_information_string[16];
#seekto 0x0c60;
    struct { // {{{
        // 0
        u8 ptt_cancel_sq:1,  // 0x80
           dis_ptt_id:1,     // 0x40
           workmode_b:2,     // 0x30
           use_roger_beep:1, // 0x08
           msk_reverse:1,    // 0x04
           workmode_a:2;     // 0x03

        // 1
        u8 backlight_color:2,
           backlight_mode:2,
           dual_single_watch:1,
           auto_keylock:1,
           scan_mode:2;

        // 2
        u8 rx_stun:1,
           tx_stun:1,
           boot_message_mode:2,
           battery_save:1,
           key_beep:1,
           voice_announce:2;

        bbcd squelch_level;     // 3
        bbcd tx_timeout;  // 4

        // 5
        u8 allow_keypad:1,
           relay_without_disable_tail:1
           _unknown_0C65:1,
           call_channel_active:1,
           vox_gain:4;

        bbcd vox_delay;   // 6
        bbcd vfo_step;    // 7
        bbcd ptt_id_type; // 8

        // 9
        u8 keypad_lock:1,
            _unknown_0C69_1:1,
            side_button_hold_mode:2,
            dtmf_sidetone:1,
            _unknown_0C69_2:1,
            side_button_click_mode:2;

        // A
        u8 roger_beep:4,
           main_watch:1,
           _unknown_0C6A:3;

        u8 channel_a; // B
        u8 channel_b; // C

        u8 priority_channel; // D

        u8 wait_time;  // E

        u8 _unknown_0C6F; // F

        u8 _unknown_0C70[8];
        char boot_message[6];

    } opt_settings; // }}}
#seekto 0x0c80;
    struct { // {{{
        // these fields are used for all ptt id forms (msk/dtmf/5t)
        // (only one can be active and stored at a time)
        // and different constraints are applied depending
        // on the ptt id type
        u8 entry[7];
        u8 length;
    } ptt_id_data[2]; // }}}
#seekto 0x0c90;
    struct { // {{{
        u8 _unknown_0C90;
        u8 _unknown_0C91_1:3,
           channel_stepping:1,
           unknown_0C91_2:1
           receive_range:2
           unknown_0C91_3:1;
        u8 _unknown_0C92[2];
        u8 vfo_freq[4];
        struct {
            u8 entry[4];
        } memory[10];
    } fm_radio; // }}}
#seekto 0x0cc0;
    struct { // {{{
        char id_code[4];
        struct {
            char entry[4];
        } phone_book[9];
    } msk_settings; // }}}
#seekto 0x0cf0;
    struct { // {{{

        // 0-3
        bbcd rx_freq[4];

        // 4-7
        bbcd tx_freq[4];

        // 8
        struct {
            u8 digital:1,
               invert:1,
               high:6;
            u8 low;
        } tone[2]; // tx_squelch on 0, rx_squelch on 1


        // C
        u8 duplex_sign:2, // not used in CALL channel, kept for consistency
           compander:1,
           txpower:1,
           modulation_width:1,
           txrx_reverse:1
           bcl:2;

        // D
        u8 scrambler_type:3,
           use_scrambler:1,
           opt_signal:2,
           ptt_id_edge:2;

        // E-F
        // u8 _unknown_0CFE[2];
        %s

    } call_channel; // }}}
#seekto 0x0d00;
    struct { // {{{

        // regarding DTMF codes:
        // stored as hex, 0-9 A-D are mapped straight
        // DTMF '*' is HEX E, DTMF '#' is HEX F

        // 0x0d00
        struct {
            u8 digit_length;       // 0x05 to 0x14 corresponding to 50-200ms
            u8 inter_digit_pause;  // same
            u8 first_digit_length; // same
            u8 first_digit_delay;  // 0x02 to 0x14 corresponding to 100-1000ms
        } timing;
#seekto 0x0d30;
        u8 _unknown_0D30[2]; // 0-1
        u8 group_code;       // 2
        u8 reset_time; // 3
        u8 alert_transpond;  // 4
        u8 id_code[4];       // 5-8
        u8 _unknown_0D39[4]; // 9-C
        u8 id_code_length;   // D
        u8 _unknown_0d3e[2]; // E-F
// 0x0d40
        u8 tx_stun_code[4];
        u8 _unknown_0D44[4];
        u8 tx_stun_code_length;
        u8 cancel_tx_stun_code_length;
        u8 cancel_tx_stun_code[4];
        u8 _unknown_0D4E[2];
// 0x0d50
        u8 rxtx_stun_code[4];
        u8 _unknown_0D54[4];
        u8 rxtx_stun_code_length;
        u8 cancel_rxtx_stun_code_length;
        u8 cancel_rxtx_stun_code[4];
        u8 _unknown_0D4E[2];
// 0x0d60
        struct {
            u8 entry[5];
            u8 _unknown_0D65[3];
            u8 length;
            u8 _unknown_0D69[7];
        } phone_book[9];
    } dtmf_settings; // }}}
    struct { // {{{
#seekto 0x0e00;
        u8 delay;            // 0
        u8 _unknown_0E01[5]; // 1-5
        u8 alert_transpond;  // 6
        u8 reset_time;       // 7
        u8 tone_standard;    // 8
        u8 id_code[3];       // 9-B
#seekto 0x0e20;
        struct {
            u8 period;
            u8 group_code:4,
               repeat_code:4;
        } tone_settings[4]; // the order is ZVEI1 ZVEI2 CCIR1 CCITT
#seekto 0x0e40;
        // unknown use, changing the values does not seem to have
        // any effect on the produced sound, but the values are not
        // overwritten either.
        il16 tone_frequency_table[16]; // 0-9 A-F
// 0xe60
        u8 tx_stun_code[5];
        u8 _unknown_0E65[3];
        u8 tx_stun_code_length;
        u8 cancel_tx_stun_code_length;
        u8 cancel_tx_stun_code[5];
        u8 _unknown_0E6F;
// 0xe70
        u8 rxtx_stun_code[5];
        u8 _unknown_0E75[3];
        u8 rxtx_stun_code_length;
        u8 cancel_rxtx_stun_code_length;
        u8 cancel_rxtx_stun_code[5];
        u8 _unknown_0E7F;
// 0xe80
        struct {
            u8 entry[3];
        } phone_book[9];
    } five_tone_settings; // }}}
} mem;
// }}}"""
# various magic numbers and strings, apart from the memory format {{{
if ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES: # {{{
    LOG.warn("ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES AND/OR DANGEROUS FEATURES ENABLED")
    MEM_FORMAT = MEM_FORMAT % (
            "u8 _unknown_000E_1: 6, experimental_unsupported_duplex_mode_indicator: 1, experimental_unsupported_force_cross_mode_indicator: 1; u8 _unknown_000F;",
            "u8 _unknown_0C0E_1: 6, experimental_unsupported_duplex_mode_indicator: 1, experimental_unsupported_force_cross_mode_indicator: 1; u8 _unknown_0C0F;",
            "u8 _unknown_0CFE_1: 6, experimental_unsupported_duplex_mode_indicator: 1, experimental_unsupported_force_cross_mode_indicator: 1; u8 _unknown_0CFF;")
    # we don't need these settings anymore, because it's exactly what the
    # experimental features are about
    SUPPORT_SPLIT_BUT_DEFAULT_TO_NONSPLIT_ALWAYS = False
    SUPPORT_NONSPLIT_DUPLEX_ONLY = False
    UNAMBIGUOUS_CROSS_MODES_ONLY = False
# }}}
else: # {{{
    MEM_FORMAT = MEM_FORMAT % (
            "u8 _unknown_000E[2];",
            "u8 _unknown_0C0E[2];",
            "u8 _unknown_0CFE[2];")
# }}}

FILE_MAGIC           = [0xc40, 0xc50, '\x50\x58\x38\x38\x38\x44\x00\xff\x13\x40\x17\x60\x40\x00\x48\x00']
HANDSHAKE_OUT        = b'XONLINE'
HANDSHAKE_IN         = [b'PX888D\x00\xff'] # huh I thought this was a K radio!

LOWER_READ_BOUND     = 0
UPPER_READ_BOUND     = 0x1000 # exclusive, one more block is read than written by the stock software
LOWER_WRITE_BOUND    = 0
UPPER_WRITE_BOUND    = 0x0fc0 # exclusive
BLOCKSIZE            = 64

OFF_INT              = ["Off"] + [str(x+1) for x in range(100)] # lots of settings are on this form, with various lengths
OFF_ON               = ["Off", "On"]
INACTIVE_ACTIVE      = ["Inactive", "Active"]
NO_YES               = ["No", "Yes"]
YES_NO               = ["Yes", "No"]

BANDS                = [(134000000, 176000000),  # VHF
                        (400000000, 480000000)]  # UHF

SPECIAL_CHANNELS     = {'VFO-A':-2, 'VFO-B':-1, 'CALL':0}
SPECIAL_NUMBERS      = {-2:'VFO-A', -1:'VFO-B', 0:'CALL'}

DUPLEX_MODES         = ['', '+', '-', 'split']
if SUPPORT_NONSPLIT_DUPLEX_ONLY:
    DUPLEX_MODES     = ['', '+', '-']

TONE_MODES           = ["", "Tone", "TSQL", "DTCS", "Cross" ]

CROSS_MODES          = ["Tone->Tone", "DTCS->", "->DTCS", "Tone->DTCS", "DTCS->Tone", "->Tone", "DTCS->DTCS", "Tone->"]
if UNAMBIGUOUS_CROSS_MODES_ONLY:
    CROSS_MODES      = ["Tone->Tone", "DTCS->", "->DTCS", "Tone->DTCS", "DTCS->Tone", "->Tone", "DTCS->DTCS"]

MODES                = ["NFM", "FM" ]

POWER_LEVELS         = [chirp_common.PowerLevel("Low", watts                                                              = 0.6), # google search VHF:0.5 UHF:0.7, spec lacks info
                        chirp_common.PowerLevel("High", watts = 4.5)]  # spec says VHF:4 UHF 5

SKIP_MODES           = ["", "S"]
BCL_MODES            = ["Off", "Carrier", "QT/DQT"]
SCRAMBLER_MODES      = OFF_INT[0:9]
PTT_ID_EDGES         = ["Off", "BOT", "EOT", "Both"]
OPTSIGN_MODES        = ["None", "DTMF", "5-Tone", "MSK"]

VFO_STRIDE           = ['5kHz', '6.25kHz', '10kHz', '12.5kHz', '25kHz' ]
AB                   = ['A', 'B']
WATCH_MODES          = ['Single watch', 'Dual watch']
AB_MODES             = ['VFO', 'Memory index', 'Memory name', 'Memory frequency']
SCAN_MODES           = ["Time", "Carrier", "Seek"]
WAIT_TIMES           = [("0.3s", 6), ("0.5s", 10)] + [("%ds"%t, t*20) for t in range(1,13)]

BUTTON_MODES         = [ "Send call list data", "Emergency alarm", "Send 1750Hz signal", "Open squelch"]
BOOT_MESSAGE_TYPES   = ["Off", "Battery voltage", "Custom message"]
TALKBACK             = ['Off', 'Chinese', 'English' ]
BACKLIGHT_COLORS     = zip(["Blue", "Orange", "Purple"], range(1,4))
VOX_GAIN             = OFF_INT[0:10]
VOX_DELAYS           = ['1s', '2s', '3s', '4s']
TRANSMIT_ALARMS      = ['Off', '30s', '60s', '90s', '120s', '150s', '180s', '210s', '240s', '270s']

DATA_MODES           = ['MSK', 'DTMF', '5-Tone' ]

ASCIIPART            = ''.join([ chr(x) for x in range(0x20, 0x7f) ])
DTMF                 = "0123456789ABCD*#"
HEXADECIMAL          = "0123456789ABCDEF"

ROGER_BEEP           = OFF_INT[0:11]
BACKLIGHT_MODES      = ["Off", "Auto", "On"]

TONE_RESET_TIME      = [ 'Off' ] + [ '%ds'%x for x in range(1,256) ]
DTMF_TONE_RESET_TIME = TONE_RESET_TIME[0:16]

DTMF_GROUPS          = zip([ "Off", "A", "B", "C", "D", "*", "#" ], [255]+range(10,16))
FIVE_TONE_STANDARDS  = ['ZVEI1', 'ZVEI2', 'CCIR1', 'CCITT']

SANE_MEMORY_DEFAULT  = b"\x13\x60\x00\x00\x13\x60\x00\x00\xff\xff\xff\xff\xc0\x00\xff\xff"


# these two option sets are listed differently, like this, in the stock software, so I'm keeping them separate for now
# if they are in fact identical in behaviour, that should probably be amended
DTMF_ALERT_TRANSPOND      = zip(['Off', 'Call alert', 'Transpond-alert', 'Transpond-ID code'], [255]+range(1,4))
FIVE_TONE_ALERT_TRANSPOND = zip(['Off', 'Alert tone', 'Transpond', 'Transpond-ID code'], [255]+range(1,4))

BFM_BANDS  = ['87.5-108MHz', '76.0-91.0MHz', '76.0-108.0MHz', '65.0-76.0MHz']
BFM_STRIDE = ['100kHz', '50kHz']
# }}}
def initial_handshake(pipe, tries): # {{{
    x = False
    for i in range(tries):
        x = attempt_initial_handshake(pipe)
        if x: break
    if not x: raise errors.RadioError("Initial handshake failed all ten tries.")
# }}}
def piperead(pipe, amount): # {{{
    """read some data, catch exceptions, validate length of data read"""
    try:
        d = pipe.read(amount)
    except Exception as e:
        raise errors.RadioError("Tried to read %d bytes from the pipe, but got an exception: %s"%(amount, repr(e)))
    if d is None:
        raise errors.RadioError("Tried to read %d bytes to the pipe, but read operation returned <None>."%(amount))
    if d is None or len(d) != amount:
        raise errors.RadioError("Tried to read %d bytes from the pipe, but got %d bytes instead."%(amount, len(d)))
    return d
# }}}
def pipewrite(pipe, data): # {{{
    """write some data, catch exceptions, validate length of data written"""
    try:
        n = pipe.write(data)
    except Exception as e:
        raise errors.RadioError("Tried to write %d bytes to the pipe, but got an exception: %s."%(len(data), repr(e)))
    if n is None:
        raise errors.RadioError("Tried to write %d bytes to the pipe, but write operation returned <None>."%(len(data)))
    if n != len(data):
        raise errors.RadioError("Tried to write %d bytes to the pipe, but wrote %d bytes instead."%(len(data), n))
# }}}
def attempt_initial_handshake(pipe): # {{{
    pipewrite(pipe, HANDSHAKE_OUT)
    x = piperead(pipe, len(HANDSHAKE_IN[0]))
    if x in HANDSHAKE_IN:
        return True
    LOG.debug("Handshake failed: received: "+repr(x)+" expected one of: "+repr(HANDSHAKE_IN))
    return False
# }}}
def mk_writecommand(addr): # {{{
    return pack('>cHc', b'W', addr, b'@')
# }}}
def mk_readcommand(addr): # {{{
    return pack('>cHc', b'R', addr, b'@')
# }}}
def expect_ack(pipe): # {{{
    x = piperead(pipe, 1)
    if x != b'\x06':
        LOG.debug("Did not get ACK when expected. received: "+repr(x)+", expected: '\\x06'")
        raise errors.RadioError("Did not get ACK when expected.")
# }}}
def end_communications(pipe): # {{{
    pipewrite(pipe, b'E')
    expect_ack(pipe)
# }}}
def read_block(pipe, addr): # {{{
    """read and return a chunk of data at specified address"""
    r = mk_readcommand(addr)
    w = mk_writecommand(addr)
    pipewrite(pipe, r)
    x = piperead(pipe, len(w))
    if x != w:
        raise errors.RadioError("Received data not following protocol.")
    block = piperead(pipe, BLOCKSIZE)
    return block
# }}}
def write_block(pipe, addr, block): # {{{
    """write a chunk of data at specified address"""
    w = mk_writecommand(addr)
    pipewrite(pipe, w)
    pipewrite(pipe, block)
    expect_ack(pipe)
# }}}
def show_progress(radio, blockaddr, upper, msg): # {{{
    if radio.status_fn:
        status = chirp_common.Status()
        status.cur = blockaddr
        status.max = upper
        status.msg = msg
        radio.status_fn(status)
# }}}
def do_download(radio): # {{{
    initial_handshake(radio.pipe, 10)
    memory = memmap.MemoryMap(b'\xff'*0x1000)
    for blockaddr in range(LOWER_READ_BOUND, UPPER_READ_BOUND, BLOCKSIZE):
        LOG.debug("Reading block "+str(blockaddr))
        block = read_block(radio.pipe, blockaddr)
        memory.set(blockaddr, block)
        show_progress(radio, blockaddr, UPPER_READ_BOUND, "Reading radio memory... %04x"%blockaddr)
    end_communications(radio.pipe)
    return memory
# }}}
def do_upload(radio): # {{{
    memory = radio.get_mmap()
    initial_handshake(radio.pipe, 10)
    for blockaddr in range(LOWER_WRITE_BOUND, UPPER_WRITE_BOUND, BLOCKSIZE):
        LOG.debug("Writing block "+str(blockaddr))
        block = memory[blockaddr:blockaddr+BLOCKSIZE]
        write_block(radio.pipe, blockaddr, block)
        show_progress(radio, blockaddr, UPPER_WRITE_BOUND, "Writing radio memory... %04x"%blockaddr)
    end_communications(radio.pipe)
# }}}
def parse_tone(t): # {{{
    if int(t.high) == 0x3f and int(t.low) == 0xff:
        return [None, None, None]
    elif bool(t.digital):
        t = [ 'DTCS',
                 (int(t.high)&0x0f)*100 + ((int(t.low)&0xf0)>>4)*10 + (int(t.low)&0x0f),
                 ['N','R'][bool(t.invert)] ]
        if t[1] not in chirp_common.DTCS_CODES: return [None, None, None]
    else:
        t = [ 'Tone',
                 (((int(t.high)&0xf0)>>4)*1000 + (int(t.high)&0x0f)*100 + ((int(t.low)&0xf0)>>4)*10 + (int(t.low)&0x0f))/10.0,
                 None]
        if t[1] not in chirp_common.TONES: return [None, None, None]
    return t
# }}}
def unparse_tone(t): # {{{
    # [ mode, value, polarity ]
    if t[0] == 'Tone':
        tint = int(t[1]*10)
        t0 = tint % 10 ; tint //= 10
        t1 = tint % 10 ; tint //= 10
        t2 = tint % 10 ; tint //= 10
        t3 = tint
        high = (t3 << 4) | t2
        low = (t1 << 4) | t0
        digital = False; invert = False;
        return digital, invert, high, low
    elif t[0] == 'DTCS':
        tint = int(t[1])
        t0 = tint % 10 ; tint //= 10
        t1 = tint % 10 ; tint //= 10
        t2 = tint
        high = t2
        low = (t1 << 4) | t0
        digital = True
        invert = t[2] == 'R'
        return digital, invert, high, low
    return None
# }}}
def decode_halfbytes(data, mapping, length): # {{{
    s = ''
    for i in range(length):
        if i&1 == 0: # even digit
            s += mapping[ (int(data[i>>1])&0xf0)>>4 ]
        else: # odd digit
            s += mapping[  int(data[i>>1])&0x0f     ]
    return s
# }}}
def encode_halfbytes(data, datapad, mapping, fillvalue, fieldlen): # {{{
    if len(data) & 1: data += datapad # pad to an even length
    o = [fillvalue] * fieldlen
    for i in range(0,len(data),2):
        v = (mapping.index(data[i]) << 4) | mapping.index(data[i+1])
        o[i>>1] = v
    return bytearray(o)
# }}}
def decode_ffstring(data): # {{{
    s = ''
    for b in data:
        if int(b) == 0xff: break
        s += chr(int(b))
    return s
# }}}
def encode_ffstring(data, fieldlen): # {{{
    extra = fieldlen-len(data)
    if extra > 0:
        data += '\xff'*extra
    return bytearray(data)
# }}}
def decode_dtmf(data, length): # {{{
    if length == 0xff: return ''
    return decode_halfbytes(data, DTMF, length)
# }}}
def encode_dtmf(data, length, fieldlen): # {{{
    return encode_halfbytes(data, '0', DTMF, b'\xff', fieldlen)
# }}}
def decode_5tone(data): # {{{
    if (int(data[2])&0x0f) != 0: return ''
    return decode_halfbytes(data, HEXADECIMAL, 5)
# }}}
def encode_5tone(data, fieldlen): # {{{
    return encode_halfbytes(data, '0', HEXADECIMAL, b'\xff', fieldlen)
# }}}
def decode_freq(data): # {{{
    data_out = ''
    if data[0] != 0xff:
        data_out = chirp_common.format_freq(int(decode_halfbytes(data, "0123456789", len(data)))*100000)
    return data_out
# }}}
def encode_freq(data, fieldlen): # {{{
    data_out = bytearray('\xff')*fieldlen
    if data != '':
        data_out = encode_halfbytes(('%%0%di'%(fieldlen<<1))%int(chirp_common.parse_freq(data)/10),'','0123456789','',fieldlen)
    return data_out
# }}}
def sbyn(s, n): # {{{
    """setting by name"""
    return filter(lambda x:x.get_name() == n, s)[0]
# }}}

# These helper classes provide a direct link between the value of the widget shown in the
# ui, and the setting in the memory map of the radio, lessening the need to write large
# chunks of code, first for populating the ui from the memory map, then secondly for
# parsing the values back.
# By supplying the mem entry to the setting instance, it is possible to automatically
# 1) initialize the value of the setting, as well as 2) automatically update the memory
# value when the user changes it in the ui, without adding any code outside the class.
class MappedIntegerSettingValue(settings.RadioSettingValueInteger): # {{{
    """"Integer setting, with the possibility to add translation functions"""
    def __init__(self, val_mem, minval, maxval, step=1, int_from_mem=lambda x:int(x), mem_from_int=lambda x:x, autowrite=True):
        self._val_mem = val_mem
        self._int_from_mem = int_from_mem
        self._mem_from_int = mem_from_int
        self._autowrite = autowrite
        settings.RadioSettingValueInteger.__init__(self, minval, maxval, self._int_from_mem(val_mem), step)
    def set_value(self, x):
        settings.RadioSettingValueInteger.set_value(self, x)
        if self._autowrite: self.write_mem()
    def write_mem(self):
        if self.get_mutable() and self._mem_from_int is not None:
            self._val_mem.set_value(self._mem_from_int(settings.RadioSettingValueInteger.get_value(self)))
# }}}
class MappedListSettingValue(settings.RadioSettingValueMap): # {{{
    """Mapped list setting"""
    def __init__(self, val_mem, options, autowrite=True):
        self._val_mem = val_mem
        self._autowrite = autowrite
        if not isinstance(options[0], tuple):
            options = zip(options, range(len(options)))
        settings.RadioSettingValueMap.__init__(self, options, mem_val=int(val_mem))
    def set_value(self, value):
        settings.RadioSettingValueMap.set_value(self, value)
        if self._autowrite: self.write_mem()
    def write_mem(self):
        if self.get_mutable():
            self._val_mem.set_value(settings.RadioSettingValueMap.get_mem_val(self))
# }}}
class MappedCodedStringSettingValue(settings.RadioSettingValueString): # {{{
    """generic base class for a number of mapped presented-as-strings values which may need conversion between mem and string, and may store a length value in a separate mem field"""
    def __init__(self, val_mem, len_mem, min_length, max_length, charset=ASCIIPART, padchar=' ', autowrite=True,
            str_from_mem=lambda mve,lve:str(mve[0:int(lve)]), mem_val_from_str=lambda s,fl:s[0:fl], mem_len_from_int=lambda l:l):
        """
        val_mem          - memory entry for the value
        len_mem          - memory entry for the length (or None)
        min_length       - length that the string will be right-padded to
        max_length       - maximum length of the string, set as maxlength for the RadioSettingValueString
        charset          - the allowed charset
        padchar          - the character that will be used to pad short strings, if not in the charset, charset[0] is used
        autowrite        - automatically call write_mem when the ui value change
        str_from_mem     - function to convert from memory entry to string value, form: func(value_entry, length_entry or none) -> string
        mem_val_from_str - function to convert from string value to memory-fitting value, form: func(string, value_entry_length) -> value to store in value entry
        mem_len_from_int - function to convert from string length to memory-fitting value, form: func(stringlength) -> value to store in length entry
        """
        self._min_length = min_length
        self._val_mem = val_mem
        self._len_mem = len_mem
        self._padchar = padchar
        if padchar not in charset:
            self._padchar = charset[0]
        self._autowrite = autowrite
        self._str_from_mem = str_from_mem
        self._mem_val_from_str = mem_val_from_str
        self._mem_len_from_int = mem_len_from_int
        settings.RadioSettingValueString.__init__(self, 0, max_length, self._str_from_mem(self._val_mem, self._len_mem), charset=charset, autopad=False)
    def set_value(self, value):
        """Set the value of the string, pad if below minimum length, unless it's '' to provide a distinction between uninitialized/reset data and needs-to-be-padded data"""
        while len(value) < self._min_length and len(value) != 0:
            value += self._padchar
        settings.RadioSettingValueString.set_value(self, value)
        if self._autowrite: self.write_mem()
    def write_mem(self):
        """update the memory"""
        if not self.get_mutable() or self._mem_val_from_str is None:
            return
        v = self.get_value()
        l = len(v)
        self._val_mem.set_value(self._mem_val_from_str(v, len(self._val_mem)))
        if self._len_mem is not None and self._mem_len_from_int is not None:
            self._len_mem.set_value(self._mem_len_from_int(l))
# }}}
class MappedFFStringSettingValue(MappedCodedStringSettingValue): # {{{
    """Mapped string setting, tailored for the puxing px888k which uses 0xff terminated strings."""
    def __init__(self, val_mem, min_length, max_length, charset=ASCIIPART, padchar=' ', autowrite=True):
        MappedCodedStringSettingValue.__init__(self,
                val_mem, None, min_length, max_length, charset=charset, padchar=padchar, autowrite=autowrite,
                str_from_mem=lambda mve,lve: decode_ffstring(mve),
                mem_val_from_str=lambda s,fl: encode_ffstring(s, fl),
                mem_len_from_int=None)
# }}}
class MappedDTMFStringSettingValue(MappedCodedStringSettingValue): # {{{
    """Mapped string setting, tailored for the puxing px888k field pairs (value+length) storing DTMF codes"""
    def __init__(self, val_mem, len_mem, min_length, max_length, autowrite=True):
        MappedCodedStringSettingValue.__init__(self,
                val_mem, len_mem, min_length, max_length, charset=DTMF, padchar='0', autowrite=autowrite,
                str_from_mem=lambda mve,lve: decode_dtmf(mve, lve),
                mem_val_from_str=lambda s,fl: encode_dtmf(s, len(s), fl))
# }}}
class MappedFiveToneStringSettingValue(MappedCodedStringSettingValue): # {{{
    """Mapped string setting, tailored for the puxing px888k fields storing 5-Tone codes"""
    def __init__(self, val_mem, autowrite=True):
        MappedCodedStringSettingValue.__init__(self,
                val_mem, None, 0, 5, charset=HEXADECIMAL, padchar='0', autowrite=autowrite,
                str_from_mem=lambda mve, lve: decode_5tone(mve),
                mem_val_from_str=lambda s, fl: encode_5tone(s, fl),
                mem_len_from_int=None)
# }}}
class MappedFreqStringSettingValue(MappedCodedStringSettingValue): # {{{
    """Mapped string setting, tailored for the puxing px888k fields for the FM radio frequencies"""
    def __init__(self, val_mem, autowrite=True):
        MappedCodedStringSettingValue.__init__(self,
                val_mem, None, 0, 128, charset=ASCIIPART, padchar=' ', autowrite=autowrite,
                str_from_mem=lambda mve,lve: decode_freq(mve),
                mem_val_from_str=lambda s,fl: encode_freq(s, fl))
# }}}

# These functions lessen the amount of boilerplate on the form
# x = RadioSetting("AAA", "BBB", SomeKindOfRadioSettingValue( ... ))
# to
# x = some_kind_of_setting("AAA", "BBB", ... )
def integer_setting(k, n, *args, **kwargs): # {{{
    return settings.RadioSetting(k, n, MappedIntegerSettingValue(*args, **kwargs))
# }}}
def list_setting(k, n, *args, **kwargs): # {{{
    return settings.RadioSetting(k, n, MappedListSettingValue(*args, **kwargs))
# }}}
def ff_string_setting(k, n, *args, **kwargs): # {{{
    return settings.RadioSetting(k, n, MappedFFStringSettingValue(*args, **kwargs))
# }}}
def dtmf_string_setting(k, n, *args, **kwargs): # {{{
    return settings.RadioSetting(k, n, MappedDTMFStringSettingValue(*args, **kwargs))
# }}}
def five_tone_string_setting(k, n, *args, **kwargs): # {{{
    return settings.RadioSetting(k, n, MappedFiveToneStringSettingValue(*args, **kwargs))
# }}}
def frequency_setting(k, n, *args, **kwargs): # {{{
    return settings.RadioSetting(k, n, MappedFreqStringSettingValue(*args, **kwargs))
# }}}

@directory.register
class Puxing_PX888K_Radio(chirp_common.CloneModeRadio): # {{{
    """Puxing PX-888K"""
    VENDOR = "Puxing"
    MODEL = "PX-888K"
    BAUD_RATE = 9600
    @classmethod
    def match_model(cls, filedata, filename): # {{{
        if len(filedata) == UPPER_READ_BOUND:
            if filedata[FILE_MAGIC[0]:FILE_MAGIC[1]] == FILE_MAGIC[2]:
                return True
            else:
                LOG.debug("The model and frequency data at 0x0c40 does not match the PX-888K")
        else:
            LOG.debug("The file size does not match.")
        return False
    # }}}
    def get_features(self): # {{{
        rf                     = chirp_common.RadioFeatures()
        rf.has_bank_index      = False
        rf.has_dtcs            = True
        rf.has_ctone           = True
        rf.has_rx_dtcs         = True
        rf.has_dtcs_polarity   = True
        rf.has_mode            = True
        rf.has_offset          = True
        rf.has_name            = True
        rf.has_bank            = False
        rf.has_bank_names      = False
        rf.has_tuning_step     = False # not on a per channel base no
        rf.has_cross           = True
        rf.has_infinite_number = False
        rf.has_nostep_tuning   = False
        rf.has_comment         = False
        rf.has_settings        = True
        if SUPPORT_NONSPLIT_DUPLEX_ONLY:
            rf.can_odd_split   = False
        else:
            rf.can_odd_split   = True

        rf.valid_modes         = MODES
        rf.valid_tmodes        = TONE_MODES
        rf.valid_duplexes      = DUPLEX_MODES
        rf.valid_bands         = BANDS
        rf.valid_skips         = SKIP_MODES
        rf.valid_power_levels  = POWER_LEVELS
        rf.valid_characters    = ASCIIPART
        rf.valid_name_length   = 6
        rf.valid_cross_modes   = CROSS_MODES
        rf.memory_bounds       = (1, 128)
        rf.valid_special_chans = SPECIAL_CHANNELS.keys()
        return rf
    # }}}
    def sync_in(self): # {{{
        self._mmap = do_download(self)
        self.process_mmap()
    # }}}
    def process_mmap(self): # {{{
        self._memobj = bitwise.parse(MEM_FORMAT, self._mmap)
    # }}}
    def sync_out(self): # {{{
        do_upload(self)
    # }}}
    def _set_sane_defaults(self, data): # {{{
        # thank's thayward!
        data.set_raw(SANE_MEMORY_DEFAULT)
    # }}}
    def _uninitialize(self, data,n): # {{{
        if isinstance(data, bitwise.arrayDataElement):
            data.set_value(b"\xff"*n)
        else:
            data.set_raw(b"\xff"*n)
    # }}}
    def _get_memory_structs(self, number): # {{{
        """
        fetch the correct data structs no matter if its regular or special channels,
        no matter if they're referred by name or channel index
        """
        index = 2501
        i = -42
        designator = 'INVALID'
        isregular = False
        iscall = False
        isvfo = False
        _data = None
        _name = None
        _present = None
        _priority = None
        if number in SPECIAL_NUMBERS.keys():
            index = number
            # speical by index
            designator = SPECIAL_NUMBERS[number]
        elif number in SPECIAL_CHANNELS.keys():
            # special by name
            index = SPECIAL_CHANNELS[number]
            designator = number
        elif number > 0:
            # regular by number
            index = number
            designator = number

        if index < 0:
            isvfo = True
            _data = self._memobj.mem.vfo_data[index+2]
        elif index == 0:
            iscall = True
            _data = self._memobj.mem.call_channel
        elif index > 0:
            isregular = True
            i = number - 1
            _data = self._memobj.mem.channel_memory.data[i]
            _name = self._memobj.mem.channel_memory.names[i].entry
            _present = self._memobj.mem.channel_memory.present[(i&0x78)|(7-(i&0x07))]
            _priority = self._memobj.mem.channel_memory.priority[(i&0x78)|(7-(i&0x07))]

        if _data == bytearray(0xff)*16:
            self._set_sane_defaults(_data)

        return index, designator, _data, _name, _present, _priority, isregular, isvfo, iscall
    # }}}
    def get_raw_memory(self, number): # {{{
        x = self._get_memory_structs(number)
        return repr(x[2])
    # }}}
    def get_memory(self, number): # {{{
        mem = chirp_common.Memory()
        index, designator, _data, _name, _present, _priority, isregular, isvfo, iscall = self._get_memory_structs(number)

        mem.number = index
        mem.extd_number = designator

        if isregular:
            if bool(_present):
                mem.empty = False
                mem.name = str(decode_ffstring(_name))
                mem.skip = SKIP_MODES[1-int(_priority)]
            else:
                mem.empty = True
                mem.name = ''
                return mem
        else:
            mem.empty = False
            mem.name = ''

        mem.freq = int(_data.rx_freq)*10
        mem.offset = int(_data.tx_freq)*10

        # only the vfo channels support duplex, memory channels operate in split mode all the time
        if isvfo:
            mem.duplex = DUPLEX_MODES[int(_data.duplex_sign)]
            if mem.duplex == '-':
                mem.offset = mem.freq - mem.offset
            elif mem.duplex == '':
                mem.offset = 0
            elif mem.duplex == '+':
                mem.offset = mem.offset - mem.freq
        else:
            if mem.freq == mem.offset:
                mem.duplex = ''
                mem.offset = 0
            elif SUPPORT_NONSPLIT_DUPLEX_ONLY or SUPPORT_SPLIT_BUT_DEFAULT_TO_NONSPLIT_ALWAYS:
                if mem.freq > mem.offset:
                    mem.offset = mem.freq - mem.offset
                    mem.duplex = '-'
                elif mem.freq < mem.offset:
                    mem.offset = mem.offset - mem.freq
                    mem.duplex = '+'
            else:
                mem.duplex = 'split'

        txtone = parse_tone(_data.tone[0])
        rxtone = parse_tone(_data.tone[1])

        chirp_common.split_tone_decode(mem, txtone, rxtone)

####################################################################################################
        if ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES:
            if bool(_data.experimental_unsupported_force_cross_mode_indicator) == False:
                if mem.tmode == 'Tone':
                    mem.cross_mode = 'Tone->'
                elif mem.tmode == 'TSQL':
                    mem.cross_mode = 'Tone->Tone'
                elif mem.tmode == 'DTCS':
                    mem.cross_mode = 'DTCS->DTCS'
                mem.tmode = 'Cross'
####################################################################################################

        mem.mode = MODES[bool(_data.modulation_width)]
        mem.power = POWER_LEVELS[_data.txpower]

        mem.extra = settings.RadioSettingGroup(
            "extra",
            "extra",
            list_setting("Busy channel lockout", "BCL", _data.bcl, BCL_MODES),
            list_setting("Swap transmit and receive frequencies", "Tx Rx freq swap", _data.txrx_reverse, OFF_ON),
            list_setting("Use compander", "Use compander", _data.compander, OFF_ON),
            list_setting("Use scrambler", "Use scrambler", _data.use_scrambler, NO_YES),
            list_setting("Scrambler selection", "Voice Scrambler", _data.scrambler_type, SCRAMBLER_MODES),
            list_setting("Automatically send ID code before and/or after transmitting", "PTT ID", _data.ptt_id_edge, PTT_ID_EDGES),
            list_setting("Optional signal before transmission, this setting overrides the PTT ID setting.", "Opt Signal", _data.opt_signal, OPTSIGN_MODES))

        if ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES:
            # override certain settings based on flags that we have set in junk areas of the memory
            # or basically, we BELIEVE this to be junk memory, hence why it's experimental
            if bool(_data.experimental_unsupported_duplex_mode_indicator) == False: # negative logic
                # if this flag is set, this means that we in the gui have set the duplex mode to something
                # the channel does not really support, such as split modes for vfo channels, and non-split
                # modes for the memory channels
                mem.duplex = DUPLEX_MODES[int(_data.duplex_sign)]
                mem.freq = int(_data.rx_freq)*10
                mem.offset = int(_data.tx_freq)*10
                if isvfo:
                    # we want split, so we have to reconstruct it from -/0/+ modes
                    if mem.duplex == '-':
                        mem.offset = mem.freq - mem.offset
                    elif mem.duplex == '':
                        mem.offset = mem.freq
                    elif mem.duplex == '+':
                        mem.offset = mem.freq + mem.offset
                    mem.duplex = 'split'
                else:
                    # we want -/0/+, so we have to reconstruct it from split modes
                    if mem.freq > mem.offset:
                        mem.offset = mem.freq - mem.offset
                        mem.duplex = '-'
                    elif mem.freq < mem.offset:
                        mem.offset = mem.offset - mem.freq
                        mem.duplex = '+'
                    else:
                        mem.offset = 0
                        mem.duplex = ''
        return mem
    # }}}
    def set_memory(self, mem): # {{{
        index, designator, _data, _name, _present, _priority, isregular, isvfo, iscall = self._get_memory_structs(mem.number)
        mem.number = index
        mem.extd_number = designator

        if mem.empty:
            if isregular:
                _present.set_value(False)
                _priority.set_value(False)
                self._uninitialize(_data, 16)
                self._uninitialize(_name, 6)
            else:
                raise errors.InvalidValueError("Can't remove CALL and/or VFO channels!")
            return

        if isregular:
            if not bool(_present):
                self._set_sane_defaults(_data)
            n = self.filter_name(mem.name)
            _name.set_value(encode_ffstring(self.filter_name(mem.name), len(_name)))
            _present.set_value(True)
            _priority.set_value(1-SKIP_MODES.index(mem.skip))

        rxf = int(mem.freq/10)
        txf = int(mem.offset/10)

        _data.rx_freq.set_value(rxf)

        if isvfo: # {{{
            # fake split modes on write, for channels
            # that do not support it, which are some
            # (the two vfo channels)
            if mem.duplex == 'split':
                for band in BANDS:
                    rb = mem.freq   in range(band[0], band[1])
                    tb = mem.offset in range(band[0], band[1])
                    if rb != tb:
                        raise errors.InvalidValueError(
                                "It is not possible to transmit/receive on different bands on VFO channels.")
                if rxf < txf:
                    _data.duplex_sign.set_value(1) # positive sign
                    _data.tx_freq.set_value(txf - rxf)
                elif rxf > txf:
                    _data.duplex_sign.set_value(2) # negative sign
                    _data.tx_freq.set_value(rxf-txf)
                else:
                    _data.duplex_sign.set_value(0)
                    _data.tx_freq.set_value(0)
            else:
                _data.duplex_sign.set_value(DUPLEX_MODES.index(mem.duplex))
                _data.tx_freq.set_value(txf)
####################################################################################################
            if ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES:
                if mem.duplex == 'split':
                    _data.experimental_unsupported_duplex_mode_indicator.set_value(0)
                else:
                    _data.experimental_unsupported_duplex_mode_indicator.set_value(1)
####################################################################################################
        # }}}
        else: # {{{
            # fake duplex modes on write, for channels
            # that do not support it, which are most
            # (all the memory channels)
            if mem.duplex == '' or mem.duplex is None:
                _data.tx_freq.set_value(rxf)
            elif mem.duplex == '+':
                _data.tx_freq.set_value(rxf + txf)
            elif mem.duplex == '-':
                _data.tx_freq.set_value(rxf - txf)
            else: # split
                _data.tx_freq.set_value(txf)
####################################################################################################
            if ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES:
                if mem.duplex != 'split':
                    _data.experimental_unsupported_duplex_mode_indicator.set_value(0)
                else:
                    _data.experimental_unsupported_duplex_mode_indicator.set_value(1)
####################################################################################################
        # }}}

        tonedata = chirp_common.split_tone_encode(mem)
        for i in range(2):
            dihl = unparse_tone(tonedata[i])
            if dihl is not None:
                _data.tone[i].digital.set_value(dihl[0])
                _data.tone[i].invert.set_value(dihl[1])
                _data.tone[i].high.set_value(dihl[2])
                _data.tone[i].low.set_value(dihl[3])
            else:
                _data.tone[i].digital.set_value(1)
                _data.tone[i].invert.set_value(1)
                _data.tone[i].high.set_value(0x3f)
                _data.tone[i].low.set_value(0xff)
####################################################################################################
        if ENABLE_DANGEROUS_EXPERIMENTAL_FEATURES:
            if mem.tmode == 'Cross' and mem.cross_mode in ['Tone->', 'Tone->Tone', 'DTCS->DTCS']:
                _data.experimental_unsupported_force_cross_mode_indicator.set_value(0)
            else:
                _data.experimental_unsupported_force_cross_mode_indicator.set_value(1)
####################################################################################################

        if str(mem.power) == 'High':
            _data.txpower.set_value(1)
        else:
            _data.txpower = 0
        _data.modulation_width.set_value(MODES.index(mem.mode))
    # }}}
    def get_settings(self): # {{{
        _model = self._memobj.mem.model_information
        _settings = self._memobj.mem.opt_settings
        _ptt_id_data = self._memobj.mem.ptt_id_data
        _msk_settings = self._memobj.mem.msk_settings
        _dtmf_settings = self._memobj.mem.dtmf_settings
        _5tone_settings = self._memobj.mem.five_tone_settings
        _broadcast = self._memobj.mem.fm_radio

        # for safety reasons we are setting these as read-only
        model_unit_settings = [ # {{{
            integer_setting("vhflo", "VHF lower bound", _model.band_limits[0].lower_freq, 134, 176, int_from_mem=lambda x:int(int(x)/10), mem_from_int=None),
            integer_setting("vhfhi", "VHF upper bound", _model.band_limits[0].upper_freq, 134, 176, int_from_mem=lambda x:int(int(x)/10), mem_from_int=None),
            integer_setting("uhflo", "UHF lower bound", _model.band_limits[1].lower_freq, 400, 480, int_from_mem=lambda x:int(int(x)/10), mem_from_int=None),
            integer_setting("uhfhi", "UHF upper bound", _model.band_limits[1].upper_freq, 400, 480, int_from_mem=lambda x:int(int(x)/10), mem_from_int=None),
            ff_string_setting("model", "Model string", _model.model_string, 0, 6)
        # }}}
        ]
        for s in model_unit_settings:
            s.value.set_mutable(False)
        model_unit_settings.append(ff_string_setting("info", "Unit Information", self._memobj.mem.radio_information_string, 0, 16))
        radio_channel_settings = [ # {{{
            list_setting("vfostep", "VFO step size", _settings.vfo_step, VFO_STRIDE),
            list_setting("abwatch", "Main watch", _settings.main_watch, AB),
            list_setting("singledualwatch", "Watch mode", _settings.main_watch, WATCH_MODES),
            list_setting("amode", "A mode", _settings.workmode_a, AB_MODES),
            list_setting("bmode", "B mode", _settings.workmode_b, AB_MODES),
            integer_setting("achan", "A channel index", _settings.channel_a, 1, 128, int_from_mem=lambda i:i+1, mem_from_int=lambda i:i-1),
            integer_setting("bchan", "B channel index", _settings.channel_b, 1, 128, int_from_mem=lambda i:i+1, mem_from_int=lambda i:i-1),
            integer_setting("pchan", "Priority channel index", _settings.priority_channel, 1, 128, int_from_mem=lambda i:i+1, mem_from_int=lambda i:i-1),
            list_setting("cactive", "Call channel active?", _settings.call_channel_active, NO_YES),
            list_setting("scanm", "Scan mode", _settings.scan_mode, SCAN_MODES),
            list_setting("swait", "Wait time", _settings.wait_time, WAIT_TIMES),
            list_setting("tail", "Relay without disable tail (?)", _settings.relay_without_disable_tail, NO_YES), # it is unclear what this option does, possibly squelch tail elimination?
            list_setting("batsav", "Battery saving mode", _settings.battery_save, OFF_ON),
            ]
        # }}}
        interface_settings = [ # {{{
            list_setting("sidehold", "Side button hold action", _settings.side_button_hold_mode, BUTTON_MODES),
            list_setting("sideclick", "Side button click action", _settings.side_button_click_mode, BUTTON_MODES),
            list_setting("bootmt", "Boot message type", _settings.boot_message_mode, BOOT_MESSAGE_TYPES),
            ff_string_setting("bootm", "Boot message", _settings.boot_message, 0, 6),
            list_setting("beep", "Key beep", _settings.key_beep, OFF_ON),
            list_setting("talkback", "Menu talkback", _settings.voice_announce, TALKBACK),
            list_setting("sidetone", "DTMF sidetone", _settings.dtmf_sidetone, OFF_ON),
            list_setting("roger", "Roger beep", _settings.use_roger_beep, ROGER_BEEP),
            list_setting("backlm", "Backlight mode", _settings.backlight_mode, BACKLIGHT_MODES),
            list_setting("backlc", "Backlight color", _settings.backlight_color, BACKLIGHT_COLORS),
            integer_setting("squelch", "Squelch level", _settings.squelch_level, 0, 9),
            list_setting("voxg", "Vox gain", _settings.vox_gain, VOX_GAIN),
            list_setting("voxd", "Vox delay", _settings.vox_delay, VOX_DELAYS),
            list_setting("txal", "Trinsmit time alarm", _settings.tx_timeout, TRANSMIT_ALARMS),
            ]
        # }}}
        data_general_settings = [ # {{{
            list_setting("disptt", "Display PTT ID", _settings.dis_ptt_id, NO_YES),
            list_setting("pttidt", "PTT ID signal type", _settings.ptt_id_type, DATA_MODES)
            ]
        # }}}
        data_msk_settings = [ # {{{
            ff_string_setting("bot", "MSK PTT ID (BOT)", _ptt_id_data[0].entry, 0, 6, autowrite=False),
            ff_string_setting("eot", "MSK PTT ID (EOT)", _ptt_id_data[1].entry, 0, 6, autowrite=False),
            ff_string_setting("id", "MSK ID code", _msk_settings.id_code, 0, 4, charset=HEXADECIMAL),
            list_setting("mskr", "MSK reverse", _settings.msk_reverse, NO_YES)
            ]
        # }}}
        data_dtmf_settings = [ # {{{
            dtmf_string_setting("bot", "DTMF PTT ID (BOT)", _ptt_id_data[0].entry, _ptt_id_data[0].length, 0, 8, autowrite=False),
            dtmf_string_setting("eot", "DTMF PTT ID (EOT)", _ptt_id_data[1].entry, _ptt_id_data[1].length, 0, 8, autowrite=False),
            dtmf_string_setting("id", "DTMF ID code", _dtmf_settings.id_code, _dtmf_settings.id_code_length, 3, 8),

            integer_setting("time", "Digit time (ms)", _dtmf_settings.timing.digit_length, 50, 200, step=10, int_from_mem=lambda x:x*10, mem_from_int=lambda x:int(x/10)),
            integer_setting("pause", "Inter digit time (ms)", _dtmf_settings.timing.digit_length, 50, 200, step=10, int_from_mem=lambda x:x*10, mem_from_int=lambda x:int(x/10)),
            integer_setting("time1", "First digit time (ms)", _dtmf_settings.timing.digit_length, 50, 200, step=10, int_from_mem=lambda x:x*10, mem_from_int=lambda x:int(x/10)),
            integer_setting("pause1", "First digit delay (ms)", _dtmf_settings.timing.digit_length, 100, 1000, step=50, int_from_mem=lambda x:x*50, mem_from_int=lambda x:int(x/50)),

            list_setting("arst", "Auto reset time", _dtmf_settings.reset_time, TONE_RESET_TIME),
            list_setting("grp", "Group code", _dtmf_settings.group_code, DTMF_GROUPS),
            dtmf_string_setting("stunt", "TX Stun code", _dtmf_settings.tx_stun_code, _dtmf_settings.tx_stun_code_length, 3, 8),
            dtmf_string_setting("cstunt", "TX Stun cancel code", _dtmf_settings.cancel_tx_stun_code, _dtmf_settings.cancel_tx_stun_code_length, 3, 8),
            dtmf_string_setting("stunrt", "RX/TX Stun code", _dtmf_settings.rxtx_stun_code, _dtmf_settings.rxtx_stun_code_length, 3, 8),
            dtmf_string_setting("cstunrt", "RX/TX Stun cancel code", _dtmf_settings.cancel_rxtx_stun_code, _dtmf_settings.cancel_rxtx_stun_code_length, 3, 8),
            list_setting("altr", "Alert/Transpond", _dtmf_settings.alert_transpond, DTMF_ALERT_TRANSPOND),
            ]
        # }}}
        data_5tone_settings = [ # {{{
            five_tone_string_setting("bot", "5-Tone PTT ID (BOT)", _ptt_id_data[0].entry, autowrite=False),
            five_tone_string_setting("eot", "5-Tone PTT ID (EOT)", _ptt_id_data[1].entry, autowrite=False),
            five_tone_string_setting("id", "5-tone ID code", _5tone_settings.id_code),
            list_setting("arst", "Auto reset time", _5tone_settings.reset_time, TONE_RESET_TIME),
            five_tone_string_setting("stunt", "TX Stun code", _5tone_settings.tx_stun_code),
            five_tone_string_setting("cstunt", "TX Stun cancel code", _5tone_settings.cancel_tx_stun_code),
            five_tone_string_setting("stunrt", "RX/TX Stun code", _5tone_settings.rxtx_stun_code),
            five_tone_string_setting("cstunrt", "RX/TX Stun cancel code", _5tone_settings.cancel_rxtx_stun_code),
            list_setting("altr", "Alert/Transpond", _5tone_settings.alert_transpond, FIVE_TONE_ALERT_TRANSPOND),
            list_setting("std", "5-Tone standard", _5tone_settings.tone_standard, FIVE_TONE_STANDARDS),
            ]
        for i in range(4):
            s = ['z1', 'z2', 'c1', 'ct'][i]
            l = FIVE_TONE_STANDARDS[i]
            data_5tone_settings.append(
                settings.RadioSettingGroup(
                    s, '%s settings'%l,
                    integer_setting("%speriod"%s, "%s Period (ms)"%l, _5tone_settings.tone_settings[i].period, 20, 255),
                    list_setting("%sgrp"%s, "%s Group code"%l, _5tone_settings.tone_settings[i].group_code, HEXADECIMAL),
                    list_setting("%srpt"%s, "%s Repeat code"%l, _5tone_settings.tone_settings[i].repeat_code, HEXADECIMAL)))
        # }}}
        data_msk_call_list = []
        data_dtmf_call_list = []
        data_5tone_call_list = []
        for i in range(9): # {{{
            j = i+1
            data_msk_call_list.append(
                ff_string_setting("ce%d"%i, "MSK call entry %d"%j, _msk_settings.phone_book[i].entry, 0, 4, charset=HEXADECIMAL))

            data_dtmf_call_list.append(
                dtmf_string_setting("ce%d"%i, "DTMF call entry %d"%j, _dtmf_settings.phone_book[i].entry, _dtmf_settings.phone_book[i].length, 0, 10))

            data_5tone_call_list.append(
                five_tone_string_setting("ce%d"%i, "5-Tone call entry %d"%j, _5tone_settings.phone_book[i].entry)),
        # }}}
        data_settings = data_general_settings
        data_settings.extend([ # {{{
                settings.RadioSettingGroup("MSK_s", "MSK settings", *data_msk_settings),
                settings.RadioSettingGroup("MSK_c", "MSK call list", *data_msk_call_list),
                settings.RadioSettingGroup("DTMF_s", "DTMF settings", *data_dtmf_settings),
                settings.RadioSettingGroup("DTMF_c", "DTMF call list", *data_dtmf_call_list),
                settings.RadioSettingGroup("5-Tone_s", "5-tone settings", *data_5tone_settings),
                settings.RadioSettingGroup("5-Tone_c", "5-tone call list", *data_5tone_call_list)
            ])
        # }}}
        locking_settings = [ # {{{
            list_setting("autolock", "Automatic timed keypad lock",  _settings.auto_keylock, OFF_ON),
            list_setting("lockon", "Current status of keypad lock",  _settings.keypad_lock, INACTIVE_ACTIVE),
            list_setting("nokeypad", "Disable keypad frequency entry, menu access etc",  _settings.allow_keypad, YES_NO),
            list_setting("rxstun", "Disable receiver functionality (rx stun)",  _settings.rx_stun, NO_YES),
            list_setting("txstun", "Disable transmitter functionality (tx stun)",  _settings.tx_stun, NO_YES),
            ]
        # }}}

        broadcast_settings = [ # {{{
            list_setting("band", "Frequency interval", _broadcast.receive_range, BFM_BANDS),
            list_setting("stride", "VFO step", _broadcast.channel_stepping, BFM_STRIDE),
            frequency_setting("vfo", "VFO frequency (MHz)", _broadcast.vfo_freq)
        ]
        # }}}
        for i in range(10): # {{{
            broadcast_settings.append(
                frequency_setting("bcd%d"%i, "Memory %d frequency"%i, _broadcast.memory[i].entry))
                #settings.RadioSetting("bc%d"%i, "Channel memory %d (MHz)"%i,
                #    settings.RadioSettingValueString(0, 100, mf)))
        # }}}

        return settings.RadioSettings( # {{{
            settings.RadioSettingGroup("model", "Model/Unit information/settings", *model_unit_settings),
            settings.RadioSettingGroup("radio", "Radio/Channel settings", *radio_channel_settings),
            settings.RadioSettingGroup("interface", "Interface", *interface_settings),
            settings.RadioSettingGroup("data", "Data", *data_settings),
            settings.RadioSettingGroup("locking", "Locking", *locking_settings),
            settings.RadioSettingGroup("broadcast", "Broadcast FM radio settings", *broadcast_settings)
        )
        # }}}
    # }}}
    def set_settings(self, s, parent=''): # {{{

        ds = sbyn(s, 'data')
        idts = sbyn(ds, 'pttidt').value
        idtv = idts.get_value()
        cs = sbyn(ds, idtv+'_s')
        tss = [ sbyn(cs, e).value for e in ['bot', 'eot'] ]

        for ts in tss:
            ts.write_mem()
    # }}}
# }}}
