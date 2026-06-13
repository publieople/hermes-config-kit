---
name: bci-game-development
description: Build brain-computer interface (BCI) games using NeuroSky TGAM EEG + camera gaze tracking. Covers TGAM protocol, MediaPipe Iris, Windows→WSL bridge, fusion engines (late fusion), real-time game server architecture.
version: 1.0.0
metadata:
  hermes:
    tags: [bci, eeg, gaze, brain-game, tgam, neurosky, mediapipe, gaming]
    related_skills: [spec-kit-greenfield-init, ui-ux-pro-max]
---

# BCI Game Development

## Overview

Hybrid BCI (hBCI) game platform using dual-modal input:
- **EEG (NeuroSky TGAM)**: attention (fire), meditation (shield), blink detection
- **Camera (MediaPipe Iris)**: gaze direction (ship movement)
- **Late Fusion**: independent streams merge at decision layer

## Architecture

```
┌── Windows ───────────────────┐        ┌── WSL ───────────────────────────┐
│                              │        │                                  │
│  EEG Bridge (bridge.py)      │  TCP   │  FastAPI Backend                 │
│  ├── serial COM{N} @ 57600  │───────→│  ├── Fusion Engine               │
│  └── WebSocket → WSL        │  :8765 │  ├── MediaPipe Gaze Tracker      │
│                              │        │  ├── WebSocket → Browser         │
│  Camera (OpenCV via WSLg)   │        │  └── Static Files (Vite build)   │
│  └── → WSL directly         │        │                                  │
│                              │        │  Browser → localhost:8000        │
└──────────────────────────────┘        └──────────────────────────────────┘
```

## When to Use

**Use when:**
- Building any game/app controlled by NeuroSky TGAM EEG
- Combining eye tracking + brainwave input
- Working with Windows EEG devices that need bridging to WSL
- Creating Canvas-based games with real-time biophysical input

**Do NOT use when:**
- Pure keyboard/mouse game (use general game dev skills instead)
- Using different EEG hardware (OpenBCI, Emotiv — different protocols)
- Game is turn-based or doesn't need real-time sensor fusion

## Prerequisites

- NeuroSky TGAM module (MindWave) on Windows COM port
- Camera (webcam) accessible from WSL
- `uv` package manager
- Python 3.11+

Need help choosing hardware? See `references/device-selection.md` for a full comparison of EEG, VR, and combined BCI hardware (international and 国产 options). Key comparison axes: channels, VR integration, signal quality, price, and China availability.

## Critical: Windows ↔ WSL EEG Bridge

**WSL CANNOT access Bluetooth virtual COM ports** (e.g. NeuroSky's COM3 via Bluetooth dongle). All `/dev/ttyS{N-1}` attempts return `(5, 'Input/output error')`. Even Windows `py.exe` called from WSL gets `PermissionError` if the port is occupied on the Windows side.

**Solution:** A lightweight Python bridge runs on Windows side, reads COM port, and pushes data via TCP/WebSocket to WSL.

### Bridge Architecture

```
Windows: python bridge.py --com COM3 --host localhost --port 8765
                                            ↓ TCP/WebSocket
WSL: FastAPI server listening on :8765 for EEG data
```

### Bridge Script Pattern (Windows-only file)

```python
# eeg_bridge.py — Run on Windows side
import serial, asyncio, json, time
import websockets

COM = "COM3"  # or pass via --com argument
WS_TARGET = "ws://localhost:8765/ws/eeg"  # WSL FastAPI endpoint

class TGAMReader:
    """TGAM serial parser (3-byte big-endian EEG powers)"""
    SYNC = bytes([0xAA, 0xAA])
    
    def __init__(self, port, baud=57600):
        self.ser = serial.Serial(port, baud, timeout=1)
        self.buf = bytearray()
    
    def read_packet(self):
        while True:
            b = self.ser.read(1)
            if not b: continue
            self.buf.append(b[0])
            if len(self.buf) >= 3 and self.buf[-2:] == self.SYNC:
                plen = self.buf[-1]
                if plen == 0x04:  # raw data
                    payload = self.ser.read(4)
                    ck = self.ser.read(1)
                    if sum(payload) & 0xFF == (~ck[0]) & 0xFF:
                        self.buf.clear()
                        return self._parse_raw(payload)
                elif plen == 0x20:  # big packet
                    payload = self.ser.read(32)
                    ck = self.ser.read(1)
                    packet = bytes([0xAA, 0xAA, 0x20]) + payload + ck
                    if self._verify_checksum(packet):
                        self.buf.clear()
                        return self._parse_big(payload)
```

### Pitfalls

- **Bluetooth COM ports appear/disappear** — always check `serial.tools.list_ports.comports()` 
- **Signal quality = 200** means no headset connection (not a read error)
- **Rate**: eSense updates ~1Hz, raw EEG ~512Hz, big packets (powers) ~1Hz
- **WSL startup order**: Start the WSL backend BEFORE the bridge, so WebSocket connect succeeds
- **Port already open**: If `PermissionError`, kill the Windows process holding the port: `netstat -ano | findstr COM3` → `taskkill /PID <pid> /F`

## TGAM Protocol Quick Reference

| Packet | Header | Payload | Key Fields |
|--------|--------|---------|------------|
| Raw data | AA AA 04 | 0x80 0x02 + int16 | Raw wave amplitude |
| Big packet | AA AA 20 | 32 bytes | eSense + 8 EEG powers |
| Signal quality | (inside big) | 0x02 + byte | 0=good, 200=disconnected |
| Attention | (inside big) | 0x04 + byte | eSense 0-100 |
| Meditation | (inside big) | 0x05 + byte | eSense 0-100 |
| EEG Power | (inside big) | 0x83 + 24 bytes | 8 bands × 3 bytes big-endian |

### EEG Power Bands (3-byte big-endian each)

| Index | Band | Freq Range |
|-------|------|------------|
| 0 | Delta | 0.5–2.75 Hz |
| 1 | Theta | 3–5 Hz |
| 2 | Low Alpha | 6–9.5 Hz |
| 3 | High Alpha | 10–12.5 Hz |
| 4 | Low Beta | 13–19.5 Hz |
| 5 | High Beta | 20–25.5 Hz |
| 6 | Low Gamma | 26–36.5 Hz |
| 7 | Mid Gamma | 37–44 Hz |

### Checksum

```python
def verify(packet):
    payload = packet[3:35]  # skip AA AA 20
    checksum = packet[35]
    return (~sum(payload) & 0xFF) == checksum
```

## eSense Processing (Engine Layer)

TGAM's eSense (Attention/Meditation) is chip-level — no extra FFT needed. The engine layer handles:

```python
class EEGEngine:
    def __init__(self, window_size=5):
        self.attention = deque(maxlen=window_size)
        self.meditation = deque(maxlen=window_size)
        self.threshold_up = 60      # hysteresis for fire/shield ON
        self.threshold_down = 45    # hysteresis for fire/shield OFF
        self.fire_active = False
        self.shield_active = False
    
    def feed(self, att, med, signal_quality):
        if signal_quality >= 200:
            return  # skip bad data
        self.attention.append(att)
        self.meditation.append(med)
        
        smoothed_att = sum(self.attention) / len(self.attention)
        smoothed_med = sum(self.meditation) / len(self.meditation)
        
        # Hysteresis thresholding
        if self.fire_active:
            self.fire_active = smoothed_att > self.threshold_down
        else:
            self.fire_active = smoothed_att > self.threshold_up
        
        return smoothed_att, smoothed_med, self.fire_active
```

## MediaPipe Gaze Tracking

```python
import cv2, mediapipe as mp

class GazeTracker:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True)
        self.cap = cv2.VideoCapture(0)
        
        # Left eye landmarks: 33 (outer), 133 (inner), 468 (iris)
        # Right eye landmarks: 362 (outer), 263 (inner), 473 (iris)
    
    def get_gaze(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return None
        
        h, w = frame.shape[:2]
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Left iris center
        l_iris = (int(landmarks[468].x * w), int(landmarks[468].y * h))
        l_outer = (landmarks[33].x, landmarks[33].y)
        l_inner = (landmarks[133].x, landmarks[133].y)
        
        # Normalize iris position between eye corners
        gaze_x = (landmarks[468].x - l_outer.x) / (l_inner.x - l_outer.x)
        gaze_x = (gaze_x - 0.5) * 2  # normalize to [-1, 1]
        
        return {"gaze_x": gaze_x, "gaze_y": ..., "screen_x": ..., "screen_y": ...}
```

### Pitfalls

- **refine_landmarks=True** is critical — without it, iris landmarks (468, 473) are not tracked
- **First 10 frames** are warm-up — discard or they return None
- **Glasses** reduce accuracy to ~89% (vs 97% without)
- **Lighting**: frontal, diffused illumination. Avoid strong backlight or side shadows
- Kalman filter recommended for gaze jitter reduction

## Fusion Strategy

**Late fusion** — independent processing, combined at decision layer:

| Input | Signal → Game Action |
|-------|---------------------|
| Gaze (x, y) | Ship position (continuous smooth lerp) |
| Attention > 60+ | Auto-fire (hysteresis 60↑/45↓) |
| Meditation > 60+ | Shield active (hysteresis 60↑/45↓) |
| Gaze + Attention | Target lock (gaze stays on enemy > 0.5s while attention > 60) |
| Double blink (EEG delta) | Menu/pause toggle |
| Gaze blink (EAR < 0.2) | (Optional) confirm action |

**Fallback modes** (graceful degradation):
- No EEG → gaze-only mode (keyboard fires)
- No camera → EEG-only mode (attention moves cursor)
- Both offline → full keyboard mode

## Game Server (FastAPI + WebSocket)

### WebSocket Protocol

**Server → Client** (data push, ~33ms interval):
```json
{"type": "control", "position": {"x": 0.5, "y": 0.3}, "fire": true, "shield": false}
{"type": "eeg", "attention": 72, "meditation": 31, "signal_quality": 0, "delta": 12345, ...}
{"type": "gaze", "gaze_x": 0.2, "gaze_y": -0.1, "screen_x": 640, "screen_y": 360}
{"type": "status", "eeg_connected": true, "camera_connected": true, "mode": "fusion"}
```

**Client → Server** (commands):
```json
{"command": "calibrate", "mode": "gaze"}
{"command": "start" | "pause" | "resume" | "restart"}
```

## Frontend Game (Vite + TypeScript Canvas)

### Game Engine Structure

```typescript
// Engine: requestAnimationFrame loop, delta-time physics
// Entities: Ship, Enemy, Bullet, StarField, Explosion
// Physics: circle-circle collision
// Input: WS input adapter + keyboard fallback
// HUD: HTML overlay (score, attention bar, meditation bar, shield indicator)
```

### WebSocket Client Pattern

```typescript
class WsClient {
  private ws: WebSocket;
  private reconnectAttempt = 0;
  private maxReconnect = 10;
  set onmessage(cb: ((msg: ServerMessage) => void) | undefined) {
    this.events.onMessage = cb;
  }
  private _scheduleReconnect() {
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 30000);
    setTimeout(() => this.connect(), delay);
  }
}
```

## Verification Checklist

- [ ] TGAM reads: signal_quality < 200, attention/meditation non-zero
- [ ] Camera reads: face landmarks detected, iris center tracked
- [ ] WebSocket: eeg, gaze, control messages all flowing at expected rates
- [ ] Fusion: fire triggers at attention > 60, shield at meditation > 60
- [ ] Game: Canvas renders at 60fps, ship follows gaze smoothly
- [ ] Fallback: all three modes (gaze-only, eeg-only, keyboard) work
- [ ] Bridge: Windows→WSL reconnects on WSL restart
