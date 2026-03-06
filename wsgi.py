import sys
sys.path.insert(0, '/home/mqy101866/kimi-feishu-bot')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from app import app as application
