# TGAM (ThinkGear ASIC Module) 协议速查

## 物理层

| 参数 | 值 |
|------|-----|
| 波特率 | 57600 |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验 | None |
| 电压 | 3.3V TTL |
| 接口 | UART (Rx/Tx) |

## 数据包格式

```
[0xAA] [0xAA] [PLENGTH] [PAYLOAD...] [CHECKSUM]
```

### 包类型

| PLENGTH | 类型 | 载荷说明 |
|----------|------|----------|
| 0x04 | Raw 小包 | 0x80 0x02 + int16 big-endian |
| 0x20 | 大包 (32B) | eSense + EEG Powers + 信号质量 |
| 其他 | 未知 | 跳过 payload + checksum |

### 校验和

```python
def verify(payload: bytes, checksum: int) -> bool:
    return (~sum(payload) & 0xFF) == checksum
```

## 大包 (0x20) 内部结构

Payload 32 bytes, TLV (Type-Length-Value) 格式：

### 信号质量 — Code 0x02
- Value: 0=优秀, 200=无连接

### 专注度 — Code 0x04
- Value: 0-100 (eSense 内建算法)

### 放松度 — Code 0x05
- Value: 0-100 (eSense 内建算法)

### 8频段EEG Power — Code 0x83
- Length: 24 bytes

| 偏移 | 频段 | 频率范围 |
|------|------|----------|
| +0 | Delta | 0.5–2.75 Hz |
| +3 | Theta | 3.0–5.0 Hz |
| +6 | Low Alpha | 6.0–9.5 Hz |
| +9 | High Alpha | 10.0–12.5 Hz |
| +12 | Low Beta | 13.0–19.5 Hz |
| +15 | High Beta | 20.0–25.5 Hz |
| +18 | Low Gamma | 26.0–36.5 Hz |
| +21 | Mid Gamma | 37.0–44.0 Hz |

## Raw 数据解析

```
0x80 0x02 [HIGH] [LOW]  →  int16 big-endian
```

```python
raw = (high << 8) | low
if raw > 32768: raw -= 65536  # signed
```

## 眨眼检测（非芯片级）

基于 delta 波突变率 + raw 波峰值：

```python
def detect_blink(delta_history, raw_data):
    if len(delta_history) < 2: return False
    ratio = delta_history[-1] / (delta_history[-2] + 1)
    recent = raw_data[-100:] if len(raw_data) >= 100 else raw_data
    peak = max(recent, default=0)
    return ratio > 1.5 and peak > 1500
```
