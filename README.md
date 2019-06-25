disfv1
======

Disassembler for Spin Semi FV-1

Copyright (C) 2019 Nathan Fraser

A simple disassembler for the Spin Semiconductor FV-1 DSP. This
disassembler will convert a FV-1 binary program file into strict
FV-1 assembler statements, suitable for use with asfv1 and the
Spin IDE.

REQUIREMENTS:
-------------

- Python \>= 3

INSTALLATION:
-------------

- pip3 install disfv1

USAGE:
------

  disfv1 input.bin output.asm

OVERVIEW:
---------

disfv1 is based on information in the FV-1 datasheet and AN0001 "Basics
of the LFOs in the FV-1". It disassembles FV-1 machine code into strict
assembler compatible with asfv1.

- This disassembler converts a single 128 instruction DSP program binary
  and outputs a corresponding assembly representation.

- Skip offsets are automatically replaced with labels. To suppress labels
  and instead get the offset, use command line option -r (--relative).

- By default, the source is assumed to be a single program. To offset
  into a bank file, use the command line option -p (--program) to
  choose an alternate program.

- Invalid instructions are disassembled as 'raw' instructions, to
  replace them with 'nop' use command line option -s (--suppressraw).

LINKS:
------

- FV-1 assembler: <https://github.com/ndf-zz/asfv1>

- Spin FV-1 website: <http://spinsemi.com/products.html>

- Datasheet: <http://spinsemi.com/Products/datasheets/spn1001/FV-1.pdf>

- AN0001: <http://spinsemi.com/Products/appnotes/spn1001/AN-0001.pdf>
