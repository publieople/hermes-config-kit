"""
{{PROJECT_NAME}} 情绪算法 — Windows 最小可用版
接收 user_id + {{INPUT_FEATURE}} → 返回 {{OUTPUT_LABELS}}
"""

import os
import json
import math
import pickle
from datetime import datetime

import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = None
scaler = None
{{DATA_STORES}}  # e.g., user_baselines = {}

# 默认用户画像 — 替换为实际数据
DEFAULT_PROFILE = {{DEFAULT_PROFILE}}  # e.g., {'gender': 1, 'age': 22, 'weight_kg': 65}

# 默认基线 — 无匹配用户时使用
DEFAULT_BASELINE = {{DEFAULT_BASELINE}}  # e.g., {'mean': 70, 'std': 10, 'median': 70}

EMOTION_LABELS = {{OUTPUT_LABELS}}  # e.g., ['calm', 'anxious', 'excited']


def load_resources():
    global model, scaler
    model_path = os.path.join(BASE_DIR, 'models', '{{MODEL_FILE}}')  # e.g., emotion_model.pkl
    scaler_path = os.path.join(BASE_DIR, 'models', '{{SCALER_FILE}}')  # e.g., scaler.pkl

    for path, name in [(model_path, '{{MODEL_FILE}}'), (scaler_path, '{{SCALER_FILE}}')]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"模型文件缺失: {name}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)

    {{LOAD_BASELINES}}  # e.g., load user_baselines from JSON

    print(f"[OK] 模型已加载 | RandomForest x {{N_FEATURES}}维特征")


def extract_features(user_id, {{INPUT_FEATURES}}):
    """构建 {{N_FEATURES}} 维特征向量"""
    user_id = str(user_id)

    profile = DEFAULT_PROFILE
    # 从 user_profiles 或数据库覆盖 profile

    # 时间/上下文特征
    dt = datetime.now()
    {{COMPUTE_FEATURES}}

    feature_vector = [
        {{FEATURE_LIST}}
    ]

    return feature_vector, {'user_id': user_id}


def predict_emotion(feature_vector):
    """推理 → label, label_name, probabilities, score"""
    X = scaler.transform(np.array([feature_vector]))
    probs = model.predict_proba(X)[0]
    label = int(model.predict(X)[0])
    label_name = EMOTION_LABELS[label]

    score = round(float(probs[label]), 4)

    return label, label_name, probs.tolist(), score


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'model_type': '{{MODEL_TYPE}}',
        'feature_count': {{N_FEATURES}},
        'target_classes': EMOTION_LABELS,
    })


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '缺少请求体'}), 400

    user_id = str(data.get('user_id', '')).strip()
    {{PARSE_INPUTS}}

    if not user_id:
        return jsonify({'success': False, 'error': '缺少 user_id'}), 400
    if {{REQUIRED_CHECKS}}:
        return jsonify({'success': False, 'error': '缺少 {{REQUIRED_FIELD}}'}), 400

    feature_vector, user_info = extract_features(user_id, {{INPUT_ARGS}})
    label, label_name, probabilities, score = predict_emotion(feature_vector)

    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            '{{OUTPUT_LABEL_KEY}}': label_name,
            '{{OUTPUT_SCORE_KEY}}': score,
            'probabilities': dict(zip(EMOTION_LABELS, [round(p, 4) for p in probabilities])),
            'analyzed_at': datetime.now().isoformat(),
        }
    })


if __name__ == '__main__':
    print("{{PROJECT_NAME}} API — Windows 最小版")
    load_resources()
    print(f"服务地址: http://localhost:{{PORT}}")
    app.run(host='0.0.0.0', port={{PORT}}, debug=False)
