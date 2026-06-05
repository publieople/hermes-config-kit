# RW BLE SDK Protocol Analysis (v1.0.6, 250811)

## Source

- SDK: `blesdk-release-250811.aar` (468 KB)
- Demo APK: `RW_SDK_V2_release_1.0.6.apk` (11.6 MB)
- Demo source: `RW_SDK_DEMO/` (Android Kotlin project)
- Vendor: RW / dhouse88.com (developer@dhouse88.com)
- Hardware target: Smart ring (also smart watches, e-cigarettes)

## BLE GATT Profile

### Primary Service (Jieli/JL chipset)
| UUID | Type | Notes |
|------|------|-------|
| `0000fee7-0000-1000-8000-00805f9b34fb` | **Service** | Standard FEE7 = Jieli wearable service |
| `0000b002-0000-1000-8000-00805f9b34fb` | **Write Characteristic** | App → Ring commands |
| `0000b003-0000-1000-8000-00805f9b34fb` | **Notify Characteristic** | Ring → App data |
| `00002902-0000-1000-8000-00805f9b34fb` | **CCC Descriptor** | Must write `0x01:00` to enable notifications |

### Alternative Services (from BleConstants)
| UUID | Role |
|------|------|
| `0000ae00-0000-1000-8000-00805f9b34fb` | Service (JL specific) |
| `0000ae01-0000-1000-8000-00805f9b34fb` | Characteristic (JL write) |
| `0000ff00-0000-1000-8000-00805f9b34fb` | Service (PXI OTA) |
| `0000ff01-0000-1000-8000-00805f9b34fb` | Characteristic (PXI OTA) |
| `0000a00a-0000-1000-8000-00805f9b34fb` | Service (unknown/vendor) |

## Protocol Format

### Command Headers (from CmdConstants bytecode)
| Constant | Value (signed byte) | Value (unsigned) |
|----------|---------------------|-------------------|
| CMD_START_JL | -85 = `0xAB` | 171 |
| CMD_START | 126 = `0x7E` | 126 |
| AGREEMENT_VERSION | 1 = `0x01` | 1 |

### Command Type Constants
| Constant Name | Notes |
|---------------|-------|
| JL_SET_CMD | Set parameters on device |
| JL_BIND_CMD | Bind/login device |
| JL_DATA_TRANSFER_CMD | Request data transfer |
| JL_PUSH_CMD | Push data to device |
| JL_CONTROL_CMD | Control commands (start/stop measurements) |
| JL_FILE_CMD | File transfer / OTA |

### Health Data Transfer Keys (real-time measurement)
| Constant | dataType value | Description |
|----------|---------------|-------------|
| JL_HR_DATA_TRANSFER_KEY | 1 | Heart Rate |
| JL_BO_DATA_TRANSFER_KEY | 3 | Blood Oxygen (SpO2) |
| JL_PRESSURE_DATA_TRANSFER_KEY | 8 | Stress |
| JL_HRV_DATA_TRANSFER_KEY | 13 | Heart Rate Variability |
| JL_BLOODSUGAR_DATA_TRANSFER_KEY | — | Blood Sugar (needs specific device) |

### Real-time Health Data Keys (JL_BLE_KEY_APP_REAL_TIME_*)
| Key Name | Data type |
|----------|-----------|
| JL_BLE_KEY_APP_REAL_TIME_ACTIVITY_DATA | Activity/step count |
| JL_BLE_KEY_APP_REAL_TIME_BLOOD_OXYGEN_DATA | SpO2 |
| JL_BLE_KEY_APP_REAL_TIME_STRESS_DATA | Stress level |
| JL_BLE_KEY_APP_REAL_TIME_HRV_DATA | HRV |
| JL_BLE_KEY_APP_REAL_TIME_BLOODSUGAR_DATA | Blood sugar |
| JL_BLE_KEY_APP_REAL_TIME_MUSLIMCOUNT_DATA | Muslim prayer count (custom) |

### Feature Setting IDs
| Constant | Purpose |
|----------|---------|
| JL_BRIGHT_SCREEN_KEY | Bright screen toggle |
| JL_BRIGHT_SCREEN_TIME_KEY | Bright screen time config |
| JL_SLEEP_AID_KEY | Sleep aid mode |
| JL_ADD_ALARM_CLOCK_ID | Set alarm |
| JL_SLEEP_SUMMARY_KEY | Sleep summary |
| JL_POWER_OFF_KEY | Power off |
| JL_SET_SLEEP_SUMMARY_ID | Sleep summary settings |

## Connection Sequence (from SDK DEMO and bytecode)

1. **Scan** → Find device with FEE7 service
2. **Connect** → Standard BLE GATT connect
3. **Discover Services** → Find service FEE7 + write/notify chars
4. **Enable Notifications** → Write `0x01:00` to CCC descriptor of B003
5. **Login/Bind Device** → Send JL_BIND_CMD with BindInfoBean (userId, bindType)
6. **Set Time** → Send JL_SET_CMD with timezone (0x20 = 8h * 4) + time
7. **Begin Health Monitoring** → Send JL_CONTROL_CMD to start HR/BO/HRV measurements
8. **Receive Data** → Data arrives via B003 notify callback

## SDK Structure (Package Map)

```
com.example.blesdk/
├── DHBleSdk.class          # Main entry point (singleton facade)
├── data/
│   ├── CmdHelper.class     # Bean→byte[] conversion (73KB, key class)
│   ├── CmdHandlerUtils.class # Command queue & dispatch
│   ├── CmdHandlerJLUtils.class # JL chipset command handler
│   ├── BleDataPackage.class  # BLE data packet wrapper
│   ├── BleResultHelper.class # byte[]→bean parsing (99KB, key class)
│   └── DataPackage.class     # Internal data packet
├── bean/
│   ├── function/            # Command beans (BindInfoBean, PowerBean, etc.)
│   └── sync/               # Sync data beans (HeartRateSyncBean, etc.)
├── ble/
│   ├── ConnectBleService.class  # Connection management
│   ├── ScanBleService.class     # BLE scanning
│   └── FileTransferService.class # OTA/file transfer
├── callback/
│   ├── data/               # Data callbacks (PowerCallback, FirmwareCallback, etc.)
│   └── status/             # Status callbacks (HealthDataControlCallback, etc.)
├── utils/
│   ├── CmdConstants.class  # Command protocol constants (22KB)
│   ├── BleConstants.class  # BLE UUID constants
│   ├── Constants.class     # App-level constants
│   ├── ByteConvertUtil.class # Byte→int conversion
│   └── ParserUtils.class   # Data parsing utilities
```

## Notes for BLE Gateway Implementation

To communicate with the ring without the Android SDK, an ESP32/RPi BLE gateway needs to:

1. **Connect** to the FEE7 service
2. **Find** characteristics B002 (write) and B003 (notify)
3. **Enable** notifications on B003 via CCC descriptor
4. **Login** with a pre-configured userId and bindType (protocol bytes constructed similar to the SDK)
5. **Send** control commands to start health data streaming
6. **Parse** received notification bytes using the byte-offset patterns from BleResultHelper

The exact byte-level command format is in CmdHelper (bean→byte[]) and the response parser is in BleResultHelper (byte[]→bean). Full decompilation with jadx is recommended for the precise packet structure.
