#
# disfv1: FV-1 Disassembler
# Copyright (C) 2019-2021 Nathan Fraser
#
# A disassembler for the Spin Semiconductor FV-1 DSP.

# Python2 > 2.6 support
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Imports
import argparse
import sys
import struct
from decimal import Decimal

# Constants
VERSION = '1.0.6'
PROGLEN = 128
MINPREC = Decimal('0.0')

# Bit Masks
M1 = 0x01
M2 = 0x03
M5 = 0x1f
M6 = 0x3f
M8 = 0xff
M9 = 0x1ff
M11 = 0x7ff
M14 = 0x3fff
M15 = 0x7fff
M16 = 0xffff
M24 = 0xffffff
M27 = 0x7ffffff
M32 = 0xffffffff

def quiet(msg):
    pass

def warning(msg):
    print(msg, file=sys.stderr)

def error(msg):
    print(msg, file=sys.stderr)

# Machine instruction table
op_tbl = {
        # opcode: [mnemonic, (arglen,left shift), ...]
        0x00: ['RDA', (M15,5),(M11,21)],
        0x01: ['RMPA', (M11,21)],
        0x02: ['WRA', (M15,5),(M11,21)],
        0x03: ['WRAP', (M15,5),(M11,21)],
        0x04: ['RDAX', (M6,5),(M16,16)],
        0x05: ['RDFX', (M6,5),(M16,16)],	# and LDAX
        0x06: ['WRAX', (M6,5),(M16,16)],
        0x07: ['WRHX', (M6,5),(M16,16)],
        0x08: ['WRLX', (M6,5),(M16,16)],
        0x09: ['MAXX', (M6,5),(M16,16)],	# and ABSA
        0x0A: ['MULX', (M6,5)],
        0x0B: ['LOG', (M16,16),(M11,5)],
        0x0C: ['EXP', (M16,16),(M11,5)],
        0x0D: ['SOF', (M16,16),(M11,5)],
        0x0E: ['AND', (M24,8)],			# and CLR
        0x0F: ['OR', (M24,8)],
        0x10: ['XOR', (M24,8)],			# and NOT
        0x11: ['SKP', (M5,27),(M6,21)],		# and NOP
        0x12: ['WLDX', (M32,0)],		# WLDS/WLDR
        0x13: ['JAM', (M2,6)],
        0x14: ['CHO', (M2,30),(M2,21),(M6,24),(M16,5)],
        'WLDS': ['WLDS', (M1,29),(M9,20),(M15,5)],
        'WLDR': ['WLDR', (M2,29),(M16,13),(M2,5)],
}

class fv1deparse(object):
    def __init__(self, source=None, relative=False, 
                       nopraw=False, wfunc=None):
        self.program = []
        self.listing = ''
        self.dowarn = wfunc
        self.relskip = relative
        self.nopraw = nopraw
        self.source = source
        self.jmptbl = { # jump table for skips
        }
        self.rampamp = {
		0x0:	'4096',
		0x1:	'2048',
		0x2:	'1024',
		0x3:	'512',
        }
        self.chotype = {
		0x0:	'rda',
		0x1:	'rda',	# override invalid chotype
		0x2:	'sof',
		0x3:	'rdal',
        }
        self.chosel = {
		0x0:	'SIN0',
		0x1:	'SIN1',
		0x2:	'RMP0',
		0x3:	'RMP1',
        }
        self.choflags = {
		0x00:	'SIN',
		0x01:	'COS',
		0x02:	'REG',
		0x04:	'COMPC',
		0x08:	'COMPA',
		0x10:	'RPTR2',
		0x20:	'NA',
        }
        self.skipflags = {
		0x10:	'RUN',
		0x08:	'ZRC',
		0x04:	'ZRO',
		0x02:	'GEZ',
		0x01:	'NEG',
        }
        self.regs = {
		0x00:	'SIN0_RATE',
		0x01:	'SIN0_RANGE',
		0x02:	'SIN1_RATE',
		0x03:	'SIN1_RANGE',
		0x04:	'RMP0_RATE',
		0x05:	'RMP0_RANGE',
		0x06:	'RMP1_RATE',
		0x07:	'RMP1_RANGE',
		0x10:	'POT0',
		0x11:	'POT1',
		0x12:	'POT2',
		0x14:	'ADCL',
		0x15:	'ADCR',
		0x16:	'DACL',
		0x17:	'DACR',
		0x18:	'ADDR_PTR',
		0x20:	'REG0',
		0x21:	'REG1',
		0x22:	'REG2',
		0x23:	'REG3',
		0x24:	'REG4',
		0x25:	'REG5',
		0x26:	'REG6',
		0x27:	'REG7',
		0x28:	'REG8',
		0x29:	'REG9',
		0x2a:	'REG10',
		0x2b:	'REG11',
		0x2c:	'REG12',
		0x2d:	'REG13',
		0x2e:	'REG14',
		0x2f:	'REG15',
		0x30:	'REG16',
		0x31:	'REG17',
		0x32:	'REG18',
		0x33:	'REG19',
		0x34:	'REG20',
		0x35:	'REG21',
		0x36:	'REG22',
		0x37:	'REG23',
		0x38:	'REG24',
		0x39:	'REG25',
		0x3a:	'REG26',
		0x3b:	'REG27',
		0x3c:	'REG28',
		0x3d:	'REG29',
		0x3e:	'REG30',
		0x3f:	'REG31',
        }

    def __reg__(self, reg):
        """Convert a register argument to text."""
        ret = '{0:#04x}'.format(reg)
        if reg in self.regs:
            ret = self.regs[reg]
        return ret

    def __s1_14__(self, val):
        """Convert and return a S1.14 real as text."""
        return str(MINPREC + Decimal(((val&((1<<15)-1))-(val&(1<<15)))/(1<<14)))

    def __s1_9__(self, val):
        """Convert and return a S1.9 real as text."""
        return str(MINPREC + Decimal(((val&((1<<10)-1))-(val&(1<<10)))/(1<<9)))

    def __s4_6__(self, val):
        """Convert and return a S4.6 real as text."""
        return str(MINPREC + Decimal(((val&((1<<10)-1))-(val&(1<<10)))/(1<<6)))

    def __s_10__(self, val):
        """Convert and return a S.10 real as text."""
        return str(MINPREC + Decimal(((val&((1<<10)-1))-(val&(1<<10)))/(1<<10)))

    def __i_15__(self, val):
        """Convert and return a signed integer as text."""
        return str(MINPREC + Decimal((val&((1<<15)-1))-(val&(1<<15))))

    def __s_15__(self, val):
        """Convert and return a S.15 real as text."""
        return str(MINPREC + Decimal(((val&((1<<15)-1))-(val&(1<<15)))/(1<<15)))

    def __s_23__(self, val):
        """Convert and return a S.23 real as text."""
        return str(MINPREC + Decimal(((val&((1<<23)-1))-(val&(1<<23)))/(1<<23)))

    def __regmult__(self, inst, address):
        """Extract a register/multiplier instruction: op REG,k"""
        reg = inst['args'][0]
        mult = inst['args'][1]
        if inst['mnemonic'] == 'rdfx' and mult == 0:
            inst['mnemonic'] = 'ldax'
            inst['argstring'] = self.__reg__(reg)
            inst['comment'] = 'reg:{0:#04x}'.format(reg)
        elif inst['mnemonic'] == 'maxx' and mult == 0 and reg == 0:
            inst['mnemonic'] = 'absa'
            inst['comment'] = 'maxx 0,0'
        else:
            inst['comment'] = 'reg:{0:#04x} k:{1:#06x}'.format(reg, mult)
            inst['argstring'] = ','.join([ self.__reg__(reg),
                                       self.__s1_14__(mult) ])

    def __cho__(self, inst, address):
        """Extract a CHO instruction."""
        typeval = inst['args'][0]
        typestr = str(typeval)
        if typeval in self.chotype:
            typestr = self.chotype[typeval]
        sel = inst['args'][1]
        selstr = str(sel)
        if sel in self.chosel:
            selstr = self.chosel[sel]
        flags = inst['args'][2]
        flagv = []
        if flags == 0x00:
            flagv.append('SIN')
        for flag in sorted(self.choflags):
            if flags&flag:
                flagv.append(self.choflags[flag])
        flagstr = '|'.join(flagv)
        d = inst['args'][3]
        dstr = None
        if typestr == 'rdal':
            inst['argstring'] = ','.join(['rdal',selstr,flagstr])
            inst['comment'] = 't:{0:#03x} n:{1:#03x} c:{2:#04x}'.format(
                typeval, sel, flags)
        elif typestr == 'rda':
            dstr = str(d)
            inst['argstring'] = ','.join(['rda',selstr,flagstr,dstr])
            inst['comment'] = 't:{0:#03x} n:{1:#03x} c:{2:#04x} addr:{3:#06x}'.format(
                typeval, sel, flags, d)
        elif typestr == 'sof':
            dstr = self.__s_15__(d)
            inst['argstring'] = ','.join(['sof',selstr,flagstr,dstr])
            inst['comment'] = 't:{0:#03x} n:{1:#03x} c:{2:#04x} d:{3:#06x}'.format(
                typeval, sel, flags, d)
        else:
            dstr = str(d)
            inst['argstring'] = ','.join([typestr,selstr,flagstr,dstr])
            inst['comment'] = 't:{0:#03x} n:{1:#03x} c:{2:#04x} addr:{3:#06x}'.format(
                typeval, sel, flags, d)

    def __jam__(self, inst, address):
        """Extract a JAM instruction."""
        lfo = inst['args'][0]|0x2
        lfostr = self.chosel[lfo]
        inst['comment'] = 'lfo:{0:#03x}'.format(lfo)
        inst['argstring'] = lfostr

    def __delayop__(self, inst, address):
        """Extract a delay/multiplier instruction: op delay,k"""
        offset = inst['args'][0]
        mult = inst['args'][1]
        inst['comment'] = 'del:{0:#06x} k:{1:#05x}'.format(offset, mult)
        inst['argstring'] = ','.join([ str(offset), 
                                       self.__s1_9__(mult) ])

    def __mulx__(self, inst, address):
        """Extract a mulx instruction."""
        reg = inst['args'][0]
        inst['comment'] = 'reg:{0:#04x}'.format(reg)
        inst['argstring'] = self.__reg__(reg)

    def __rmpa__(self, inst, address):
        """Extract a rmpa instruction."""
        mult = inst['args'][0]
        inst['comment'] = 'k:{0:#05x}'.format(mult)
        inst['argstring'] = self.__s1_9__(mult)

    def __scaleoft__(self, inst, address):
        """Extract a scale/offset instruction: op k,const"""
        mult = inst['args'][0]
        offset = inst['args'][1]
        inst['comment'] = 'k:{0:#06x} const:{1:#05x}'.format(mult,offset)
        ostr = self.__s_10__(offset)
        inst['argstring'] = ','.join([ self.__s1_14__(mult), ostr ])

    def __bitop__(self, inst, address):
        """Extract a bitwise accumulator operation: op mask"""
        mask = inst['args'][0]
        if inst['mnemonic'] == 'and' and mask == 0:
            inst['mnemonic'] = 'clr'
            inst['comment'] = 'and 0'
        elif inst['mnemonic'] == 'xor' and mask == 0xffffff:
            inst['mnemonic'] = 'not'
            inst['comment'] = 'xor 0xffffff'
        else:
            inst['comment'] = 'val:'.format(mask) + self.__s_23__(mask)
            inst['argstring'] = '{0:#08x}'.format(mask)

    def __wldx__(self, inst, address):
        """Extract wldr and wlds instructions."""
        if inst['command'] & 0x40000000:
            # WLDR
            ni = self.__decode__(inst['command'], override='WLDR')
            inst['args'] = ni['args']
            inst['mnemonic'] = 'wldr'
            lfo = inst['args'][0]&0x1
            freq = inst['args'][1]
            amp = inst['args'][2]
            ampstr = '{0:01x}'.format(amp)
            if amp in self.rampamp:
                ampstr = self.rampamp[amp]
            inst['argstring'] = ','.join(['RMP'+str(lfo),
                  self.__i_15__(freq), ampstr ])
            inst['comment'] = 'lfo:{0:#03x} f:{1:#06x} a:{2:#03x}'.format(
                 lfo, freq, amp)
        else:
            # WLDS
            ni = self.__decode__(inst['command'], override='WLDS')
            inst['args'] = ni['args']
            inst['mnemonic'] = 'wlds'
            lfo = inst['args'][0]&0x1
            freq = inst['args'][1]
            amp = inst['args'][2]
            inst['argstring'] = ','.join(['SIN'+str(lfo),
                  str(freq), str(amp) ])
            inst['comment'] = 'lfo:{0:#03x} f:{1:#05x} a:{2:#06x}'.format(
                 lfo, freq, amp)

    def __skp__(self, inst, address):
        """Extract a skp operation."""
        flags = inst['args'][0]
        offset = inst['args'][1]
        targetstr = '{0:d}'.format(offset)
        if not self.relskip:
            taddr = address+offset+1
            targetstr = 'addr{0:02x}'.format(taddr)
            self.jmptbl[taddr] = targetstr
            inst['target'] = targetstr
        inst['comment'] = 'flags:{0:#04x} offset:{1:#04x}'.format(
                                flags, offset)
        flagv = []
        if flags == 0:
            flagv.append('0')
        else:
            for flag in self.skipflags:
                if flags&flag:
                    flagv.append(self.skipflags[flag])
        inst['argstring'] = ','.join([
              '|'.join(flagv),
              targetstr ])

    def __raw__(self, inst, address):
        """Extract a raw data instruction."""
        val = inst['args'][0]
        if self.nopraw:
            inst['mnemonic'] = 'nop'
        else:
            inst['argstring'] = '{0:#010x}'.format(val)
        inst['comment'] = repr(struct.pack('>I',val))

    def __fixinst__(self, inst, address):
        """Examine instruction and extract an assembly equivalent."""
        if inst['mnemonic'] == 'skp':
            if inst['args'][0] == 0 and inst['args'][1] == 0:
                inst['mnemonic'] = 'nop'
                inst['comment'] = 'skp 0,0'
            else:
                self.__skp__(inst, address)
        elif inst['mnemonic'] in ['rdax', 'wrax', 'maxx',
                                  'rdfx', 'wrlx', 'wrhx',]:
            self.__regmult__(inst, address)
        elif inst['mnemonic'] in ['mulx',]:
            self.__mulx__(inst, address)
        elif inst['mnemonic'] in ['rda', 'wra', 'wrap',]:
            self.__delayop__(inst, address)
        elif inst['mnemonic'] in ['log', 'exp', 'sof']:
            self.__scaleoft__(inst, address)
        elif inst['mnemonic'] in ['rmpa',]:
            self.__rmpa__(inst, address)
        elif inst['mnemonic'] in ['jam',]:
            self.__jam__(inst, address)
        elif inst['mnemonic'] in ['cho',]:
            self.__cho__(inst, address)
        elif inst['mnemonic'] in ['wldx',]:
            self.__wldx__(inst, address)
        elif inst['mnemonic'] in ['and', 'or', 'xor',]:
            self.__bitop__(inst, address)
        elif inst['mnemonic'] == 'raw':
            self.__raw__(inst, address)
        else:
            self.dowarn('info: Unknown mnemonic: '
                         + repr(inst['mnemonic'])
                         + ' raw:{0:#010x} at address:{1:#04x}'.format(
                              inst['command'], address))
        if address in self.jmptbl:
            inst['label'] = self.jmptbl[address]

    def __decode__(self, command, override=None):
        """Decode raw command into opcode and arguments."""
        opcode = command&M5
        ret = {'opcode':opcode,
               'mnemonic':None,
               'args':[],
               'command':command,
               'label':None,
               'comment':None,
               'argstring':None,
               'target':None,
              }
        if override is not None:
            opcode = override
        if opcode in op_tbl:
            inst = op_tbl[opcode]
            ret['mnemonic'] = inst[0].lower()
            for arg in inst[1:]:
                ret['args'].append((command>>arg[1])&arg[0])
        else:
            ret['mnemonic'] = 'raw'
            ret['args'].append(command)
        return ret

    def deparse(self):
        """Disassemble input."""
        plen = len(self.source)
        oft = 0
        while oft+3 < plen:
            rawinst = struct.unpack_from('>I', self.source, oft)[0]
            self.program.append(self.__decode__(rawinst))
            oft += 4
        cnt = 0
        for i in self.program:
            self.__fixinst__(i, cnt)
            cnt += 1
        cnt = len(self.program)-1
        while cnt > 0:
            if self.program[cnt]['mnemonic'] in ['nop', 'skp']:
                del(self.program[cnt])
            else:
                break
            cnt -= 1
        for l in self.program:
            label = ''
            if l['label'] is not None:
                label = l['label']+':'
            mnemonic = l['mnemonic']
            argstring = ''
            if l['argstring'] is not None:
                argstring = l['argstring']
            comment = ''
            if l['comment'] is not None:
                comment = '; ' + l['comment']
            self.listing += '\t'.join([
                     label, mnemonic, argstring.ljust(23), comment
                          ]) + '\n'
        for j in sorted(self.jmptbl):
            if j >= len(self.program):
                self.listing += self.jmptbl[j] + ':\n'
        self.dowarn('info: Read {} instructions.'.format(len(self.program)))

def main():
    parser = argparse.ArgumentParser(
                description='Disassemble a single FV-1 DSP program.')
    parser.add_argument('infile',
                        type=argparse.FileType('rb'),
                        help='binary program file',
                        default=sys.stdin) 
    parser.add_argument('outfile',
                        nargs='?',
                        help='assembly program output file',
                        default=sys.stdout) 
    parser.add_argument('-v', '--version',
                        action='version',
                        help='print version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('-q', '--quiet',
                        action='store_true',
                        help='suppress warnings')
    parser.add_argument('-r', '--relative',
                        action='store_true',
                        help='use relative skip targets')
    parser.add_argument('-s', '--suppressraw',
                        action='store_true',
                        help="convert invalid/raw statements into nop")
    parser.add_argument('-p',
                        help='program number',
                        type=int, choices=list(range(0,8)))
    args = parser.parse_args()
    dowarn = warning
    if args.quiet:
        dowarn = quiet
    dowarn('FV-1 Disassembler v' + VERSION)
    dowarn('info: Reading input from ' + args.infile.name)
    inbuf = args.infile.read(8*4*PROGLEN)
    oft = 0
    if args.p is not None:
        oft = args.p * (PROGLEN*4)
        dowarn('info: Reading from program {0} at offset {1:#06x}'.format(
               args.p, oft))
    fp = fv1deparse(inbuf[oft:oft+(PROGLEN*4)],
                    relative=args.relative, nopraw=args.suppressraw,
                    wfunc=dowarn)
    fp.deparse()
    ofile = None
    if args.outfile is sys.stdout:
        ofile = args.outfile
    else:
        try:
            ofile = open(args.outfile, 'w')
        except Exception as e:
            error('error: writing output: ' + str(e))
            sys.exit(-1)
    ofile.write(fp.listing)
    ofile.close()
if __name__ == '__main__':
    main()
