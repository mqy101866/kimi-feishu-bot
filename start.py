"""
Kimi 飞书助理 - 本地启动脚本（带 Ngrok 穿透）
"""

import os
import sys
import time
import signal
from pyngrok import ngrok
from app import app

# 配置
PORT = int(os.environ.get("PORT", 5000))

def start_ngrok():
    """启动 Ngrok 隧道"""
    # 检查是否有 Ngrok Token
    ngrok_token = os.environ.get("NGROK_AUTHTOKEN", "")
    
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
        print("✅ 已配置 Ngrok Token")
    else:
        print("⚠️ 未配置 Ngrok Token，使用免费版（有限制）")
        print("   如需稳定连接，请访问 https://dashboard.ngrok.com/get-started/your-authtoken 获取 Token")
    
    # 启动隧道
    try:
        public_url = ngrok.connect(PORT, "http")
        print(f"\n🌐 公网地址: {public_url}")
        print(f"📎 Webhook 地址: {public_url}/webhook")
        print(f"🔗 测试地址: {public_url}/test")
        print(f"\n⏰ 此地址有效期约 8 小时\n")
        return public_url
    except Exception as e:
        print(f"❌ Ngrok 启动失败: {e}")
        return None

def signal_handler(sig, frame):
    """优雅退出"""
    print("\n\n🛑 正在关闭服务...")
    ngrok.kill()
    sys.exit(0)

if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 50)
    print("🤖 Kimi 飞书智能助理 - 本地启动")
    print("=" * 50)
    
    # 检查配置
    print("\n📋 配置检查:")
    kimi_key = os.environ.get("KIMI_API_KEY", "")
    feishu_id = os.environ.get("FEISHU_APP_ID", "")
    feishu_secret = os.environ.get("FEISHU_APP_SECRET", "")
    
    print(f"   KIMI_API_KEY: {'✅ 已配置' if kimi_key else '❌ 未配置'}")
    print(f"   FEISHU_APP_ID: {'✅ 已配置' if feishu_id else '❌ 未配置'}")
    print(f"   FEISHU_APP_SECRET: {'✅ 已配置' if feishu_secret else '❌ 未配置'}")
    
    if not kimi_key:
        print("\n⚠️ 警告: KIMI_API_KEY 未配置，机器人将无法回复")
    
    # 启动 Ngrok
    print("\n🚀 启动 Ngrok 穿透...")
    url = start_ngrok()
    
    if url:
        print("🟢 服务已启动，按 Ctrl+C 停止\n")
        # 启动 Flask
        app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
    else:
        print("❌ 启动失败")
        sys.exit(1)
