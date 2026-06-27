# Programmatic Icon Generation for Tauri

## RGBA PNG (required by `generate_context!()`)

```python
import struct, zlib

def rgba_png(size, r, g, b, a=255):
    def chunk(ct, data):
        c = ct + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    raw = b''
    for _ in range(size):
        raw += b'\x00' + bytes([r, g, b, a]) * size
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw)) +
            chunk(b'IEND', b''))

# Generate all required sizes
for s in [32, 128, 256]:
    open(f'icon-{s}.png', 'wb').write(rgba_png(s, 88, 166, 255))
```

**Note**: `color_type=6` (RGBA) is required. `color_type=2` (RGB) causes `generate_context!()` to panic with "icon is not RGBA".

## Multi-size ICO (required by Windows Resource Compiler)

```python
import struct

def make_ico(png_sizes):
    """png_sizes: list of (size, png_bytes) tuples"""
    n = len(png_sizes)
    header = struct.pack('<HHH', 0, 1, n)
    offset = 6 + 16 * n
    entries = b''
    data = b''
    for size, png in png_sizes:
        w = size if size < 256 else 0
        h = size if size < 256 else 0
        entries += struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(png), offset)
        data += png
        offset += len(png)
    open('icon.ico', 'wb').write(header + entries + data)

# Usage: include 32px and 128px PNGs
png32 = open('icon-32.png', 'rb').read()
png128 = open('icon-128.png', 'rb').read()
make_ico([(32, png32), (128, png128)])
```

Without valid ICO: `error RC2175: resource file icon.ico is not in 3.00 format`.
