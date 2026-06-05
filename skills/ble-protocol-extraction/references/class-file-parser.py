#!/usr/bin/env python3
"""
Java .class file constant pool parser for BLE protocol extraction.
Extracts string constants, integer constants, UUIDs, and field/method references
from compiled Java class files — no JDK/jadx required.

Usage:
    python3 class-file-parser.py CmdConstants.class
    python3 class-file-parser.py *.class  # batch mode
"""

import struct, sys, re
from pathlib import Path

def parse_class_file(path):
    """Parse a Java .class file and extract all constant pool entries."""
    with open(path, 'rb') as f:
        data = f.read()

    magic = struct.unpack('>I', data[0:4])[0]
    if magic != 0xCAFEBABE:
        print(f"  Not a valid class file: magic=0x{magic:08x}")
        return None

    minor = struct.unpack('>H', data[4:6])[0]
    major = struct.unpack('>H', data[6:8])[0]
    pos = 8
    cp_count = struct.unpack('>H', data[pos:pos+2])[0]
    pos += 2

    cp = []
    i = 1
    while i < cp_count:
        tag = data[pos]
        pos += 1
        if tag == 1:  # CONSTANT_Utf8
            length = struct.unpack('>H', data[pos:pos+2])[0]
            pos += 2
            value = data[pos:pos+length].decode('utf-8', errors='replace')
            pos += length
            cp.append(('Utf8', value))
        elif tag == 3:  # CONSTANT_Integer
            val = struct.unpack('>i', data[pos:pos+4])[0]
            pos += 4
            cp.append(('Integer', val))
        elif tag == 4:  # CONSTANT_Float
            val = struct.unpack('>f', data[pos:pos+4])[0]
            pos += 4
            cp.append(('Float', val))
        elif tag == 5:  # CONSTANT_Long (takes 2 slots)
            val = struct.unpack('>q', data[pos:pos+8])[0]
            pos += 8
            cp.append(('Long', val))
            i += 1
        elif tag == 6:  # CONSTANT_Double (takes 2 slots)
            val = struct.unpack('>d', data[pos:pos+8])[0]
            pos += 8
            cp.append(('Double', val))
            i += 1
        elif tag == 7:  # CONSTANT_Class
            idx = struct.unpack('>H', data[pos:pos+2])[0]
            pos += 2
            cp.append(('Class', idx))
        elif tag == 8:  # CONSTANT_String
            idx = struct.unpack('>H', data[pos:pos+2])[0]
            pos += 2
            cp.append(('String', idx))
        elif tag == 9:  # CONSTANT_Fieldref
            ci = struct.unpack('>H', data[pos:pos+2])[0]
            ni = struct.unpack('>H', data[pos+2:pos+4])[0]
            pos += 4
            cp.append(('Fieldref', ci, ni))
        elif tag == 10:  # CONSTANT_Methodref
            ci = struct.unpack('>H', data[pos:pos+2])[0]
            ni = struct.unpack('>H', data[pos+2:pos+4])[0]
            pos += 4
            cp.append(('Methodref', ci, ni))
        elif tag == 11:  # CONSTANT_InterfaceMethodref
            ci = struct.unpack('>H', data[pos:pos+2])[0]
            ni = struct.unpack('>H', data[pos+2:pos+4])[0]
            pos += 4
            cp.append(('InterfaceMethodref', ci, ni))
        elif tag == 12:  # CONSTANT_NameAndType
            ni = struct.unpack('>H', data[pos:pos+2])[0]
            di = struct.unpack('>H', data[pos+2:pos+4])[0]
            pos += 4
            cp.append(('NameAndType', ni, di))
        elif tag == 15:  # MethodHandle
            pos += 3
            cp.append(('MethodHandle',))
        elif tag == 16:  # MethodType
            pos += 2
            cp.append(('MethodType',))
        elif tag in (17, 18):  # Dynamic/InvokeDynamic
            pos += 4
            cp.append(('Dynamic',))
        elif tag in (19, 20):  # Module/Package
            pos += 2
            cp.append(('Module',))
        else:
            print(f"  WARNING: Unknown tag {tag} at offset {pos-1}, stopping")
            break
        i += 1

    def resolve(idx):
        if idx <= 0 or idx >= len(cp):
            return f"<bad:{idx}>"
        e = cp[idx-1]
        if e[0] == 'Utf8':
            return e[1]
        elif e[0] == 'Class':
            return resolve(e[1])
        elif e[0] == 'String':
            return resolve(e[1])
        elif e[0] == 'NameAndType':
            return f"{resolve(e[1])}:{resolve(e[2])}"
        elif e[0] in ('Fieldref', 'Methodref', 'InterfaceMethodref'):
            return f"{resolve(e[1])}.{resolve(e[2])}"
        return f"<{e[0]}>"

    return cp, resolve, minor, major


def analyze(path):
    """Analyze a .class file and print BLE-relevant findings."""
    result = parse_class_file(path)
    if result is None:
        return
    cp, resolve, minor, major = result

    name = Path(path).stem
    print(f"{'='*70}")
    print(f"CLASS: {name}  (Java {major}.{minor})")
    print(f"{'='*70}")

    # Extract BLE UUIDs
    uuids = []
    for entry in cp:
        if entry[0] == 'Utf8' and '-' in entry[1] and len(entry[1]) == 36:
            uuids.append(entry[1])
    if uuids:
        print(f"\n▶ BLE UUIDs:")
        for u in uuids:
            print(f"    {u}")

    # Extract command constants and protocol strings
    interesting = []
    for i, entry in enumerate(cp):
        if entry[0] == 'Utf8':
            val = entry[1]
            # BLE-relevant patterns
            if any(kw in val.upper() for kw in ['UUID', 'CMD_', 'BLE_KEY', 'DATA_TRANSFER',
                                                  'SERVICE', 'CHARACTERISTIC', 'PROTOCOL',
                                                  'START', '_KEY', '_ID', 'AGREEMENT',
                                                  'CONTROL', 'RESULT', 'SYNC', 'POWER',
                                                  'REMIND', 'FACTORY', 'RECOVERY']):
                interesting.append(f"    [{i+1}] {val}")
    if interesting:
        print(f"\n▶ Protocol strings:")
        for s in interesting:
            print(s)

    # Extract integer constants (potential byte-level markers)
    ints = []
    for i, entry in enumerate(cp):
        if entry[0] == 'Integer':
            val = entry[1]
            unsigned = val & 0xFFFFFFFF
            if 0 < unsigned <= 0xFFFF:  # filter out large/negative as unsigned
                ints.append(f"    [{i+1}] {val:5d} = 0x{unsigned:04x}")
    if ints:
        print(f"\n▶ Integer constants:")
        for s in ints:
            print(s)

    # Extract field references to understand constant wiring
    fields = []
    for entry in cp:
        if entry[0] == 'Fieldref':
            fields.append(f"    Field: {resolve(entry[1])} -> {resolve(entry[2])}")
    if fields:
        print(f"\n▶ Field references:")
        for s in fields[:20]:
            print(s)
        if len(fields) > 20:
            print(f"    ... ({len(fields)} total, showing first 20)")

    print()


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if Path(arg).is_file() and arg.endswith('.class'):
            analyze(arg)
        else:
            print(f"Skipping {arg} (not a .class file)")
