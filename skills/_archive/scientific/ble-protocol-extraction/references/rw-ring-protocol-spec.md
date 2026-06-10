# RW BLE Smart Ring — Protocol Reference

Recovered from `blesdk-release-250811.aar` class file analysis + mini-program protocol PDF.

## BLE GATT UUIDs

| Role | 16-bit UUID | Full UUID |
|------|------------|-----------|
| Service | `0BC0` | `00000BC0-0000-1000-8000-00805F9B34FB` |
| Write (App→Ring) | `0BC1` | `00000BC1-0000-1000-8000-00805F9B34FB` |
| Notify (Ring→App) | `0BC2` | `00000BC2-0000-1000-8000-00805F9B34FB` |
| OTA Service | `FF00` | `0000FF00-0000-1000-8000-00805F9B34FB` |
| OTA Characteristic | `FF01` | `0000FF01-0000-1000-8000-00805F9B34FB` |

**Also found in AAR (SDK variant):**
- `0000fee7-0000-1000-8000-00805f9b34fb` (standard wearable service)
- `0000b002-...` (write char), `0000b003-...` (notify char), `00002902-...` (CCC desc)
- `0000a00a-...` / `0000ae00-...` (alternate services)

## Packet Format (Little-Endian?)

```
Offset  Size  Field      Description
0       1     Header     Fixed 0xC6
1       1     Flag       0x01 = App→Device, 0x11 = Device→App
2       2     Length     Data section length (big-endian uint16)
4       2     CRC16      CRC-16 of Data section
6       N     Data       Protocol payload
```

## Data Payload Format

```
Offset  Size  Field      Description
0       1     CMD        Function group
1       1     Key        Sub-function
2       1     KeyFlag    0x00=write, 0x10=read, 0x20=add, 0x30=delete
3       N     Value      Per-command payload
```

## CRC16 Algorithm

Table-based CRC-16 (custom polynomial). Validate with known examples.

```python
CRC_TABLE = [0x72ae, 0x2cd6, 0x3d6c, 0x4ae1, 0x6784, 0x18be, 0x4823, 0x0029,
             0x01eb, 0x26e9, 0x41bb, 0x5af1, 0x6df1, 0x1649, 0x5f90, 0x6952,
             0x0099, 0x0f3e, 0x390c, 0x7e87, 0x153c, 0x12db, 0x2ea6, 0x0bb3,
             0x54de, 0x1547, 0x4db7, 0x4d06, 0x491c, 0x440d, 0x305e, 0x0124,
             0x26a6, 0x428b, 0x66bb, 0x6443, 0x4dc8, 0x074d, 0x2d12, 0x39b3,
             0x1e1f, 0x3b25, 0x1238, 0x4509, 0x767d, 0x7a5a, 0x5d03, 0x701f,
             0x323b, 0x4e45, 0x7ff5, 0x7f96, 0x6bfc, 0x63cb, 0x1ad4, 0x6e5d,
             0x0732, 0x56ae, 0x0bdb, 0x301c, 0x030a, 0x6b89, 0x260d, 0x2213,
             0x5cfd, 0x6b36, 0x5878, 0x4b40, 0x22ee, 0x2350, 0x759a, 0x0120,
             0x0ddc, 0x5f49, 0x797d, 0x3a9e, 0x3bf6, 0x5f32, 0x1a49, 0x3e12,
             0x1cd0, 0x1366, 0x2e40, 0x4944, 0x4df2, 0x5e14, 0x314f, 0x4cad,
             0x5422, 0x15a1, 0x2c3b, 0x6032, 0x7eb7, 0x4230, 0x66c4, 0x366b,
             0x73da, 0x121f, 0x798b, 0x12e1, 0x409d, 0x5991, 0x0822, 0x3ef6,
             0x7049, 0x139d, 0x5772, 0x7bb9, 0x0902, 0x3699, 0x26ca, 0x58b0,
             0x4080, 0x13e9, 0x3cd5, 0x6899, 0x16c5, 0x187e, 0x4a80, 0x692c,
             0x3cd6, 0x5c67, 0x60bf, 0x5753, 0x48cc, 0x23c9, 0x33ea, 0x5db2,
             0x0d66, 0x368e, 0x54dc, 0x422d, 0x047e, 0x6ad6, 0x2f14, 0x0fbf,
             0x288f, 0x6c69, 0x2fff, 0x3c61, 0x2c49, 0x4657, 0x75ef, 0x7983,
             0x6172, 0x1916, 0x489c, 0x5e9d, 0x261e, 0x7dd1, 0x22cd, 0x3a61,
             0x0677, 0x494a, 0x7f4f, 0x0384, 0x71f0, 0x401d, 0x32e6, 0x6b72,
             0x0fc9, 0x6bcb, 0x1953, 0x542c, 0x5039, 0x6be8, 0x18d7, 0x4402,
             0x5dd5, 0x11f4, 0x2b0c, 0x249e, 0x7874, 0x2833, 0x5f1e, 0x0e12,
             0x07cf, 0x0035, 0x127e, 0x2059, 0x5fa4, 0x4cd4, 0x5a9f, 0x6ad4,
             0x3a2d, 0x0e90, 0x01d3, 0x46cf, 0x0ecc, 0x1af4, 0x6d22, 0x6732,
             0x252a, 0x591d, 0x19d9, 0x37e6, 0x0975, 0x458f, 0x57d3, 0x6048,
             0x7b44, 0x4087, 0x1481, 0x5078, 0x442b, 0x49f7, 0x1dc0, 0x37e5,
             0x7fbe, 0x3a8d, 0x7f61, 0x16d4, 0x2b00, 0x1850, 0x765f, 0x590e,
             0x251f, 0x7282, 0x0633, 0x773b, 0x3807, 0x0c15, 0x5005, 0x0c7b,
             0x3bb1, 0x39ce, 0x4d54, 0x5064, 0x19da, 0x3492, 0x6270, 0x1d18,
             0x3004, 0x486a, 0x5c46, 0x4ff8, 0x6a15, 0x6d69, 0x513e, 0x4c85,
             0x5968, 0x4d67, 0x182f, 0x1f16, 0x73d9, 0x470e, 0x5e73, 0x1796,
             0x5876, 0x4f68, 0x4e57, 0x5ed0, 0x0a4a, 0x3f4a, 0x2cf7, 0x4ad4]

def calc_crc16(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc = (crc >> 8) ^ CRC_TABLE[(crc ^ byte) & 0xff]
    return crc
```

## Command Reference

### Setup & Control

| Action | Packet (hex) | Description |
|--------|-------------|-------------|
| **Login** | `C60100035FC0` `030220` | Login device (ring: optional) |
| **Set timezone** | `c60100046165` `02020020` | Timezone = 32 (China, 8×4) |
| **Set time** | `c6010009xxxx` `020100190a1d101732` | Yr(25=2025),M(10),D(29),H(16),M(23),S(50) |
| **Get firmware** | `c601000340ed` `020410` | → 0.2.2, square, 240×296 |
| **Get battery** | `c60100034045` `020310` | → 1 byte (0x1e = 30%) |
| **Set user info** | `c601000exxxx` `02060000001a00002a4300008242` | Metric, M, age 26, 173cm, 65.0kg |
| **Get MAC** | `c601000307dc` `020510` | → 6 bytes reversed |
| **Find device** | `c601000413E8` `02340001` | Device lights up |
| **Resting health** | `c60100032283` `028110` | → HR(66), HRV(50), SpO2(98) |

### Single Health Tests (CMD=0x06, Key=0x09)

| DataType | Start Command | Stop Command |
|----------|--------------|--------------|
| **Heart rate** (0x0503) | `c60100067efe` `060900030501` | `c60100064279` `060900030500` |
| **Blood pressure** (0x0504) | `c6010006785c` `060900040501` | `c6010006281b` `060900040500` |
| **Blood oxygen** (0x0509) | `c6010006017d` `060900090501` | `c60100063007` `060900090500` |
| **HRV** (0x050A) | `c60100061850` `0609000a0501` | `c60100061f69` `0609000a0500` |
| **Stress** (0x050D) | `c60100066e33` `0609000d0501` | `c60100061aba` `0609000d0500` |
| **Blood sugar** (0x0510) | `c6010006016d` `060900100501` | `c60100063017` `060900100500` |

All reply with: `c61100034092` `060900` (CRC varies)

### Monitoring Interval Settings (CMD=0x02)

| Health Type | Key | Get | Set ON | Set OFF |
|------------|-----|-----|--------|---------|
| Heart rate | 0x25 | `021610` | `021600010000173b1e` | `021600000000173b1e` |
| Blood oxygen | 0x25 (ring) | `022510` | `022500010000173b1e` | `022500000000173b1e` |
| HRV | 0x6a | `026a10` | `026a00010000173b1e` | `026a00000000173b1e` |
| Stress | 0x6b | `026b10` | `026b00010000173b1e` | `026b00000000173b1e` |
| Blood sugar | 0x6e | `026e10` | `026e00010000173b1e` | `026e00000000173b1e` |
| Blood pressure | 0x7c | `027c10` | `027c00010000173b1e` | `027c00000000173b1e` |

Note: Start/end times fixed at 00:00-23:59. Interval: 30 or 60 min (HR), 60 min (all others).

### Health Data Sync (CMD=0x05)

All follow the **read-delete loop** pattern:

| Data Type | Key | Read | Delete |
|-----------|-----|------|--------|
| Steps (today) | 0x1a | `051a10` | `051a30` |
| Steps (history) | 0x02 | `050210` | `050230` |
| Sleep | 0x05 | `050510` | `050530` |
| Heart rate | 0x03 | `050310` | `050330` |
| Blood oxygen | 0x09 | `050910` | `050930` |
| HRV | 0x0a | `050a10` | `050a30` |
| Stress | 0x0d | `050d10` | `050d30` |
| Blood sugar | 0x10 | `051010` | `051030` |
| Blood pressure | 0x04 | `050410` | `050430` |

### Data Item Format

**HRItem** (6 bytes each):
```
Time(4, big-endian) | HR(1) | padding(1)
```
Time = epoch + 946684800 (tai_seconds_from_2000)

**BloodOxygenItem** (6 bytes each):
```
Time(4, big-endian) | SpO2(1) | padding(1)
```

**SleepItem** (7 bytes each):
```
Time(4, be) | Status(1) | pad1(1) | pad2(1)
```
Status: 17=start, 34=end, 1=deep, 2=light, 3=awake, 4=REM

**StepItem** (16 bytes each):
```
Time(4, be) | mode(1) | pad(3) | steps(4, le) | calorie(4, le) | distance(4, le)
```
Calorie ÷ 10 = kcal. Distance ÷ 10000 = meters.

### Touch Events (Device→App, CMD=0x04, Key=0x06)

```
040600 | keyType(1) | touchType(1)
```
- keyType: 1 = touch key (default)
- touchType: 1=single, 2=double, 3=triple, 4=long press

### LED Brightness (Ring with screen, CMD=0x02, Key=0x66)

```
026600/026610 | switch(1) | level(1)
```
Level: 1=low, 2=mid, 3=high

### Wear Position (Ring with screen, CMD=0x02, Key=0x68)

```
026800/026810 | pos(1)  # 0=left, 1=right
```

### HID Control (Ring, CMD=0x02, Key=0x64)

```
026400 | appType(1) | switch(1)
```
appType: 0=off, 1=short video, 2=e-book, 3=music

### Power Off / Factory Reset (CMD=0x02, Key=0x22)

```
022200 | type(1)  # 1=shutdown, 2=factory reset
```

## OTA Firmware Upgrade

Separate service: FF00/FF01. Little-endian throughout.

### OTA Commands (PXI_CMD_FW)

| Command | Value | Description |
|---------|-------|-------------|
| CMD_FW_INIT | 0x10 | Initialize |
| CMD_FW_SET_ADDRESS | 0x11 | Set flash address |
| CMD_FW_ERASE | 0x16 | Erase sector |
| CMD_FW_WRITE | 0x17 | Write data ack |
| CMD_FW_UPGRADE | 0x18 | Upgrade firmware |
| CMD_FW_MCU_RESET | 0x22 | Reset MCU |
| CMD_FW_OBJECT_CREATE | 0x25 | Create block obj |
| CMD_FW_EXECUTE | 0x26 | Execute |
| CMD_FW_OTA_INIT_NEW | 0x27 | OTA init |
| EVT_COMMAND_COMPLETE | 0x0E | Event complete |

### OTA Flow
1. Send `0x27` + FW length → Read back init params (max_object_size, mtu_size, prn_threshold)
2. Send `0x25` to create object → Ack
3. Send firmware data in MTU-sized chunks. Every `prn_threshold` chunks, read back CRC `0x17`
4. All objects done → Send `0x18` + total length + CRC → Ack
5. Send `0x22` → MCU resets

## Protocol Constants from AAR

```
CMD_START_JL  = 0xAB  (-85 signed)
CMD_START     = 0x7E  (126)
AGREEMENT_VER = 1
RESULT_SUCCESS = 0

Data types (CmdConstants):
  JL_SET_CMD
  JL_BIND_CMD
  JL_DATA_TRANSFER_CMD
  JL_PUSH_CMD
  JL_CONTROL_CMD
  JL_FILE_CMD

Real-time health data keys:
  JL_BLE_KEY_APP_REAL_TIME_ACTIVITY_DATA
  JL_BLE_KEY_APP_REAL_TIME_BLOOD_OXYGEN_DATA
  JL_BLE_KEY_APP_REAL_TIME_STRESS_DATA
  JL_BLE_KEY_APP_REAL_TIME_HRV_DATA
  JL_BLE_KEY_APP_REAL_TIME_BLOODSUGAR_DATA
```

## Notes

- The AAR contains both "JL" (Jieli chipset) and "PXI" (alternate chipset) protocol variants
- The mini-program doc UUIDs (`0BC0/0BC1/0BC2`) differ from AAR constants (`0xFEE7/0xB002/0xB003`). The mini-program UUIDs are for products SY01 (≥2.1.5) and SY02 (≥2.2.7)
- Data payload CRC is computed over the Data section ONLY (not the header/flags/length)
