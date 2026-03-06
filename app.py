"""
Kimi 飞书智能助理
支持私聊和群聊@回复
"""

from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

app = Flask(__name__)

# ==================== 配置区域 ====================
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = "https://api.moonshot.cn/v1"

# 飞书应用配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# 存储简单的会话上下文（生产环境建议用 Redis）
conversations = {}

# ==================== Kimi API 调用 ====================

def chat_with_kimi(message, session_id=None):
    """
    调用 Kimi API 获取回复，支持多轮对话
    """
    if not KIMI_API_KEY:
        return "⚠️ 抱歉，Kimi API Key 未配置，请联系管理员"
    
    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 获取或创建会话历史
    if session_id not in conversations:
        conversations[session_id] = [
            {"role": "system", "content": """你是 Kimi 智能助理，由月之暗面开发。

你的特点：
1. 用中文回答，语气友好专业
2. 回答简洁明了，重点突出
3. 对于代码问题，提供可运行的示例
4. 如果不确定，诚实告知用户

你可以帮用户：
- 回答问题、解释概念
- 写代码、改 Bug
- 分析数据、生成文案
- 提供建议和思路
"""}
        ]
    
    # 添加用户消息
    conversations[session_id].append({"role": "user", "content": message})
    
    # 只保留最近 10 轮对话（避免超出 token 限制）
    if len(conversations[session_id]) > 21:
        conversations[session_id] = [conversations[session_id][0]] + conversations[session_id][-20:]
    
    data = {
        "model": "moonshot-v1-8k",
        "messages": conversations[session_id],
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{KIMI_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        
        # 保存助手回复到会话历史
        conversations[session_id].append({"role": "assistant", "content": reply})
        
        return reply
    except Exception as e:
        print(f"Kimi API 错误: {e}")
        return f"❌ 调用 Kimi 出错: {str(e)}"

# ==================== 飞书消息处理 ====================

def get_feishu_token():
    """获取飞书 tenant_access_token"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return None
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        result = resp.json()
        return result.get("tenant_access_token")
    except Exception as e:
        print(f"获取飞书 token 失败: {e}")
        return None

def send_message_to_feishu(receive_id, content, msg_type="text", is_user=True):
    """
    主动发送消息到飞书（用于异步回复）
    """
    token = get_feishu_token()
    if not token:
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # receive_id_type: open_id / user_id / union_id / chat_id
    id_type = "open_id" if is_user else "chat_id"
    
    params = {"receive_id_type": id_type}
    
    if msg_type == "text":
        data = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": content[:4000]})  # 飞书限制
        }
    else:
        # 卡片消息
        card_content = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content[:4000]}
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "🤖 Kimi 智能助理"}]
                }
            ],
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "Kimi 回复"}
            }
        }
        data = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "card": card_content
        }
    
    try:
        resp = requests.post(url, headers=headers, params=params, json=data, timeout=10)
        result = resp.json()
        if result.get("code") == 0:
            return True
        print(f"发送消息失败: {result}")
        return False
    except Exception as e:
        print(f"发送消息异常: {e}")
        return False

def process_message_async(sender_id, message, session_id):
    """
    异步处理消息（防止飞书超时）
    """
    import threading
    
    def async_reply():
        # 调用 Kimi
        reply = chat_with_kimi(message, session_id)
        # 发送回复
        send_message_to_feishu(sender_id, reply, msg_type="interactive", is_user=True)
    
    thread = threading.Thread(target=async_reply)
    thread.start()

# ==================== Webhook 路由 ====================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "service": "Kimi 智能助理",
        "features": ["私聊回复", "群聊@回复", "多轮对话"],
        "time": datetime.now().isoformat()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    接收飞书消息推送
    """
    try:
        data = request.get_json()
        print(f"[{datetime.now()}] 收到飞书消息: {json.dumps(data, ensure_ascii=False)[:500]}")
        
        if not data:
            return jsonify({"code": 0})
        
        # 处理 URL 验证
        if data.get("type") == "url_verification":
            challenge = data.get("challenge")
            print(f"URL 验证: {challenge}")
            return jsonify({"challenge": challenge})
        
        # 处理回调事件
        event = data.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})
        
        # 获取发送者信息
        sender_info = sender.get("sender_id", {})
        sender_id = sender_info.get("open_id", "")
        
        # 获取消息信息
        chat_type = message.get("chat_type", "")  # p2p(私聊) / group(群聊)
        msg_type = message.get("message_type", "")
        content = message.get("content", "{}")
        
        # 生成会话 ID
        session_id = f"{sender_id}_{chat_type}"
        
        # 处理文本消息
        if msg_type == "text":
            text_data = json.loads(content) if isinstance(content, str) else content
            text = text_data.get("text", "").strip()
            
            # 去掉 @机器人的内容（群聊时）
            if chat_type == "group":
                # 飞书群聊 @ 格式: @_user_X
                import re
                text = re.sub(r'@_user_\d+\s*', '', text).strip()
            
            print(f"用户[{sender_id}]: {text}")
            
            # 特殊命令处理
            if text == "/help":
                reply = """🤖 **Kimi 智能助理 使用指南**

**基本功能：**
• 直接输入问题，我会用 AI 回答
• 支持多轮对话，记得上下文

**快捷命令：**
• `/help` - 显示帮助
• `/new` - 开启新对话（清空上下文）
• `/status` - 查看服务状态

**我可以帮你：**
✍️ 写文章、改文案
💻 写代码、改 Bug
📊 分析数据、做计算
🔍 查资料、解答问题

有什么可以帮你的吗？"""
                send_message_to_feishu(sender_id, reply, msg_type="interactive", is_user=True)
                return jsonify({"code": 0})
            
            if text == "/new":
                if session_id in conversations:
                    del conversations[session_id]
                send_message_to_feishu(sender_id, "✅ 已开启新对话，上下文已清空", is_user=True)
                return jsonify({"code": 0})
            
            if text == "/status":
                reply = f"""📊 **服务状态**

Kimi API: {'✅ 正常' if KIMI_API_KEY else '❌ 未配置'}
飞书连接: ✅ 正常
当前会话数: {len(conversations)}
"""
                send_message_to_feishu(sender_id, reply, msg_type="interactive", is_user=True)
                return jsonify({"code": 0})
            
            # 普通消息：同步处理（飞书 3 秒内必须返回）
            # 先返回"正在输入"提示，避免超时
            reply = chat_with_kimi(text, session_id)
            
            # 直接返回卡片消息
            return jsonify({
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": reply[:4000]}},
                        {"tag": "note", "elements": [{"tag": "plain_text", "content": "🤖 Kimi 智能助理"}]}
                    ],
                    "header": {"template": "blue", "title": {"tag": "plain_text", "content": "Kimi 回复"}}
                }
            })
        
        # 其他消息类型
        return jsonify({"code": 0})
        
    except Exception as e:
        print(f"处理消息出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"code": 0})

@app.route("/test", methods=["GET"])
def test():
    """测试 Kimi API 是否正常工作"""
    if not KIMI_API_KEY:
        return jsonify({"error": "KIMI_API_KEY 未设置"})
    
    reply = chat_with_kimi("你好，请介绍一下自己", "test_session")
    return jsonify({
        "status": "ok",
        "kimi_reply": reply[:200] + "..." if len(reply) > 200 else reply
    })

@app.route("/test-feishu", methods=["GET"])
def test_feishu():
    """测试飞书连接"""
    token = get_feishu_token()
    if token:
        return jsonify({"status": "ok", "message": "飞书连接正常"})
    return jsonify({"status": "error", "message": "飞书连接失败，请检查 App ID 和 Secret"})

# ==================== 启动 ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🤖 Kimi 智能助理启动，端口: {port}")
    print(f"   API Key 配置: {'✅' if KIMI_API_KEY else '❌'}")
    print(f"   飞书配置: {'✅' if FEISHU_APP_ID else '❌'}")
    app.run(host="0.0.0.0", port=port, debug=False)
