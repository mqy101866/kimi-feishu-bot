"""
Railway 简化版 - 直接启动 Flask，无需 Gunicorn
"""

import os
from flask import Flask, request, jsonify
import requests
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

@app.route("/")
def index():
    return jsonify({
        "status": "running",
        "service": "Kimi Feishu Bot (Railway)",
        "kimi_configured": bool(KIMI_API_KEY),
        "feishu_configured": bool(FEISHU_APP_ID and FEISHU_APP_SECRET)
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        
        # URL 验证
        if data.get("type") == "url_verification":
            return jsonify({"challenge": data.get("challenge")})
        
        # 处理消息
        event = data.get("event", {})
        message = event.get("message", {})
        
        if message.get("message_type") == "text":
            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "").strip()
            
            # 调用 Kimi
            if KIMI_API_KEY:
                headers = {
                    "Authorization": f"Bearer {KIMI_API_KEY}",
                    "Content-Type": "application/json"
                }
                resp = requests.post(
                    "https://api.moonshot.cn/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": text}]
                    },
                    timeout=30
                )
                reply = resp.json()["choices"][0]["message"]["content"]
            else:
                reply = "Kimi API Key 未配置"
            
            # 返回卡片消息
            return jsonify({
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": reply[:3000]}}
                    ],
                    "header": {"template": "blue", "title": {"tag": "plain_text", "content": "Kimi 回复"}}
                }
            })
        
        return jsonify({"code": 0})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"code": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
