# WSL → Windows Bluetooth Serial Device Bridge

## Problem

WSL cannot access Windows Bluetooth virtual COM ports (/dev/ttyS* returns Input/output error 5).
USB cameras are fine (WSLg forwards them) — this is specific to Bluetooth serial profiles.

## Solution: Three Approaches

### Approach 1 — Windows py.exe from WSL (simplest, for quick tests)

```bash
/mnt/c/Windows/py.exe -c "import serial; ser = serial.Serial('COM3', 57600)"
```

Useful for one-off reads and debugging. Not suitable for persistent streaming
because the process exits when done — but fine for verifying connectivity:

```python
import serial, time
ser = serial.Serial('COM3', 57600, timeout=2)
for _ in range(100):
    b = ser.read(10)
    print(b.hex())
ser.close()
```

### Approach 2 — Long-lived Windows Bridge Script (recommended for production)

A Python script that runs on the Windows side, reads the serial port continuously,
and forwards data to the WSL backend via WebSocket.

**Bridge script structure (`scripts/tgam_bridge.py`):**

```python
# -*- coding: utf-8 -*-
"""Windows-side EEG bridge: reads TGAM COM port → WebSocket → WSL backend."""
import asyncio
import json
import serial
import websockets

COM_PORT = "COM3"
BAUD = 57600
WSL_WS_URL = "ws://localhost:8765/eeg"  # WSL backend WebSocket endpoint

class TGAMBridge:
    def __init__(self):
        self.ser = serial.Serial(COM_PORT, BAUD, timeout=0.1)
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect(WSL_WS_URL)

    async def read_and_send(self):
        """Read one TGAM packet and forward to WSL."""
        while True:
            b = self.ser.read(1)
            if not b or b[0] != 0xAA:
                continue
            # ... TGAM protocol parsing from eeg.py ...
            data = {"attention": att, "meditation": med, "delta": delta, ...}
            await self.ws.send(json.dumps(data))

    async def run(self):
        await self.connect()
        await self.read_and_send()

asyncio.run(TGAMBridge().run())
```

**WSL-side WebSocket handler (in backend):**

```python
from fastapi import WebSocket
from collections import deque

eeg_buffer = deque(maxlen=50)

@app.websocket("/eeg")
async def eeg_bridge(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_json()
        eeg_buffer.append(data)
```

### Approach 3 — Named Pipe / File (not recommended for real-time)

Windows writes to a file, WSL reads it. Too slow and race-condition-prone for
real-time game control (target < 100ms latency). Only suitable for data logging.

## Finding the Right COM Port

```bash
# From WSL — list all /dev/ttyS*
ls /dev/ttyS*

# From Windows — check Device Manager for "NeuroSky MindWave" or "Bluetooth virtual COM"
# COM{N} → WSL /dev/ttyS{N-1} (COM3 → /dev/ttyS2)
```

## Verifying TGAM Protocol Works (Diagnostic Script)

Run this from WSL or Windows terminal to confirm the TGAM device is sending valid data:

```bash
/mnt/c/Windows/py.exe -c "
import serial, time, collections

data = collections.deque(maxlen=5000)
attention = collections.deque(maxlen=21)
meditation = collections.deque(maxlen=21)
eeg = {n: collections.deque(maxlen=21) for n in ['delta','theta','low_alpha','high_alpha','low_beta','high_beta','low_gamma','mid_gamma']}

def parse_big(pkt):
    if len(pkt) < 36 or pkt[:3] != b'\\xaa\\xaa ':
        return False
    payload, cs = pkt[3:35], pkt[35]
    if (~sum(payload) & 0xFF) != cs:
        return False
    i = 0
    while i < len(payload):
        c = payload[i]
        if c == 0x02: sq = payload[i+1]; i += 2
        elif c == 0x83 and payload[i+1] == 24:
            b = i+2
            for j, n in enumerate(['delta','theta','low_alpha','high_alpha','low_beta','high_beta','low_gamma','mid_gamma']):
                val = (payload[b+j*3]<<16)|(payload[b+j*3+1]<<8)|payload[b+j*3+2]
                eeg[n].append(val)
            i += 26
        elif c == 0x04: attention.append(payload[i+1]); i += 2
        elif c == 0x05: meditation.append(payload[i+1]); i += 2
        else: i += 1
    return True

ser = serial.Serial('COM3', 57600, timeout=1)
start = time.time()
pkts = 0
while time.time() - start < 10:
    if ser.read(1) == b'\\xaa' and ser.read(1) == b'\\xaa':
        plen = ord(ser.read(1))
        if plen == 0x20:
            pkt = b'\\xaa\\xaa\\x20' + ser.read(32) + ser.read(1)
            if parse_big(pkt): pkts += 1
ser.close()
print(f'{pkts} big packets, {len(attention)} attention, {len(eeg[\"delta\"])} band samples')
print(f'Latest att/med: {list(attention)[-3:]}, {list(meditation)[-3:]}')
"
```

**Expected output with headset OFF (but Bluetooth paired):**
- Raw data: ~5000 samples in 10s → ✅ TGAM streaming raw wave
- ~5 big packets → ✅ protocol parsing working
- Attention/Meditation: all 0 → ⚠️ Normal (eSense outputs 0 when signal_quality=200)
- EEG bands: all non-zero → ✅ spectrum data received

**Expected output with headset ON (good contact):**
- Signal quality: < 50
- Attention/Meditation: fluctuating values 0-100
- EEG bands: realistic proportions (delta/theta dominate gamma)

## Known Limitations

| Issue | Symptom | Fix |
|-------|---------|-----|
| COM port busy | PermissionError on open | Close other apps (old demo, Arduino IDE, etc.) |
| Signal quality 200 | No head contact | Put on the headset, check electrode contact |
| All eSense values 0 | Headset not worn or not paired | Re-pair Bluetooth, wait for signal quality to drop below 50 |
| WSL IP changes | Bridge can't connect | Use `wsl hostname -I` to get WSL IP; configure in bridge script |
| Port conflict with Hermes Windows-MCP | Port 8000 used by Hermes gateway | Use a different port (e.g. 8010) — check with `ss -tlnp \| grep PORT` |
| Hermes gateway intercepts requests | curl returns 401 with "Missing authorization header" | Test via Python httpx from within WSL, which bypasses the gateway. Browser access works from Windows side. |
