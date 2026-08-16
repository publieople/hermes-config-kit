# Windows → WSL EEG Bridge

将 NeuroSky TGAM 脑电数据从 Windows 转发到 WSL。

## 核心问题

- WSL (`/dev/ttyS{N-1}`) → COM3 蓝牙虚拟串口 → `(5, 'Input/output error')`
- Windows py.exe 从 WSL 调用 → `PermissionError(13, '拒绝访问')`（端口被其他Windows进程占用）
- **解决方案**: Windows 侧独立运行桥接脚本

## 桥接脚本模板

```python
# eeg_bridge.py — 在 Windows 侧运行
# python eeg_bridge.py --com COM3 --ws ws://localhost:8765/ws/eeg
# 依赖: pip install pyserial websockets

import serial, asyncio, json, sys, argparse, time
import websockets

SYNC = bytes([0xAA, 0xAA])

class TGAMReader:
    def __init__(self, port="COM3", baud=57600):
        self.ser = serial.Serial(port, baud, timeout=1)
        self.buf = bytearray()
    
    def read(self):
        while True:
            b = self.ser.read(1)
            if not b: continue
            self.buf.append(b[0])
            if len(self.buf) >= 3 and bytes(self.buf[-3:-1]) == SYNC:
                plen = self.buf[-1]
                if plen == 0x04:
                    return self._read_raw()
                elif plen == 0x20:
                    return self._read_big()
                else:
                    self.buf.clear()
                    self.ser.read(plen + 1)
    
    def _read_raw(self):
        payload = self.ser.read(4)
        ck = self.ser.read(1)
        if len(payload) == 4 and len(ck) == 1:
            if payload[0] == 0x80 and payload[1] == 0x02:
                raw = (payload[2] << 8) | payload[3]
                if raw > 32768: raw -= 65536
                self.buf.clear()
                return {"type": "raw", "value": raw}
        self.buf.clear()
        return None
    
    def _read_big(self):
        payload = self.ser.read(32)
        ck = self.ser.read(1)
        if len(payload) == 32 and len(ck) == 1:
            packet = bytes([0xAA, 0xAA, 0x20]) + payload + ck
            if (~sum(payload) & 0xFF) == ck[0]:
                data = {"type": "eeg", "timestamp": time.time()}
                i = 0
                while i < len(payload):
                    code = payload[i]
                    if code == 0x02:
                        data["signal_quality"] = payload[i+1]; i += 2
                    elif code == 0x04:
                        data["attention"] = payload[i+1]; i += 2
                    elif code == 0x05:
                        data["meditation"] = payload[i+1]; i += 2
                    elif code == 0x83 and payload[i+1] == 24:
                        b = i + 2
                        bands = ["delta","theta","low_alpha","high_alpha",
                                 "low_beta","high_beta","low_gamma","mid_gamma"]
                        for j, band in enumerate(bands):
                            val = (payload[b+j*3] << 16) | (payload[b+j*3+1] << 8) | payload[b+j*3+2]
                            data[band] = val
                        i += 2 + 24
                    else:
                        i += 1
                self.buf.clear()
                return data
        self.buf.clear()
        return None

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--com", default="COM3")
    parser.add_argument("--ws", default="ws://localhost:8765/ws/eeg")
    parser.add_argument("--baud", type=int, default=57600)
    args = parser.parse_args()
    
    reader = TGAMReader(args.com, args.baud)
    print(f"Connected to {args.com}")
    
    async with websockets.connect(args.ws) as ws:
        while True:
            data = reader.read()
            if data:
                await ws.send(json.dumps(data))

if __name__ == "__main__":
    asyncio.run(main())
```

## 启动顺序

1. 启动 WSL FastAPI 后端
2. 等待后端打印 "WebSocket server ready"
3. 在 Windows 侧运行 `python eeg_bridge.py`
4. 检查 WebSocket 日志确认连接成功

## 排查

- `PermissionError` → `netstat -ano | findstr COM3` → `taskkill /PID <pid> /F`
- 桥接连不上 WSL → 检查防火墙（WSL 使用虚拟网络，通常无需额外配置）
- 数据全是 signal_quality=200 → 头戴没开/没配对
