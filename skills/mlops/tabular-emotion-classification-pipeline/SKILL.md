---
name: tabular-emotion-classification-pipeline
description: Build an end-to-end ML emotion classification pipeline from raw tabular/biosignal data — heuristic label generation, feature engineering, RandomForest training, Flask API, and SQL schema.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tabular, classification, emotion, biosignal, sklearn, random-forest, heuristic-labels, flask-api]
    related_skills: [ml-web-course-project-wsl, ml-course-project-delivery-packaging]
---

# Tabular Emotion Classification Pipeline

## Overview

Build an end-to-end ML classification pipeline from tabular CSV data (e.g., heart rate, blood oxygen) when there are **no ground-truth emotion labels**. Uses domain heuristics to generate labels, then trains a RandomForest classifier, serves via Flask API, and provides database schema.

**Pipeline:**
```
Raw CSV → Feature Engineering → Heuristic Label Generation → Train RandomForest → Flask API → SQL Schema
```

## When to Use

**Trigger conditions — load this skill when ALL are true:**

- User has tabular/CSV data (numeric columns, timestamps, user IDs)
- The task is to classify something that has no explicit labels (emotion, sentiment, state)
- Labels need to be generated heuristically from the data itself (percentiles, time-of-day, etc.)
- The model must be a scikit-learn tabular classifier (RandomForest, LogisticRegression, etc.)
- The output needs a Flask REST API + database schema

**Also trigger when:**
- User says "训练模型判断情绪" (train a model to judge emotion) with heart rate / biosignal data
- User says "没有标签数据" (no labeled data) and needs synthetic labels
- User has per-user time-series data and needs per-user baseline statistics
- User mentions "导师的表设计" (advisor's table design) with ls_xxx  naming convention

## Step-by-Step

### Phase 1: Data Exploration

First, understand the data:

```python
import csv
from collections import Counter

# Check unique users, records per user, heart rate ranges
users = {}
with open('data.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        uid = row['用户ID']
        if uid not in users:
            users[uid] = {'records': 0, 'hrs': []}
        users[uid]['records'] += 1
        users[uid]['hrs'].append(int(row['心率(bpm)']))

for uid, info in sorted(users.items(), key=lambda x: int(x[0])):
    hrs = info['hrs']
    print(f"User {uid}: {info['records']} records, HR {min(hrs)}-{max(hrs)}, avg {sum(hrs)/len(hrs):.1f}")
```

### Phase 2: Feature Engineering

Compute per-user baselines and extract features.

**Per-user baseline statistics** (for `user_baselines.json`):

```python
from collections import defaultdict

user_hrs = defaultdict(list)
for r in rows:
    user_hrs[r['用户ID']].append(int(r['心率(bpm)']))

baselines = {}
for uid, hrs in user_hrs.items():
    n = len(hrs)
    hrs_sorted = sorted(hrs)
    baselines[uid] = {
        'count': n, 'min': hrs_sorted[0], 'max': hrs_sorted[-1],
        'mean': sum(hrs_sorted) / n,
        'median': hrs_sorted[n // 2],
        'p25': hrs_sorted[int(n * 0.25)],
        'p75': hrs_sorted[int(n * 0.75)],
        'std': (sum((h - sum(hrs_sorted)/n)**2 for h in hrs_sorted) / n) ** 0.5,
    }
```

**User demographics** (collected separately from user group/registration):

```python
USER_PROFILES = {
    '4669': {'gender': 0, 'age': 22, 'weight_kg': 55},  # F
    '4686': {'gender': 1, 'age': 23, 'weight_kg': 65},  # M
    # ... collect from ring group
}
```

**11 feature types** to extract per record:

| # | Feature | Description |
|---|---------|-------------|
| 1 | `age` | User age |
| 2 | `gender` | 0=F, 1=M |
| 3 | `weight_kg` | Body weight (kg) |
| 4 | `heart_rate` | Current HR (bpm) |
| 5 | `hr_baseline_deviation` | HR - user baseline mean |
| 6 | `hr_zscore` | Deviation / baseline std |
| 7 | `hr_ratio` | HR / baseline median |
| 8 | `hour_sin` | sin(2π * hour/24) — circular time |
| 9 | `hour_cos` | cos(2π * hour/24) |
| 10 | `is_night` | 1 if 0:00-5:00 or 23:00-24:00 |
| 11 | `hrv_proxy` | Rolling window HR std (3-5 samples) |

**HRV proxy calculation** (sliding window):

```python
hr_values = [r['心率'] for r in records]
hr_window = []
for i, r in enumerate(records):
    hr = r['心率']
    hr_window.append(hr)
    if len(hr_window) > 5:
        hr_window.pop(0)
    window_hrv = 0
    if len(hr_window) >= 3:
        mean_hr = sum(hr_window) / len(hr_window)
        window_hrv = math.sqrt(sum((h - mean_hr)**2 for h in hr_window) / len(hr_window))
```

**Circular time encoding** (avoids 23:00→0:00 discontinuity):

```python
hour_sin = math.sin(2 * math.pi * hour_decimal / 24.0)
hour_cos = math.cos(2 * math.pi * hour_decimal / 24.0)
```

### Phase 3: Heuristic Label Generation

When no ground-truth labels exist, use domain heuristics:

**Strategy: HR percentile + time-of-day + HRV**

```python
if hr <= baseline['p75']:
    label = 0          # calm
    label_name = 'calm'
else:
    # HR > P75 → emotional arousal
    if is_night:
        label = 1      # anxious (night HR spike = negative)
        label_name = 'anxious'
    else:
        # Daytime: use HRV to disambiguate
        if window_hrv > baseline['std'] * 0.5:
            label = 2  # excited (high HR + high HRV = positive)
            label_name = 'excited'
        else:
            label = 1  # anxious (high HR + low HRV = tension)
            label_name = 'anxious'
```

**Labels:** `0 = calm` (normal range), `1 = anxious` (negative arousal), `2 = excited` (positive arousal)

**⚠️ Important:** The model will achieve ~99.8% accuracy on these labels because labels are derived from the features themselves. This is expected and should be explained in documentation: "Labels are currently heuristic-based; when real user-labeled data is collected, the model will learn genuine emotion patterns at lower but realistic accuracy."

### Phase 4: Model Training

Use RandomForest for explainability (feature importance, tree visualization):

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier(
    n_estimators=200, max_depth=12, min_samples_leaf=5,
    class_weight='balanced', random_state=42, n_jobs=-1
)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
print(classification_report(y_test, y_pred, target_names=['calm','anxious','excited']))

# Feature importance analysis
importances = sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1])
for name, imp in importances:
    print(f"{name:25s} {imp:.4f} {'█' * int(imp*50)}")
```

Save model + scaler:
```python
import pickle
with open('models/emotion_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
```

### Phase 5: Flask API

**Emotion Score calculation** (maps prediction probability to 0.000-1.000 scale):

```python
# calm → low score (0.000-0.300)
# anxious/excited → higher score (0.300-1.000)
if label == 0:  # calm
    score = round((1 - probs[0]) * 0.3, 3)
else:  # anxious or excited
    score = round(probs[label] * 0.7 + 0.3, 3)
```

**extra_result JSON format** (stored in `ls_emotion_analysis_result.extra_result`):

```python
extra_result = {
    'feature_vector': {
        'age': 24, 'gender': 1, 'weight_kg': 72, 'heart_rate': 105,
        'hr_baseline_deviation': 35.7, 'hr_zscore': 2.51, 'hr_ratio': 1.52,
        'hour_sin': 0.5, 'hour_cos': -0.87, 'is_night': 1, 'hrv_proxy': 4.26
    },
    'probabilities': {
        'calm': 0.0, 'anxious': 0.89, 'excited': 0.11
    },
    'user_info': {
        'age': 24, 'gender': 1, 'weight_kg': 72,
        'baseline_mean': 69.3, 'baseline_std': 14.2
    }
}
```

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check + model info |
| POST | `/api/v1/predict` | Single prediction |
| POST | `/api/v1/batch_predict` | Batch predictions |
| GET | `/api/v1/baseline/<uid>` | User baseline info |

**Single prediction request:**

```json
{
  "user_id": "4698",
  "heart_rate": 105,
  "timestamp": "2026-05-14 02:30:00",
  "gender": 1,        // optional, read from DB
  "age": 24,          // optional
  "weight_kg": 72     // optional
}
```

**Single prediction response:**

```json
{
  "success": true,
  "data": {
    "raw_data_id": null,
    "user_id": "4698",
    "analyzed_at": "2026-05-14 02:30:00",
    "emotion_label": "anxious",
    "emotion_score": 1.0,
    "extra_result": "{...}"
  }
}
```

**Feature vector construction for API prediction** (single point, no sliding window):

```python
# HRV proxy falls back to baseline std * 0.3 for single-point predictions
feature_vector = [
    float(age), float(gender), float(weight_kg), float(heart_rate),
    round(hr_deviation, 1), round(hr_zscore, 3), round(hr_ratio, 3),
    round(hour_sin, 4), round(hour_cos, 4), float(is_night),
    round(baseline.get('std', 5) * 0.3, 2)  # HRV proxy
]
```

**Run the API:**

```python
# Follow the pattern in api_server.py:
# 1. Load model, scaler, user_baselines on startup
# 2. Define routes
# 3. app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# IMPORTANT: In production, set debug=False and use_reloader=False
# to avoid issues with background process tools
```

### Phase 6: SQL Schema

Match advisor database table design (if provided). Common pattern:

**Table 1: `ls_biometric_raw_data`** — stores raw sensor data + user info

| Field | Type | Purpose |
|-------|------|---------|
| id | BIGINT AUTO_INCREMENT | Primary key |
| user_id | VARCHAR(64) | User identifier |
| device_id, device_type | VARCHAR | Device info |
| collected_at | DATETIME(3) | Millisecond precision |
| heart_rate | SMALLINT | HR value |
| weight_kg, gender, age | nullable | User profile (updated from group survey) |
| exec_status | VARCHAR | '0'=unprocessed, '1'=processed |
| created_at | DATETIME(3) | Insert time |

**Table 2: `ls_emotion_analysis_result`** — stores prediction results

| Field | Type | Purpose |
|-------|------|---------|
| id | BIGINT AUTO_INCREMENT | Primary key |
| raw_data_id | BIGINT | FK to ls_biometric_raw_data |
| user_id | VARCHAR(64) | Denormalized for query perf |
| analyzed_at | DATETIME(3) | Analysis time |
| emotion_label | VARCHAR(32) | calm / anxious / excited |
| emotion_score | DECIMAL(4,3) | 0.000-1.000 |
| extra_result | VARCHAR(1000) | JSON: feature vectors, probabilities |

**Table 3: `ls_user_profile`** — user demographics (collected from ring group via WeChat)

### Project Structure

```
project/
├── data/
│   ├── heart_rate_cleaned.csv     ← Raw input
│   ├── features.csv               ← Feature engineering output
│   └── user_baselines.json        ← Per-user baseline stats
├── models/
│   ├── emotion_model.pkl          ← Trained RandomForest
│   ├── scaler.pkl                 ← StandardScaler
│   ├── model_summary.json         ← PPT-friendly summary
│   └── feature_importance.csv     ← For charting
├── feature_engineering.py         ← Phase 2+3
├── train_model.py                 ← Phase 4
├── api_server.py                  ← Phase 5
├── test_model.py                  ← Verify without API
├── sql_schema.sql                 ← Phase 6
└── requirements.txt               ← sklearn, flask, numpy, pandas, joblib
```

## Common Pitfalls

### 1. Model accuracy is suspiciously high (~99%)

**Expected.** Labels are derived from features (HR > P75 + time → label), so the model learns the labeling rule itself. **Always document this clearly**:
- "The current model uses heuristic labels (HR percentiles + time-of-day + HRV proxy). This creates an upper bound on accuracy (~99%) because labels are deterministically derived from features. When real user-labeled data is collected, the model will learn genuine emotion patterns at lower but realistic accuracy."

### 2. API server won't start in background mode

If `terminal(background=true)` produces no output and the port doesn't respond:
- **Fix**: Use `debug=False, use_reloader=False` in `app.run()`
- **Fix**: Set `PYTHONUNBUFFERED=1` environment variable
- **Fallback**: Use `execute_code` + `subprocess.Popen` to start and check startup health
- **Test directly**: Run `python3 -c "from api_server import app; app.run(port=5000)"` in foreground to catch errors

### 3. Single-point predictions lose HRV context

For API predictions on single data points (no historical window), HRV proxy defaults to `baseline['std'] * 0.3`. This is a limitation of real-time vs batch processing. Document this and handle batch mode (with sliding windows) for higher accuracy.

### 4. User profile data not yet collected

Start with reasonable defaults for gender/age/weight, but add a clear comment in code: `# TODO: Replace with actual data after group survey`

### 5. Two users sharing the same phone number

Check for duplicate phone numbers across user IDs. This may indicate test accounts or merged identities.

### 6. Class imbalance

Biosignal data often has a naturally imbalanced distribution (more calm → anxious/excited). Use `class_weight='balanced'` in RandomForest and report per-class precision/recall, not just accuracy.

## Verification Checklist

- [ ] Feature engineering runs: `python3 feature_engineering.py`
- [ ] Label distribution is reasonable (not all one class)
- [ ] Model training completes: `python3 train_model.py`
- [ ] Test predictions work: `python3 test_model.py`
- [ ] API health endpoint responds: `curl http://127.0.0.1:5000/health`
- [ ] API prediction works: `curl -X POST ... /api/v1/predict`
- [ ] SQL schema matches the advisor's table design
- [ ] Feature importance data exported for PPT charting
- [ ] GitHub repo initialized with .gitignore + README (add collaborators)

## Production Deployment (Database-Integrated API)

After the model is trained, deploy it with database integration so it can receive and process live data.

### Dual Storage Backend Pattern

Design the API to support **MySQL** (production) with **JSON file fallback** (development/demo):

```python
import os, json
from datetime import datetime

# Configure via environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME', 'ringhealth')
STORAGE_MODE = os.environ.get('STORAGE_MODE', 'json')  # 'mysql' or 'json'

HAVE_PYMYSQL = False
if DB_HOST and DB_USER and DB_PASS:
    try:
        import pymysql
        HAVE_PYMYSQL = True
    except ImportError:
        pass

def _get_db_conn():
    """Get DB connection if configured, else None."""
    if not HAVE_PYMYSQL or not all([DB_HOST, DB_USER, DB_PASS, DB_NAME]):
        return None
    try:
        return pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASS, database=DB_NAME,
            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
        )
    except Exception:
        return None
```

### Biometric Data Endpoint (Write + Auto-Analyze)

The core endpoint that frontend calls to submit heart rate data and get an emotion result:

```python
@app.route('/api/v1/biometric', methods=['POST'])
def add_biometric():
    """
    Receive heart rate data → clean → store → analyze → return result.
    
    Request:
    {
        "user_id": "4698",
        "device_id": "RING_001",
        "device_type": "ring",
        "heart_rate": 95,
        "collected_at": "2026-05-15 14:30:00",
        "gender": 1,           # optional
        "age": 24,             # optional
        "weight_kg": 72        # optional
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data'}), 400
    
    # Validate required fields
    required = ['user_id', 'heart_rate', 'device_id', 'device_type']
    errors = [f for f in required if f not in data]
    if errors:
        return jsonify({'success': False, 'error': f'Missing: {errors}'}), 400
    
    # Clean & validate
    hr = int(data['heart_rate'])
    if hr < 30 or hr > 220:
        return jsonify({'success': False, 'error': 'heart_rate out of range [30-220]'}), 400
    
    # Save record (database or JSON)
    record = save_to_db_or_json(data)
    
    # Auto-analyze emotion
    emotion_result = analyze_single_record(record)
    
    return jsonify({'success': True, 'data': emotion_result})
```

### Data Cleaning Module

Separate `data_cleaner.py` for batch processing of raw CSV exports:

```python
"""
数据清洗脚本 — 原始数据 → 清洗 → 待入库JSON
输出:
  output/cleaned_for_import.json  可直接入库
  output/cleaning_report.json     清洗报告
"""

# Key cleaning rules:
# - heart_rate: 30-220 bpm
# - blood_ox: 80-100 (if present)
# - timestamp: validate datetime format
# - user_id -> phone mapping from reference CSV
# - source -> user_id mapping from cleaned reference data

# Can run as:
#   python3 data_cleaner.py              # One-time batch
#   python3 data_cleaner.py --watch      # Watch directory for new files
#   python3 data_cleaner.py --db-import  # Clean + import to DB
```

### Endpoints for Production API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check + model + storage status |
| POST | `/api/v1/predict` | Single prediction (original) |
| POST | `/api/v1/batch_predict` | Batch predictions |
| GET | `/api/v1/baseline/<uid>` | User baseline info |
| **POST** | **`/api/v1/biometric`** | **Submit HR data → auto-analyze** |
| **GET** | **`/api/v1/latest/<uid>`** | **Latest biometric + emotion result** |
| **POST** | **`/api/v1/process-pending`** | **Process unanalyzed records** |
| **GET** | **`/api/v1/stats`** | **System statistics** |

### Linux Deployment Package

Create a deployable package with three components:

**1. `deploy.sh`** — Interactive Linux deployment script (~808 lines):
```
- Detect OS (Ubuntu/Debian/CentOS)
- Install Python if missing
- Create/activate venv
- pip install -r requirements.txt
- Configure MySQL (interactive, write .env)
- Optionally initialize database from sql_schema.sql
- Start systemd service
- Verify health check
```

**2. `DEPLOY.md`** — Full deployment documentation (~1016 lines):
- System architecture diagram
- Prerequisites (Python ≥ 3.8, MySQL ≥ 5.7)
- Step-by-step deployment
- Environment variable reference
- API documentation with request/response examples
- Production recommendations (systemd, nginx, supervisor)
- Troubleshooting FAQ

**3. Systemd service template:**
```ini
[Unit]
Description=RingHealth Emotion API
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ringhealth-emotion
EnvironmentFile=/opt/ringhealth-emotion/.env
ExecStart=/opt/ringhealth-emotion/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 api_server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Production Deployment Checklist

- [ ] Python environment ready: `python3 -m venv venv && source venv/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Model files present: `models/emotion_model.pkl`, `models/scaler.pkl`
- [ ] Database configured: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` in `.env`
- [ ] Tables created: `ls_biometric_raw_data`, `ls_emotion_analysis_result`, `ls_user_profile`
- [ ] API responds: `curl http://localhost:5000/health`
- [ ] Prediction works: `curl -X POST http://localhost:5000/api/v1/predict ...`
- [ ] Biometric endpoint works: `curl -X POST http://localhost:5000/api/v1/biometric ...`
- [ ] Systemd service installed: `systemctl status ringhealth-emotion`
- [ ] Data flow end-to-end verified

## Team Collaboration Pattern

When the pipeline is part of a larger project with a separate frontend team:

```
Hardware (BLE sensor) → Frontend app (UniApp/iOS/Android)
                           ↓  POST heart_rate + user_id
                    Flask API (emotion prediction)
                           ↓  JSON response
                    Frontend displays emotion label
```

### Hardware BLE Integration

When the frontend connects to a BLE wearable (smart ring, watch), the system architecture becomes:

```
Hardware (BLE ring)
    ↓  Bluetooth LE
Frontend app (UniApp / native)
    ↓  HTTP POST /api/v1/biometric
Flask API (emotion analysis)
    ↓  Write + analyze
Database (ls_biometric_raw_data → ls_emotion_analysis_result)
    ↓  Return result
Frontend displays emotion label
```

**For UniApp/WeChat Mini Program BLE integration:**

- Service UUID: `OBC0`, Write characteristic: `0BC1`, Notify characteristic: `0BC2`
- Protocol: Hex packet with header `0xC6`, CRC16 checksum, CMD+Key+KeyFlag+Value structure
- Key commands: Login (`0x03,0x02,0x20`), Time sync (`0x02,0x01`), Single HR test (`0x06,0x09,0x00,0x0503`)
- See the `rw_miniprogram_doc_260424.pdf` protocol document for full command reference

**Common BLE connection pitfalls (from real UniApp implementation):**

1. **Mock device fallback**: When `uni.openBluetoothAdapter()` or `uni.startBluetoothDevicesDiscovery()` fails, many fallback patterns automatically insert mock devices. Users then click on non-real devices and can't connect. **Fix**: Remove mock fallback — let the scan fail with a clear error message instead.

2. **`isLikelyRingDevice` filter too strict**: If the filter checks for `rw|ring|sy` in device names but the actual device name is different (e.g., `SY02` without those patterns), real devices get filtered out. **Fix**: Log all discovered devices in debug mode, or relax the filter to show all BLE devices initially.

3. **UUID format variations**: On Android, BLE UUIDs may come as 128-bit (`00000BC0-0000-1000-8000-00805F9B34FB`). Use `.includes('0BC0')` (case-insensitive substring match) rather than exact match.

**Frontend team needs:**
- API endpoint URL (`POST /api/v1/predict`)
- Request/response format (share the JSON schema)
- BLE protocol doc if they connect directly to hardware
- User baseline endpoint (`GET /api/v1/baseline/<uid>`) for initialization

**Setup GitHub for team:**
```bash
# After cleaning workspace (remove __pycache__, temp scripts):
git init
git add -A
git commit -m "🎉 init: [project name]"
gh repo create <repo-name> --public --push --remote origin --source .
git branch -m main
# Share the URL with team
```

**.gitignore essentials:**
```
__pycache__/
*.py[cod]
venv/
.env
.DS_Store
.vscode/
.idea/
```
