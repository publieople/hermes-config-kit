#!/usr/bin/env python3
"""Send a text message to a Feishu/Lark group chat via open API.

Usage: python3 lark_send.py <chat_id> <message>
Env: reads FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_DOMAIN from ~/.hermes/.env
"""
import json
import os
import sys
import urllib.request


def load_env(path=os.path.expanduser("~/.hermes/.env")):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip().strip('"').strip("'")
    return env


def post(url, data, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, json.dumps(data).encode(), headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


def send(chat_id, message):
    env = load_env()
    domain = (
        "https://open.larksuite.com"
        if env.get("FEISHU_DOMAIN") == "lark"
        else "https://open.feishu.cn"
    )
    tok = post(
        domain + "/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": env["FEISHU_APP_ID"], "app_secret": env["FEISHU_APP_SECRET"]},
    )
    if tok.get("code") != 0:
        raise RuntimeError(f"token failed: {tok}")
    body = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": message}),
    }
    r = post(
        domain + "/open-apis/im/v1/messages?receive_id_type=chat_id",
        body,
        {"Authorization": "Bearer " + tok["tenant_access_token"]},
    )
    return r


if __name__ == "__main__":
    chat_id, message = sys.argv[1], sys.argv[2]
    r = send(chat_id, message)
    print(r.get("code"), r.get("msg"))
