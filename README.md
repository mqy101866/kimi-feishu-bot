# 🤖 Kimi 飞书智能助理

让 Kimi AI 成为你的飞书私人助理，支持私聊和群聊互动。

## ✨ 功能特点

- 💬 **私聊对话**：一对一私聊，像朋友一样聊天
- 👥 **群聊@回复**：在群里 @助理，随时提问
- 🧠 **多轮对话**：支持上下文记忆，聊得更连贯
- ⚡ **异步回复**：响应快速，不怕超时
- 📝 **快捷命令**：`/help`、`/new`、`/status`
- 🎨 **卡片消息**：美观的消息展示

## 🚀 快速部署

### 第一步：准备工作

1. **获取 Kimi API Key**
   - 访问 https://platform.moonshot.cn/
   - 登录 → API Key 管理 → 创建 Key
   - 复制保存（后续使用）

2. **创建飞书测试企业**
   - 访问 https://open.feishu.cn/
   - 扫码登录 → 创建企业 → **创建测试企业**
   - 填写企业名称（如"Kimi助理测试"）

### 第二步：创建飞书应用

1. 进入 https://open.feishu.cn/app
2. 点击「**创建企业自建应用**」
3. 填写信息：
   - 应用名称：`Kimi 智能助理`
   - 应用描述：`我的个人 AI 助理`
4. 点击「添加应用能力」→ 选择「**机器人**」
5. 记录 **App ID** 和 **App Secret**（后面部署用）

### 第三步：配置权限和事件

**开通权限**（左侧权限管理）：
- ✅ `im:chat:readonly`
- ✅ `im:message:send`
- ✅ `im:message.group_at_msg:readonly`
- ✅ `im:chat`（获取群组信息）

**订阅事件**（左侧事件订阅）：
- ✅ `im.message.receive_v1`（接收私聊消息）
- ✅ `im.message.group_at_msg_v1`（接收群聊@消息）

请求地址暂时不填，部署完后再回来配置。

### 第四步：部署到 Render

1. **Fork 或上传代码到 GitHub**
   ```bash
   # 把这4个文件上传到 GitHub 仓库：
   # - app.py
   # - requirements.txt
   # - Procfile
   # - .env.example
   ```

2. **访问 Render 创建服务**
   - 打开 https://render.com/
   - 用 GitHub 登录
   - 点击「New +」→「Web Service」
   - 选择你的代码仓库

3. **配置服务**
   - **Name**: `kimi-assistant`（随意）
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **添加环境变量**（点击 Advanced → Add Environment Variable）
   ```
   KIMI_API_KEY = 你的Kimi API Key
   FEISHU_APP_ID = 你的飞书App ID
   FEISHU_APP_SECRET = 你的飞书App Secret
   ```

5. **点击「Create Web Service」**
   - 等待 2-3 分钟部署完成
   - 记录你的服务地址：`https://kimi-assistant-xxx.onrender.com`

### 第五步：完成飞书配置

1. 回到飞书开放平台 → 事件订阅
2. 填写**请求地址**：
   ```
   https://kimi-assistant-xxx.onrender.com/webhook
   ```
3. 点击「保存」

### 第六步：发布应用

1. 左侧「版本管理与发布」
2. 点击「创建版本」
3. 填写版本号（1.0.0）和更新说明
4. 点击「申请发布」→「确认发布」

### 第七步：开始使用 🎉

1. 打开飞书 App
2. 搜索你的助理名称（如"Kimi 智能助理"）
3. 开始私聊！试试发送：
   - `你好`
   - `/help`
   - `帮我写一段 Python 代码`

**群聊使用**：
- 把机器人拉到群里
- @机器人提问，如 `@Kimi 智能助理 今天天气怎么样`

## 📝 使用指南

### 快捷命令

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助信息 |
| `/new` | 开启新对话（清空上下文） |
| `/status` | 查看服务状态 |

### 功能示例

**💻 编程助手**
```
帮我写一个 Python 函数，计算斐波那契数列
```

**✍️ 文案写作**
```
帮我写一封请假邮件，理由是家里有事
```

**📊 数据分析**
```
解释什么是相关系数，并给出一个例子
```

**🔍 知识问答**
```
量子计算和经典计算有什么区别？
```

## 🧪 测试接口

部署完成后，可以访问以下地址测试：

| 地址 | 功能 |
|------|------|
| `https://你的地址/` | 查看服务状态 |
| `https://你的地址/test` | 测试 Kimi API |
| `https://你的地址/test-feishu` | 测试飞书连接 |

## 🔧 常见问题

### 1. 机器人不回复
- 检查 Render 日志（Dashboard → Logs）
- 确认 `KIMI_API_KEY` 已正确设置
- 确认飞书事件订阅 URL 填写正确（以 `/webhook` 结尾）

### 2. 飞书验证失败
- 确保 URL 格式：`https://xxx.onrender.com/webhook`
- 确保服务已启动（访问首页看是否正常）
- 检查 Render 是否显示 "Your service is live"

### 3. 回复很慢
- 免费版 Render 有冷启动，第一条消息可能慢（30秒左右）
- 后续消息会快很多
- 如需更快响应，可考虑升级到 Render 付费版或使用 Railway

### 4. 上下文丢失
- 默认保存最近 10 轮对话
- 发送 `/new` 可手动清空上下文

## 🎨 自定义配置

修改 `app.py` 中的：
- **模型版本**：`moonshot-v1-8k` 可换成 `moonshot-v1-32k`（长文本）
- **系统提示词**：修改 system message 定义助理性格
- **温度参数**：temperature 控制回复创意程度（0-1）

## 📚 相关链接

- Kimi 开放平台: https://platform.moonshot.cn/
- 飞书开放平台: https://open.feishu.cn/
- Render: https://render.com/

## 💬 支持

有问题可以：
1. 查看 Render 日志排查
2. 查看飞书「事件订阅」页面的推送记录
3. 访问 `/test` 和 `/test-feishu` 测试接口

---

**祝你使用愉快！** 🤖✨
