# disfv1

Disassembler for Spin Semi FV-1

Copyright (C) 2019 Nathan Fraser

A simple disassembler for the Spin Semiconductor FV-1 DSP. This
disassembler will convert a FV-1 binary program file into strict
FV-1 assembler statements, suitable for use with asfv1 and the
Spin IDE.


## Requirements

- Python \>= 3


## Installation

	$ pip3 install disfv1

## Usage

	$ disfv1 input.bin output.asm
	
	$ disfv1 -h
	usage: disfv1 [-h] [-v] [-q] [-r] [-s] [-p {0,1,2,3,4,5,6,7}] infile [outfile]
	
	Disassemble a single FV-1 DSP program.
	
	positional arguments:
	  infile                binary program file
	  outfile               assembly program output file
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -v, --version         print version
	  -q, --quiet           suppress warnings
	  -r, --relative        use relative skip targets
	  -s, --suppressraw     convert invalid/raw statements into nop
	  -p {0,1,2,3,4,5,6,7}  program number


## Overview

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

## Example

	$ disfv1 example.bin
	info: Reading input from example.bin
	info: Read 9 instructions.
		skp	RUN,addr03             	; flags:0x10 offset:0x02
		ldax	POT0                   	; reg:0x10
		wrax	REG0,0.0               	; reg:0x20 k:0x0000
	addr03:	ldax	ADCL                   	; reg:0x14
		mulx	REG0                   	; reg:0x20
		wra	0,0.0                  	; del:0x0000 k:0x000
		rda	9830,0.5               	; del:0x2666 k:0x100
		rda	19660,0.5              	; del:0x4ccc k:0x100
		wrax	DACL,0.0               	; reg:0x16 k:0x0000

## Links

- FV-1 assembler: <https://github.com/ndf-zz/asfv1>
- Spin FV-1 website: <http://spinsemi.com/products.html>
- Datasheet: <http://spinsemi.com/Products/datasheets/spn1001/FV-1.pdf>
- AN0001: <http://spinsemi.com/Products/appnotes/spn1001/AN-0001.pdf>
