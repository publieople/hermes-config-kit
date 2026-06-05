---
title: BLE Protocol Extraction
name: ble-protocol-extraction
description: Extract BLE communication protocol specifications from Android SDK artifacts (AAR/APK) and documentation files — class file analysis, UUID discovery, command constant recovery, and PDF protocol doc text extraction.
category: iot
triggers:
  - reverse-engineer BLE protocol
  - extract protocol from AAR
  - decompile Android BLE SDK
  - recover BLE UUIDs from class files
  - extract BLE command format
  - parse Java class file for BLE constants
  - read BLE protocol PDF document
  - RW ring protocol analysis
  - smart watch/ring BLE reverse engineering
---

# BLE Protocol Extraction

Systematic approach for extracting BLE communication protocols from Android SDK artifacts and documentation. Covers AAR/JAR analysis, Java class file constant pool extraction, and PDF protocol document parsing.

## Phase 1: AAR Decompilation

Android Archive (AAR) files are ZIP archives containing compiled Java/Kotlin code.

### 1.1 Extract AAR

```python
import zipfile, os

with zipfile.ZipFile('blesdk-release-xxxx.aar') as aar:
    aar.extractall('sdk-reverse/')
    for f in aar.namelist():
        print(f'{aar.getinfo(f).file_size:>8}  {f}')
```

Key files inside an AAR:
- `classes.jar` — compiled Java bytecode (THE target)
- `R.txt` — Android resource IDs
- `AndroidManifest.xml` — permissions and service declarations
- `proguard.txt` — obfuscation rules (indicates what's kept/removed)

### 1.2 Extract JAR Contents

```python
with zipfile.ZipFile('classes.jar') as jar:
    for f in sorted(jar.namelist()):
        if f.endswith('.class'):
            print(f)
```

**Target classes for BLE protocol analysis:**

| Package | Classes | What they contain |
|---------|---------|-------------------|
| `blesdk/utils/` | `CmdConstants`, `BleConstants`, `Constants` | BLE UUIDs, command byte constants, protocol markers |
| `blesdk/data/` | `CmdHelper`, `CmdHandlerUtils`, `BleResultHelper`, `BleDataPackage` | Command → byte[] serialization, result parsing |
| `blesdk/ble/` | `ConnectBleService`, `ScanBleService`, `FileTransferService` | BLE connection/scan/OTA logic |
| `blesdk/` | `DHBleSdk` | Main SDK entry point — method signatures reveal all available commands |
| `blesdk/callback/` | Various `*Callback` | Data types and structures |
| `blesdk/bean/sync/` | `HeartRateSyncBean`, `BloodOxySyncBean`, etc. | Data model structures |

## Phase 2: Java Class File Constant Pool Analysis

No Java/jadx needed — Python can parse `.class` files to extract string constants, integer constants, and BLE UUIDs.

### 2.1 Extract BLE Service UUIDs

BLE UUIDs appear as string constants in the constant pool. Look for:
- `UUID_SERVICE` / `SERVICE_UUID` field names
- UUID patterns: `0000xxxx-0000-1000-8000-00805f9b34fb` (standard BLE base)
- 16-bit shortcuts like `0BC0`, `FEE7`, `FF00`

**Key pattern**: Standard BLE base UUID `0000xxxx-0000-1000-8000-00805f9b34fb`. The first 4 hex digits after `0000` are the 16-bit UUID.

### 2.2 Extract Protocol Markers

Look for field names and string values containing:
- `CMD_`, `KEY_`, `_DATA_TRANSFER_`, `_CONTROL_CMD`
- `START`, `AGREEMENT_VERSION`, `PROTOCOL`
- `SET_`, `GET_`, `SYNC_`

These reveal:
- Command header bytes (e.g., `CMD_START = 0x7E` or `CMD_START_JL = 0xAB`)
- Protocol version numbers
- Command type identifiers (`JL_SET_CMD`, `JL_BIND_CMD`, etc.)

### 2.3 Extract Integer Constants

Integer constants with values in `0x00-0xFF` range are often byte-level protocol markers. Negative values under `-1` are Java's signed byte representation (e.g., `-85` = `0xAB`).

### 2.4 Field References Map

Field references like `Fieldref: CmdConstants -> JL_HR_DATA_TRANSFER_KEY` reveal how command constants are wired to values.

### 2.5 Complete Python Parser

See `references/class-file-parser.py` for a full implementation that extracts:
- All string constants (filtered for BLE-relevant patterns)
- Integer constants
- Field/method references
- UUID patterns

## Phase 3: PDF Protocol Document Extraction

When a PDF protocol document is available (often more complete than decompiled code):

### 3.1 Cross-Platform Extraction

**WSL → Windows bridge** (useful when WSL lacks PDF tools):

```bash
# Copy PDF to Windows Downloads
cp protocol.pdf /mnt/c/Users/po/Downloads/

# Use PowerShell to extract text via Windows pdftotext
```

```powershell
pdftotext.exe "C:\path\to\document.pdf" "C:\path\to\output.txt" -raw
```

**Native WSL approach**:
```bash
pip3 install pdfminer.six
python3 -c "
from pdfminer.high_level import extract_text
text = extract_text('protocol.pdf')
print(text)
"
```

### 3.2 What to Extract from Protocol Docs

| Section | Key information |
|---------|-----------------|
| **BLE service/characteristic UUIDs** | Actual UUIDs to use (may differ from AAR constants) |
| **Packet header format** | Header byte, flags, length field, CRC algorithm |
| **Data payload format** | CMD+Key+KeyFlag structure, value encoding |
| **Command table** | Complete list of CMD/Key pairs for all operations |
| **Health data item formats** | Per-data-type byte layouts (endianness, field sizes) |
| **OTA protocol** | Firmware upgrade flow, block transfer, CRC |
| **Example hex dumps** | Actual working commands with CRC values — use to validate your CRC implementation |

## Phase 4.5: Chipset Identification

Many Chinese wearables use standard BLE chipsets with known default services. The SDK's constant names often reveal the chipset:

| Chipset | Service UUID | Characteristics | Common In | Telltale constants |
|---------|-------------|-----------------|-----------|-------------------|
| **Jieli (JL) / BR23** | `FEE7` | Write=B002, Notify=B003 | Rings, watches | `JL_SET_CMD`, `CMD_START_JL=0xAB` |
| **Actions (ATS)** | `FEE0` | Variable | Watches | `ATS_*` prefixes |
| **Nordic (nRF52)** | Custom | Custom | Premium devices | No JL/ATS prefix |
| **Dialog DA145xx** | Custom | Custom | Older devices | |

**Key pattern**: Constant names with a prefix like `JL_`, `PXI_`, `ATS_` directly identify the chipset vendor. The `JL_` prefix (Jieli) is overwhelmingly the most common in Chinese BLE wearables.

### Common BLE Wearable UUID Patterns

| UUID | Typical Use |
|------|-------------|
| `0000FEE7-...` | Xiaomi/Huami/Chinese wearable (very common, Jieli) |
| `0000FEE0-...` | Another common wearable service |
| `0000180A-...` | Device Information Service (standard) |
| `0000180F-...` | Battery Service (standard) |
| `0000180D-...` | Heart Rate Service (standard) |
| `00002902-...` | Client Characteristic Configuration Desc (CCC, standard) |

### Connection Sequence (from SDK bytecode)

1. **Scan** → Find device with FEE7 (or target service UUID)
2. **Connect** → Standard BLE GATT connect
3. **Discover Services** → Find service + write/notify characteristics
4. **Enable Notifications** → Write `0x01:00` to CCC descriptor of notify characteristic
5. **Login/Bind Device** → Send bind command with userId and bindType (most rings require this before accepting any other command)
6. **Set Time** → Send time/zone configuration
7. **Begin Health Monitoring** → Send control commands to start HR/BO/HRV streaming
8. **Receive Data** → Data arrives via notify callback

## Phase 4.6: Full Decompilation (Optional — for precise packet structure)

For full protocol reconstruction, use jadx to get readable Java source:

```bash
# Install jadx
wget -O jadx.zip "https://github.com/skylot/jadx/releases/latest/download/jadx-1.5.0.zip"
unzip jadx.zip -d jadx
export PATH="$PWD/jadx/bin:$PATH"

# Decompile JAR
jadx -d decompiled-sdk classes.jar

# Or decompile APK directly
jadx -d decompiled-apk device.apk
```

**Key classes** for BLE protocol understanding (naming varies by vendor):
- `CmdHelper` — converts Java beans → byte arrays for sending
- `BleResultHelper` — parses raw byte arrays → Java beans
- `CmdHandlerUtils` / `CmdHandlerJLUtils` — command queuing and dispatch
- `DHBleSdk` — main SDK entry point (method signatures reveal all available commands)
- `BleConstants` — BLE UUID constants
- `CmdConstants` — command protocol constants

## Phase 5: Verification Checklist

After extraction, verify your understanding against this checklist:

- [ ] BLE Service UUID extracted and verified against known chipset databases
- [ ] Write characteristic UUID identified
- [ ] Notify characteristic UUID identified
- [ ] CCC descriptor UUID confirmed
- [ ] Protocol command headers identified (CMD_START values)
- [ ] Command type constants mapped (SET, BIND, DATA_TRANSFER, CONTROL)
- [ ] Health data keys identified (HR, BO, HRV, stress, etc.)
- [ ] Result/error codes extracted
- [ ] Alternative service UUIDs (for JL/PXI chipsets) documented
- [ ] Connection sequence mapped (especially login/bind step)
- [ ] CRC algorithm validated against example hex dumps

## Phase 4: Protocol Spec Reconstruction

### 4.1 Packet Structure

```
Header(1) | Flag(1) | Length(2) | CRC16(2) | Data(N)
```

- **Header**: Fixed marker (e.g., `0xC6`)
- **Flag**: Direction indicator (e.g., `0x01`=write/send, `0x11`=reply/receive)
- **Length**: Big-endian uint16 of Data section length
- **CRC16**: CRC-16 of Data section (custom table-based algorithm)
- **Data**: Protocol payload

### 4.2 Data Payload Structure

```
CMD(1) | Key(1) | KeyFlag(1) | Value(N)
```

- **CMD**: Function group identifier
- **Key**: Sub-function identifier
- **KeyFlag**: Operation type:
  - `0x00` = set/write
  - `0x10` = get/read/query
  - `0x20` = add
  - `0x30` = delete
- **Value**: Operation-specific payload

### 4.3 Health Data Sync Pattern

Health history data follows a **read-delete loop**:
```
1. Send GET command (CMD=0x05, Key=X, Flag=0x10)
2. Device returns data block (Len > 3 = has data)
3. Send DELETE command (CMD=0x05, Key=X, Flag=0x30)
4. Device confirms delete
5. Repeat step 1
6. Device returns Len = 3 (no more data → done)
```

### 4.4 CRC16 Algorithm

```python
CRC_TABLE = [0x72ae, 0x2cd6, 0x3d6c, ...]  # 256 entries

def calc_crc16(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc = (crc >> 8) ^ CRC_TABLE[(crc ^ byte) & 0xff]
    return crc
```

Validate using example hex dumps from the protocol doc (CRC is the 2 bytes after Length in the packet header).

## Pitfalls

- **Multiple BLE service UUIDs**: The AAR may have different UUIDs than the mini-program protocol doc. The mini-program doc is usually more authoritative for the actual product. Check device firmware version.
- **Signed bytes in Java**: Java `byte` is signed (-128 to 127). Values appearing negative in Integer constants need `& 0xFF` conversion. Python's struct parser for JVM class dumps shows them as signed — `0xAB` appears as `-85`.
- **Missing the binding/login step**: Most BLE wearables require an initial `loginDevice()` call before they respond to any other command. The protocol usually involves sending a bind packet after BLE connection.
- **CCC descriptor required**: To receive notifications, you must write `0x01:00` to the CCC descriptor (`0x2902`) on the notify characteristic. Without this, the device won't send any data.
- **CRC validation**: Always verify your CRC implementation against the example commands in the protocol doc before sending real commands.
- **Timeout between commands**: Some devices need delay between commands (e.g., OTA init needs ~300ms before read).
- **Endianness**: BLE packet header fields (length) are often big-endian. Data payload fields may be big-endian (health sync) or little-endian (sensor raw data). Check each section.
- **Command queue**: Multiple rapid commands may conflict. Implement a command queue with timeout.
- **Command header ambiguity**: Some chipsets use `0xAB` as header (Jieli JL), others use `0x7E`. Some devices support both. Extract the `CMD_START` constants carefully.
- **Kotlin vs Java in SDK**: Kotlin compiles to the same .class format, but generates many extra synthetic classes (e.g., `SyncDataService$hrCallback$2$1.class`). Filter by ignoring classes with `$` in the name when looking for the main logic classes.
- **ProGuard obfuscation**: If the AAR is ProGuarded, class names will be `a.class`, `b.class`, etc. The string constants in the constant pool are NOT obfuscated though — UUID strings, command keys, and API URLs remain readable.
